from datetime import datetime, timezone
from decimal import Decimal

from app.extensions import db
from app.models.booking import Booking
from app.models.payment import Payment
from app.services import razorpay_client
from app.services.booking import (
    BookingError,
    booking_summary,
    confirm_locked_booking,
    lock_booking,
)
from app.services.razorpay_client import RazorpayError

CURRENCY = "INR"

# Do not start a payment that cannot finish before the hold expires.
MIN_HOLD_SECONDS = 30


class PaymentError(Exception):
    def __init__(self, message, status_code=400, code="PAYMENT_ERROR"):
        super().__init__(message)
        self.status_code = status_code
        self.code = code


def _require_configured():
    if not razorpay_client.is_configured():
        raise PaymentError(
            "Payments are not configured on the server.",
            503,
            "PAYMENTS_NOT_CONFIGURED",
        )


def _to_paise(amount):
    return int((Decimal(amount) * 100).to_integral_value())


def _as_utc(value):
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def create_payment_order(booking_id, user_id):
    """Create a Razorpay order for a PENDING booking's total.

    Each call is a new payment attempt with its own order, so a failed
    or abandoned checkout can simply be retried while the hold lasts.
    """
    _require_configured()

    if isinstance(booking_id, bool) or not isinstance(booking_id, int):
        raise PaymentError("booking_id must be an integer.")

    booking = db.session.get(Booking, booking_id)

    # Another user's booking is reported as not found.
    if booking is None or booking.user_id != user_id:
        raise PaymentError("Booking not found.", 404)

    now = datetime.now(timezone.utc)
    expires_at = _as_utc(booking.expires_at)

    if booking.status != "PENDING":
        raise PaymentError(
            f"Booking cannot be paid from status {booking.status}.", 409
        )

    seconds_left = (
        int((expires_at - now).total_seconds()) if expires_at else 0
    )

    if seconds_left < MIN_HOLD_SECONDS:
        raise PaymentError(
            "Booking hold has expired. Please create a new booking.", 409
        )

    amount = Decimal(booking.total_amount)

    # No locks are held while calling Razorpay; payment verification
    # re-checks the booking under lock before confirming it.
    try:
        order = razorpay_client.create_order(
            _to_paise(amount),
            CURRENCY,
            receipt=booking.booking_reference,
            notes={"booking_reference": booking.booking_reference},
        )
    except RazorpayError as exc:
        db.session.rollback()
        raise PaymentError(
            f"Could not start the payment: {exc}", 502, "PROVIDER_ERROR"
        ) from exc

    try:
        payment = Payment(
            booking_id=booking.id,
            provider_order_id=order["id"],
            amount=amount,
            currency=CURRENCY,
            status="CREATED",
        )
        db.session.add(payment)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return {
        "payment_id": payment.id,
        "key_id": razorpay_client.key_id(),
        "order_id": order["id"],
        "amount": order["amount"],
        "currency": CURRENCY,
        "booking_reference": booking.booking_reference,
        "expires_at": expires_at.isoformat(),
        "hold_seconds_left": seconds_left,
    }


def _payment_by_order(order_id):
    return db.session.execute(
        db.select(Payment).filter_by(provider_order_id=order_id)
    ).scalar_one_or_none()


def _check_provider_payment(payment, remote):
    # Compare Razorpay's own record with what we asked to be paid.
    if (
        remote.get("order_id") != payment.provider_order_id
        or remote.get("amount") != _to_paise(payment.amount)
        or remote.get("currency") != payment.currency
    ):
        raise PaymentError(
            "Payment details do not match the order.",
            400,
            "PAYMENT_MISMATCH",
        )


def verify_payment(order_id, payment_id, signature, user_id):
    """Verify a Checkout result server-side and confirm the booking.

    The frontend only passes along Razorpay's ids and signature. The
    signature is checked with the key secret, and the payment itself is
    fetched from Razorpay, before anything is confirmed.
    """
    _require_configured()

    if not all(
        isinstance(value, str) and value
        for value in (order_id, payment_id, signature)
    ):
        raise PaymentError(
            "order_id, payment_id and signature are required."
        )

    if not razorpay_client.verify_payment_signature(
        order_id, payment_id, signature
    ):
        raise PaymentError(
            "Payment signature is invalid.", 400, "INVALID_SIGNATURE"
        )

    payment = _payment_by_order(order_id)

    if payment is None or payment.booking.user_id != user_id:
        raise PaymentError("Payment order not found.", 404)

    try:
        remote = razorpay_client.fetch_payment(payment_id)
        _check_provider_payment(payment, remote)

        if remote.get("status") == "authorized":
            # Accounts without automatic capture leave payments
            # authorized; capture so the money is actually collected.
            remote = razorpay_client.capture_payment(
                payment_id, remote["amount"], remote["currency"]
            )

    except RazorpayError as exc:
        db.session.rollback()
        raise PaymentError(
            f"Could not verify the payment: {exc}", 502, "PROVIDER_ERROR"
        ) from exc

    if remote.get("status") != "captured":
        db.session.rollback()
        raise PaymentError(
            f"Payment is not complete (status {remote.get('status')}).",
            409,
        )

    return _finalize_payment(payment.id, payment_id)


def _finalize_payment(payment_row_id, provider_payment_id):
    """Mark a captured payment PAID and confirm its booking.

    Idempotent: the Checkout callback and the webhook can both arrive.
    If the booking can no longer be confirmed (hold expired, cancelled,
    total changed, already paid by another order), the payment is kept
    as REFUND_PENDING instead.
    """
    now = datetime.now(timezone.utc)

    try:
        booking_id = db.session.execute(
            db.select(Payment.booking_id).filter_by(id=payment_row_id)
        ).scalar_one()

        # Lock order: schedule, booking, then the payment row.
        booking = lock_booking(id=booking_id)
        payment = db.session.execute(
            db.select(Payment)
            .filter_by(id=payment_row_id)
            .with_for_update()
        ).scalar_one()

        if payment.status == "PAID":
            result = booking_summary(booking, include_seats=True)
            db.session.commit()
            return result

        if payment.status == "REFUND_PENDING":
            raise PaymentError(_refund_message(payment.failure_reason), 409)

        payment.provider_payment_id = provider_payment_id

        try:
            if Decimal(booking.total_amount) != Decimal(payment.amount):
                raise BookingError(
                    "The booking total changed after payment started.", 409
                )

            result = confirm_locked_booking(booking, now)

        except BookingError as exc:
            # Discard any partial changes, then record the refund.
            db.session.rollback()
            _mark_refund_pending(
                payment_row_id, provider_payment_id, str(exc)
            )
            raise PaymentError(_refund_message(str(exc)), 409) from exc

        payment.status = "PAID"
        payment.failure_reason = None
        db.session.commit()
        return result

    except Exception:
        db.session.rollback()
        raise


def _mark_refund_pending(payment_row_id, provider_payment_id, reason):
    payment = db.session.execute(
        db.select(Payment)
        .filter_by(id=payment_row_id)
        .with_for_update()
    ).scalar_one()

    payment.status = "REFUND_PENDING"
    payment.provider_payment_id = provider_payment_id
    payment.failure_reason = reason[:255]
    db.session.commit()


def _refund_message(reason):
    return (
        "Payment was received, but the booking could not be confirmed"
        f"{': ' + reason if reason else '.'} The amount will be refunded."
    )


def _mark_failed(order_id, provider_payment_id, reason):
    try:
        payment = db.session.execute(
            db.select(Payment)
            .filter_by(provider_order_id=order_id)
            .with_for_update()
        ).scalar_one_or_none()

        # A later attempt on the same order may still succeed, so only
        # an attempt that has not been paid is marked failed.
        if payment is not None and payment.status in {"CREATED", "FAILED"}:
            payment.status = "FAILED"
            payment.provider_payment_id = provider_payment_id
            payment.failure_reason = (reason or "Payment failed.")[:255]

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise


def handle_webhook(raw_body, signature, event):
    """Process a Razorpay webhook. Returns a short status string.

    Only payment.captured and payment.failed are acted on; other events
    are acknowledged and ignored.
    """
    if not razorpay_client.verify_webhook_signature(raw_body, signature):
        raise PaymentError(
            "Webhook signature is invalid.", 400, "INVALID_SIGNATURE"
        )

    event_name = event.get("event")
    entity = (
        event.get("payload", {}).get("payment", {}).get("entity") or {}
    )
    order_id = entity.get("order_id")

    if event_name not in {"payment.captured", "payment.failed"}:
        return "ignored"

    payment = _payment_by_order(order_id) if order_id else None

    if payment is None:
        db.session.rollback()
        return "unknown_order"

    if event_name == "payment.failed":
        _mark_failed(
            order_id, entity.get("id"), entity.get("error_description")
        )
        return "failed_recorded"

    _check_provider_payment(payment, entity)

    try:
        _finalize_payment(payment.id, entity.get("id"))
    except PaymentError:
        # Recorded as REFUND_PENDING; nothing for Razorpay to retry.
        return "refund_pending"

    return "confirmed"

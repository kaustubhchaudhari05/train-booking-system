from datetime import datetime, timezone

from app.extensions import db
from app.models.booking import Booking
from app.models.seat_reservation import SeatReservation


def expire_stale_holds(now=None):
    """Mark PENDING bookings whose hold has passed, and their HELD
    reservations, as EXPIRED.

    Safe to run repeatedly: already-expired rows no longer match.
    CONFIRMED and CANCELLED bookings and reservations are never touched.
    """
    now = now or datetime.now(timezone.utc)

    try:
        # SKIP LOCKED leaves bookings that a confirm or cancel request is
        # currently processing; those requests re-check expiry themselves,
        # and the next cleanup run picks up anything still pending.
        bookings = db.session.execute(
            db.select(Booking)
            .where(
                Booking.status == "PENDING",
                Booking.expires_at.is_not(None),
                Booking.expires_at <= now,
            )
            .with_for_update(skip_locked=True)
        ).scalars().all()

        if not bookings:
            return {"expired_bookings": 0, "expired_reservations": 0}

        booking_ids = [booking.id for booking in bookings]

        reservations = db.session.execute(
            db.select(SeatReservation)
            .where(
                SeatReservation.booking_id.in_(booking_ids),
                SeatReservation.status == "HELD",
            )
            .with_for_update()
        ).scalars().all()

        for booking in bookings:
            booking.status = "EXPIRED"

        for reservation in reservations:
            reservation.status = "EXPIRED"

        db.session.commit()

        return {
            "expired_bookings": len(bookings),
            "expired_reservations": len(reservations),
        }

    except Exception:
        db.session.rollback()
        raise

from datetime import datetime, timezone

from app.extensions import db
from app.models.booking import Booking
from app.models.seat_reservation import SeatReservation
from app.services.waitlist import lock_schedule, promote_waitlist


def expire_stale_holds(now=None):
    """Mark PENDING bookings whose hold has passed, and their HELD
    reservations, as EXPIRED.

    Safe to run repeatedly: already-expired rows no longer match.
    CONFIRMED and CANCELLED bookings and reservations are never touched,
    except that waitlisted passengers are promoted into released seats.
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
            return {
                "expired_bookings": 0,
                "expired_reservations": 0,
                "promoted_passengers": 0,
            }

        booking_ids = [booking.id for booking in bookings]
        affected = {
            (booking.train_schedule_id, booking.coach_class)
            for booking in bookings
        }

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

        expired_bookings = len(bookings)
        expired_reservations = len(reservations)

    except Exception:
        db.session.rollback()
        raise

    # Give the released seats to waitlisted passengers, one schedule and
    # class at a time, each under its own schedule lock.
    promoted = 0

    for train_schedule_id, coach_class in sorted(affected):
        try:
            schedule = lock_schedule(train_schedule_id)
            if schedule is not None:
                promoted += promote_waitlist(schedule, coach_class, now)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    return {
        "expired_bookings": expired_bookings,
        "expired_reservations": expired_reservations,
        "promoted_passengers": promoted,
    }

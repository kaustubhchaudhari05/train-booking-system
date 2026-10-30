
from datetime import datetime, timezone

from app.extensions import db
from app.models.coach import Coach
from app.models.seat import Seat
from app.models.seat_reservation import SeatReservation
from app.models.booking import Booking
from app.models.train_schedule import TrainSchedule


def reserved_seat_ids_query(
    train_schedule_id,
    coach_class,
    source_stop_order,
    destination_stop_order,
    now,
):
    # Seats held by an active reservation whose segment overlaps
    # [source_stop_order, destination_stop_order). Shared by the
    # availability and booking services so the rules stay identical.
    return (
        db.session.query(SeatReservation.seat_id)
        .join(Booking, SeatReservation.booking_id == Booking.id)
        .filter(
            Booking.train_schedule_id == train_schedule_id,
            Booking.coach_class == coach_class,
            Booking.status.in_(["PENDING", "CONFIRMED"]),
            SeatReservation.status.in_(["HELD", "CONFIRMED"]),
            db.or_(
                SeatReservation.status != "HELD",
                SeatReservation.expires_at.is_(None),
                SeatReservation.expires_at > now,
            ),
            SeatReservation.source_stop_order < destination_stop_order,
            SeatReservation.destination_stop_order > source_stop_order,
        )
    )


def get_available_seats(
    train_schedule_id,
    coach_class,
    source_stop_order,
    destination_stop_order,
):
    if source_stop_order >= destination_stop_order:
        raise ValueError("Source stop must come before destination stop.")

    schedule = db.session.get(TrainSchedule, train_schedule_id)

    if not schedule or schedule.status != "SCHEDULED":
        return None

    reserved_seat_ids = reserved_seat_ids_query(
        train_schedule_id,
        coach_class,
        source_stop_order,
        destination_stop_order,
        datetime.now(timezone.utc),
    )

    return (
        db.session.query(Seat)
        .join(Coach, Seat.coach_id == Coach.id)
        .filter(
            Coach.train_id == schedule.train_id,
            Coach.coach_class == coach_class,
            ~Seat.id.in_(reserved_seat_ids),
        )
        .order_by(Coach.coach_number, Seat.id)
        .all()
    )

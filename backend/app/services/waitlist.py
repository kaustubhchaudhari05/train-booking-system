from app.extensions import db
from app.models.booking import Booking
from app.models.booking_passenger import BookingPassenger
from app.models.seat_reservation import SeatReservation
from app.models.train_schedule import TrainSchedule
from app.services.availability import free_seats

# Waitlisted passengers are in the queue only once their booking is
# CONFIRMED or WAITLISTED. Waitlisted passengers of a PENDING booking
# join the queue when that booking is confirmed.
QUEUE_BOOKING_STATUSES = ("CONFIRMED", "WAITLISTED")


def lock_schedule(train_schedule_id):
    """Lock the schedule row.

    Every operation that takes or frees seats on a schedule (booking,
    confirmation, cancellation, promotion) locks the schedule first, so
    these operations are serialized per schedule and always acquire
    locks in the same order.
    """
    return db.session.execute(
        db.select(TrainSchedule)
        .where(TrainSchedule.id == train_schedule_id)
        .with_for_update()
    ).scalar_one_or_none()


def _queue_filters(train_schedule_id, coach_class):
    return (
        Booking.train_schedule_id == train_schedule_id,
        Booking.coach_class == coach_class,
        Booking.status.in_(QUEUE_BOOKING_STATUSES),
        BookingPassenger.status == "WAITLISTED",
    )


def _queue_count(train_schedule_id, coach_class, *extra_filters):
    return db.session.execute(
        db.select(db.func.count(BookingPassenger.id))
        .join(Booking, BookingPassenger.booking_id == Booking.id)
        .where(
            *_queue_filters(train_schedule_id, coach_class),
            *extra_filters,
        )
    ).scalar_one()


def waitlist_count(
    train_schedule_id,
    coach_class,
    source_stop_order,
    destination_stop_order,
):
    """Waitlisted passengers whose journey overlaps the segment."""
    return _queue_count(
        train_schedule_id,
        coach_class,
        Booking.source_stop_order < destination_stop_order,
        Booking.destination_stop_order > source_stop_order,
    )


def waitlist_position(passenger, booking):
    """1-based waitlist position of a queued passenger, or None.

    Counts queued passengers on an overlapping segment who were booked
    before or with this passenger.
    """
    if (
        passenger.status != "WAITLISTED"
        or booking.status not in QUEUE_BOOKING_STATUSES
    ):
        return None

    return _queue_count(
        booking.train_schedule_id,
        booking.coach_class,
        Booking.source_stop_order < booking.destination_stop_order,
        Booking.destination_stop_order > booking.source_stop_order,
        BookingPassenger.id <= passenger.id,
    )


def _pick_seat(seats, berth_preference):
    for seat in seats:
        if seat.berth_type == berth_preference:
            return seat
    return seats[0]


def promote_waitlist(schedule, coach_class, now):
    """Give free seats to waitlisted passengers, oldest first.

    The caller must hold the schedule lock (see lock_schedule). Each
    passenger is promoted as soon as a seat is free for their segment
    (first that fits), and becomes CONFIRMED straight away. Returns the
    number of passengers promoted.
    """
    queue = db.session.execute(
        db.select(BookingPassenger, Booking)
        .join(Booking, BookingPassenger.booking_id == Booking.id)
        .where(*_queue_filters(schedule.id, coach_class))
        .order_by(BookingPassenger.id)
    ).all()

    promoted = 0

    for passenger, booking in queue:
        seats = free_seats(
            schedule,
            coach_class,
            booking.source_stop_order,
            booking.destination_stop_order,
            now,
        )

        if not seats:
            continue

        seat = _pick_seat(seats, passenger.berth_preference)

        booking.status = "CONFIRMED"
        passenger.status = "ACTIVE"

        db.session.add(SeatReservation(
            booking_id=booking.id,
            booking_passenger_id=passenger.id,
            seat_id=seat.id,
            source_stop_order=booking.source_stop_order,
            destination_stop_order=booking.destination_stop_order,
            status="CONFIRMED",
            expires_at=None,
        ))

        # Flush so the next free-seat query sees this reservation.
        db.session.flush()
        promoted += 1

    return promoted

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.extensions import db
from app.models.booking import Booking
from app.models.booking_passenger import BookingPassenger
from app.models.coach import Coach
from app.models.seat import Seat
from app.models.seat_reservation import SeatReservation
from app.models.train_schedule import TrainSchedule
from app.services.availability import reserved_seat_ids_query
from app.services.fare import calculate_fare

BERTH_PREFERENCES = {
    "NO_PREFERENCE",
    "LOWER",
    "MIDDLE",
    "UPPER",
    "SIDE_LOWER",
    "SIDE_UPPER",
}


class BookingError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code


def _validate_passenger(passenger_data):
    name = passenger_data.get("passenger_name")
    age = passenger_data.get("age")
    gender = passenger_data.get("gender")
    berth_preference = passenger_data.get(
        "berth_preference", "NO_PREFERENCE"
    )

    if not isinstance(name, str) or not name.strip():
        raise BookingError("Passenger name is required.")

    if (
        isinstance(age, bool)
        or not isinstance(age, int)
        or not 0 <= age <= 120
    ):
        raise BookingError("Passenger age must be between 0 and 120.")

    if gender not in {"MALE", "FEMALE", "OTHER"}:
        raise BookingError("Invalid passenger gender.")

    if berth_preference not in BERTH_PREFERENCES:
        raise BookingError("Invalid berth preference.")

    return {
        "passenger_name": name.strip(),
        "age": age,
        "gender": gender,
        "berth_preference": berth_preference,
    }


def _assign_seats(passengers, free_seats):
    # First give passengers with a berth preference a matching seat,
    # then fill everyone else from the remaining seats in coach order.
    remaining = list(free_seats)
    assigned = [None] * len(passengers)

    for index, passenger in enumerate(passengers):
        preference = passenger["berth_preference"]
        if preference == "NO_PREFERENCE":
            continue

        for seat in remaining:
            if seat.berth_type == preference:
                assigned[index] = seat
                remaining.remove(seat)
                break

    for index in range(len(passengers)):
        if assigned[index] is None:
            assigned[index] = remaining.pop(0)

    return assigned


def create_booking(
    *,
    train_schedule_id,
    source_station_id,
    destination_station_id,
    source_stop_order,
    destination_stop_order,
    coach_class,
    passengers,
):
    # Basic request validation
    if (
        isinstance(source_stop_order, bool)
        or not isinstance(source_stop_order, int)
        or isinstance(destination_stop_order, bool)
        or not isinstance(destination_stop_order, int)
        or source_stop_order >= destination_stop_order
    ):
        raise BookingError(
            "Source stop must come before destination stop."
        )

    if coach_class not in {"SL", "3A", "2A", "1A"}:
        raise BookingError("Invalid coach class.")

    if not isinstance(passengers, list) or not passengers:
        raise BookingError("At least one passenger is required.")

    if len(passengers) > 6:
        raise BookingError("A maximum of 6 passengers is allowed.")

    if not all(isinstance(p, dict) for p in passengers):
        raise BookingError("Each passenger must be an object.")

    passengers = [_validate_passenger(p) for p in passengers]

    try:
        # Lock and validate the schedule within the transaction.
        schedule = (
            db.session.query(TrainSchedule)
            .filter_by(id=train_schedule_id)
            .with_for_update()
            .first()
        )

        if schedule is None or schedule.status != "SCHEDULED":
            raise BookingError(
                "Train schedule not found or cancelled.", 404
            )

        # Validate that the requested stations and stop orders match
        # this train's actual route.
        from app.models.train_route import TrainRoute

        source_route = TrainRoute.query.filter_by(
            train_id=schedule.train_id,
            station_id=source_station_id,
            stop_order=source_stop_order,
        ).first()

        destination_route = TrainRoute.query.filter_by(
            train_id=schedule.train_id,
            station_id=destination_station_id,
            stop_order=destination_stop_order,
        ).first()

        if source_route is None or destination_route is None:
            raise BookingError(
                "Stations or stop orders do not match this train's route."
            )

        if source_route.distance_km >= destination_route.distance_km:
            raise BookingError("Journey distance must be positive.")

        # Calculate fare per passenger.
        try:
            passenger_fare = calculate_fare(
                train_id=schedule.train_id,
                source_station_id=source_station_id,
                destination_station_id=destination_station_id,
                coach_class=coach_class,
            )
        except ValueError as exc:
            raise BookingError(str(exc)) from exc

        now = datetime.now(timezone.utc)
        hold_expiry = now + timedelta(minutes=10)

        # The schedule row lock above serializes bookings for this
        # schedule, so the free seats found here cannot be taken by a
        # concurrent request before this transaction commits.
        reserved_seat_ids = reserved_seat_ids_query(
            train_schedule_id,
            coach_class,
            source_stop_order,
            destination_stop_order,
            now,
        )

        free_seats = (
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

        if len(free_seats) < len(passengers):
            raise BookingError(
                f"Only {len(free_seats)} seat(s) available in "
                f"{coach_class} for this journey.",
                409,
            )

        assigned_seats = _assign_seats(passengers, free_seats)

        booking = Booking(
            booking_reference=uuid4().hex[:20].upper(),
            train_schedule_id=train_schedule_id,
            source_station_id=source_station_id,
            destination_station_id=destination_station_id,
            source_stop_order=source_stop_order,
            destination_stop_order=destination_stop_order,
            coach_class=coach_class,
            status="PENDING",
            total_amount=passenger_fare * len(passengers),
            expires_at=hold_expiry,
        )

        db.session.add(booking)
        db.session.flush()

        passenger_results = []

        for passenger_data, seat in zip(passengers, assigned_seats):
            passenger = BookingPassenger(
                booking_id=booking.id,
                **passenger_data,
            )

            db.session.add(passenger)
            db.session.flush()

            reservation = SeatReservation(
                booking_id=booking.id,
                booking_passenger_id=passenger.id,
                seat_id=seat.id,
                source_stop_order=source_stop_order,
                destination_stop_order=destination_stop_order,
                status="HELD",
                expires_at=hold_expiry,
            )

            db.session.add(reservation)

            passenger_results.append({
                "passenger_name": passenger.passenger_name,
                "age": passenger.age,
                "gender": passenger.gender,
                "berth_preference": passenger.berth_preference,
                "coach_number": seat.coach.coach_number,
                "seat_number": seat.seat_number,
                "berth_type": seat.berth_type,
            })

        db.session.commit()

        return {
            "booking_id": booking.id,
            "booking_reference": booking.booking_reference,
            "status": booking.status,
            "coach_class": booking.coach_class,
            "passengers": passenger_results,
            "total_amount": str(booking.total_amount),
            "expires_at": (
                booking.expires_at.isoformat()
                if booking.expires_at
                else None
            ),
        }

    except Exception:
        db.session.rollback()
        raise



def confirm_booking(booking_id):
    try:
        # Lock the booking so concurrent confirmation attempts
        # cannot process it at the same time.
        booking = (
            db.session.query(Booking)
            .filter_by(id=booking_id)
            .with_for_update()
            .first()
        )

        if booking is None:
            raise BookingError("Booking not found.", 404)

        if booking.status != "PENDING":
            raise BookingError(
                f"Booking cannot be confirmed from status {booking.status}.",
                409,
            )

        now = datetime.now(timezone.utc)

        # Do not confirm an expired booking.
        if booking.expires_at is not None:
            expiry = booking.expires_at
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)

            if expiry <= now:
                raise BookingError(
                    "Booking hold has expired. Please create a new booking.",
                    409,
                )

        # Lock all reservations for this booking.
        reservations = (
            db.session.query(SeatReservation)
            .filter_by(booking_id=booking.id)
            .with_for_update()
            .all()
        )

        if not reservations or len(reservations) != len(booking.passengers):
            raise BookingError(
                "Booking does not have a reservation for every passenger.",
                409,
            )

        # Validate every reservation before changing any status.
        for reservation in reservations:
            if reservation.status != "HELD":
                raise BookingError(
                    "All seat reservations must be HELD to confirm this booking.",
                    409,
                )

            if reservation.expires_at is not None:
                expiry = reservation.expires_at
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=timezone.utc)

                if expiry <= now:
                    raise BookingError(
                        "A seat reservation has expired. Please create a new booking.",
                        409,
                    )

        # Update the booking and reservations in one transaction.
        booking.status = "CONFIRMED"

        for reservation in reservations:
            reservation.status = "CONFIRMED"
            reservation.expires_at = None

        db.session.commit()

        return {
            "booking_id": booking.id,
            "booking_reference": booking.booking_reference,
            "status": booking.status,
            "confirmed_seats": len(reservations),
            "total_amount": str(booking.total_amount),
        }

    except Exception:
        db.session.rollback()
        raise

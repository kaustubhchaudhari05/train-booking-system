from datetime import date, datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from uuid import uuid4

from app.extensions import db
from app.models.booking import Booking
from app.models.booking_passenger import BookingPassenger
from app.models.coach import Coach
from app.models.seat import Seat
from app.models.seat_reservation import SeatReservation
from app.models.train_route import TrainRoute
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

            # Seat details are only returned once the booking is
            # confirmed (see confirm_booking).
            passenger_results.append({
                "id": passenger.id,
                "passenger_name": passenger.passenger_name,
                "age": passenger.age,
                "gender": passenger.gender,
                "berth_preference": passenger.berth_preference,
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

        # Cancelled passengers are left out; only active passengers
        # and their reservations are confirmed.
        active_passengers = [
            passenger for passenger in booking.passengers
            if passenger.status == "ACTIVE"
        ]

        # Lock the active passengers' reservations.
        reservations = (
            db.session.query(SeatReservation)
            .filter(
                SeatReservation.booking_id == booking.id,
                SeatReservation.booking_passenger_id.in_(
                    [passenger.id for passenger in active_passengers]
                ),
            )
            .with_for_update()
            .all()
        )

        if not reservations or len(reservations) != len(active_passengers):
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

        reservation_by_passenger = {
            reservation.booking_passenger_id: reservation
            for reservation in reservations
        }

        passenger_results = []

        for passenger in active_passengers:
            seat = reservation_by_passenger[passenger.id].seat
            passenger_results.append({
                "id": passenger.id,
                "passenger_name": passenger.passenger_name,
                "age": passenger.age,
                "gender": passenger.gender,
                "berth_preference": passenger.berth_preference,
                "coach_number": seat.coach.coach_number,
                "seat_number": seat.seat_number,
                "berth_type": seat.berth_type,
            })

        return {
            "booking_id": booking.id,
            "booking_reference": booking.booking_reference,
            "status": booking.status,
            "coach_class": booking.coach_class,
            "confirmed_seats": len(reservations),
            "passengers": passenger_results,
            "total_amount": str(booking.total_amount),
        }

    except Exception:
        db.session.rollback()
        raise


def _as_utc(value):
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _effective_status(booking, now):
    # Expired holds are only moved to EXPIRED in the database when the
    # expire-holds command runs, so report them as expired here.
    expires_at = _as_utc(booking.expires_at)
    if (
        booking.status == "PENDING"
        and expires_at is not None
        and expires_at <= now
    ):
        return "EXPIRED"
    return booking.status


def _serialize_booking(booking, now):
    schedule = booking.train_schedule
    train = schedule.train

    routes = {
        route.stop_order: route
        for route in TrainRoute.query.filter(
            TrainRoute.train_id == train.id,
            TrainRoute.stop_order.in_([
                booking.source_stop_order,
                booking.destination_stop_order,
            ]),
        )
    }
    source_route = routes.get(booking.source_stop_order)
    destination_route = routes.get(booking.destination_stop_order)

    status = _effective_status(booking, now)

    # Seat details are only shown for confirmed bookings.
    seats_by_passenger = {}
    if status == "CONFIRMED":
        reservations = SeatReservation.query.filter_by(
            booking_id=booking.id,
            status="CONFIRMED",
        ).all()
        seats_by_passenger = {
            reservation.booking_passenger_id: reservation.seat
            for reservation in reservations
        }

    booking_cancellable = _cancel_blocker(booking, status) is None

    passengers = []
    for passenger in booking.passengers:
        passenger_data = {
            "id": passenger.id,
            "passenger_name": passenger.passenger_name,
            "age": passenger.age,
            "gender": passenger.gender,
            "berth_preference": passenger.berth_preference,
            "status": passenger.status,
            "can_cancel": (
                booking_cancellable and passenger.status == "ACTIVE"
            ),
        }

        seat = seats_by_passenger.get(passenger.id)
        if seat is not None:
            passenger_data.update({
                "coach_number": seat.coach.coach_number,
                "seat_number": seat.seat_number,
                "berth_type": seat.berth_type,
            })

        passengers.append(passenger_data)

    def format_time(value):
        return value.strftime("%H:%M") if value else None

    distance_km = None
    if source_route and destination_route:
        distance_km = str(
            destination_route.distance_km - source_route.distance_km
        )

    expires_at = _as_utc(booking.expires_at)

    return {
        "booking_id": booking.id,
        "booking_reference": booking.booking_reference,
        "status": status,
        "coach_class": booking.coach_class,
        "total_amount": str(booking.total_amount),
        "expires_at": (
            expires_at.isoformat()
            if expires_at and status == "PENDING"
            else None
        ),
        "created_at": _as_utc(booking.created_at).isoformat(),
        "journey_date": schedule.journey_date.isoformat(),
        "train": {
            "train_number": train.train_number,
            "name": train.name,
        },
        "source": {
            "code": booking.source_station.code,
            "name": booking.source_station.name,
            "departure_time": format_time(
                source_route.departure_time if source_route else None
            ),
        },
        "destination": {
            "code": booking.destination_station.code,
            "name": booking.destination_station.name,
            "arrival_time": format_time(
                destination_route.arrival_time if destination_route else None
            ),
        },
        "distance_km": distance_km,
        "can_cancel": booking_cancellable,
        "passengers": passengers,
    }


def _cancel_blocker(booking, status):
    # Returns why a booking cannot be cancelled, or None if it can.
    if status not in {"PENDING", "CONFIRMED"}:
        return f"Booking cannot be cancelled from status {status}."

    if booking.train_schedule.journey_date < date.today():
        return "Bookings cannot be cancelled after the journey date."

    return None


def _normalize_reference(reference):
    return (reference or "").strip().upper()


def get_booking_by_reference(reference):
    booking = Booking.query.filter_by(
        booking_reference=_normalize_reference(reference)
    ).first()

    if booking is None:
        raise BookingError("Booking not found.", 404)

    return _serialize_booking(booking, datetime.now(timezone.utc))


def cancel_booking(reference):
    try:
        # Lock the booking so cancellation cannot race with
        # confirmation or another cancellation.
        booking = (
            db.session.query(Booking)
            .filter_by(booking_reference=_normalize_reference(reference))
            .with_for_update()
            .first()
        )

        if booking is None:
            raise BookingError("Booking not found.", 404)

        now = datetime.now(timezone.utc)
        blocker = _cancel_blocker(booking, _effective_status(booking, now))

        if blocker:
            raise BookingError(blocker, 409)

        reservations = (
            db.session.query(SeatReservation)
            .filter_by(booking_id=booking.id)
            .with_for_update()
            .all()
        )

        _cancel_whole_booking(booking, reservations)

        db.session.commit()

        return _serialize_booking(booking, now)

    except Exception:
        db.session.rollback()
        raise


def _cancel_whole_booking(booking, reservations):
    # Cancelling the reservations releases the seats for the
    # booked segment.
    for reservation in reservations:
        if reservation.status in {"HELD", "CONFIRMED"}:
            reservation.status = "CANCELLED"
            reservation.expires_at = None

    for passenger in booking.passengers:
        passenger.status = "CANCELLED"

    booking.status = "CANCELLED"
    booking.expires_at = None


def cancel_passenger(reference, passenger_name):
    if not isinstance(passenger_name, str) or not passenger_name.strip():
        raise BookingError("Passenger name is required.")

    # Names are stored trimmed, so only surrounding spaces are ignored;
    # the match is otherwise exact and case-sensitive.
    passenger_name = passenger_name.strip()

    try:
        # Same lock order as cancel_booking: booking, then reservations.
        booking = (
            db.session.query(Booking)
            .filter_by(booking_reference=_normalize_reference(reference))
            .with_for_update()
            .first()
        )

        if booking is None:
            raise BookingError("Booking not found.", 404)

        matches = [
            p for p in booking.passengers
            if p.passenger_name == passenger_name
        ]
        active_matches = [p for p in matches if p.status == "ACTIVE"]

        if not matches:
            raise BookingError(
                "No passenger with this exact name was found in the "
                "booking.",
                404,
            )

        if not active_matches:
            raise BookingError(
                "This passenger's ticket is already cancelled.", 409
            )

        if len(active_matches) > 1:
            raise BookingError(
                "More than one passenger in this booking has this name.",
                409,
            )

        passenger = active_matches[0]

        now = datetime.now(timezone.utc)
        blocker = _cancel_blocker(booking, _effective_status(booking, now))

        if blocker:
            raise BookingError(blocker, 409)

        reservations = (
            db.session.query(SeatReservation)
            .filter_by(booking_id=booking.id)
            .with_for_update()
            .all()
        )

        active_count = sum(
            1 for p in booking.passengers if p.status == "ACTIVE"
        )

        if active_count == 1:
            # Cancelling the last active passenger cancels the booking.
            _cancel_whole_booking(booking, reservations)
        else:
            for reservation in reservations:
                if (
                    reservation.booking_passenger_id == passenger.id
                    and reservation.status in {"HELD", "CONFIRMED"}
                ):
                    reservation.status = "CANCELLED"
                    reservation.expires_at = None

            passenger.status = "CANCELLED"

            # Every passenger in a booking pays the same fare, so the
            # total drops by one share.
            passenger_fare = (
                Decimal(booking.total_amount) / active_count
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            booking.total_amount = (
                Decimal(booking.total_amount) - passenger_fare
            )

        db.session.commit()

        return _serialize_booking(booking, now)

    except Exception:
        db.session.rollback()
        raise

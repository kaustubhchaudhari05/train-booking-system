from datetime import date

from flask import Blueprint, jsonify, request
from sqlalchemy.orm import aliased
from sqlalchemy import func

from app.extensions import db
from app.models import Train, TrainRoute, TrainSchedule, Station,Coach, Seat

trains_bp = Blueprint("trains", __name__, url_prefix="/api/trains")


@trains_bp.get("/search")
def search_trains():
    source_code = request.args.get("source", "").strip().upper()
    destination_code = request.args.get("destination", "").strip().upper()
    journey_date_str = request.args.get("date", "").strip()

    if not source_code or not destination_code or not journey_date_str:
        return jsonify({
            "error": "Source, destination, and date are required.",
            "example": "/api/trains/search?source=NGP&destination=BSL&date=2026-10-28",
        }), 400

    if source_code == destination_code:
        return jsonify({
            "error": "Source and destination must be different."
        }), 400

    try:
        journey_date = date.fromisoformat(journey_date_str)
    except ValueError:
        return jsonify({
            "error": "Invalid date. Use YYYY-MM-DD format."
        }), 400

    source_route = aliased(TrainRoute)
    destination_route = aliased(TrainRoute)
    source_station = aliased(Station)
    destination_station = aliased(Station)

    statement = (
        db.select(
            Train,
            TrainSchedule,
            source_station,
            destination_station,
            source_route,
            destination_route,
        )
        .join(
            TrainSchedule,
            TrainSchedule.train_id == Train.id,
        )
        .join(source_route, source_route.train_id == Train.id)
        .join(
            source_station,
            source_station.id == source_route.station_id,
        )
        .join(destination_route, destination_route.train_id == Train.id)
        .join(
            destination_station,
            destination_station.id == destination_route.station_id,
        )
        .where(
            Train.is_active.is_(True),
            TrainSchedule.journey_date == journey_date,
            TrainSchedule.status == "SCHEDULED",
            source_station.code == source_code,
            destination_station.code == destination_code,
            source_station.is_active.is_(True),
            destination_station.is_active.is_(True),
            source_route.stop_order < destination_route.stop_order,
        )
        .order_by(source_route.departure_time)
    )

    results = db.session.execute(statement).all()

    trains = [
        {
            "schedule_id": schedule.id,
            "journey_date": schedule.journey_date.isoformat(),
            "train_number": train.train_number,
            "name": train.name,
            "running_days": train.running_days,
            "source": {
                "code": src_station.code,
                "name": src_station.name,
                "departure_time": (
                    src_route.departure_time.strftime("%H:%M")
                    if src_route.departure_time else None
                ),
            },
            "destination": {
                "code": dest_station.code,
                "name": dest_station.name,
                "arrival_time": (
                    dest_route.arrival_time.strftime("%H:%M")
                    if dest_route.arrival_time else None
                ),
            },
            "distance_km": str(
                dest_route.distance_km - src_route.distance_km
            ),
        }
        for (
            train,
            schedule,
            src_station,
            dest_station,
            src_route,
            dest_route,
        ) in results
    ]

    return jsonify({
        "journey_date": journey_date.isoformat(),
        "count": len(trains),
        "trains": trains,
    }), 200


@trains_bp.get("/<int:train_id>/inventory")
def get_train_inventory(train_id):
    train = db.session.get(Train, train_id)

    if not train or not train.is_active:
        return jsonify({"error": "Train not found"}), 404

    coach_class = request.args.get("class", "").upper()

    allowed_classes = {"SL", "3A", "2A", "1A"}
    if coach_class not in allowed_classes:
        return jsonify({
            "error": "Provide a valid class: SL, 3A, 2A, or 1A"
        }), 400

    coaches = Coach.query.filter_by(
        train_id=train.id,
        coach_class=coach_class,
    ).order_by(Coach.coach_number).all()

    inventory = []
    total_seats = 0

    for coach in coaches:
        seats = Seat.query.filter_by(
            coach_id=coach.id
        ).order_by(Seat.seat_number).all()

        total_seats += len(seats)

        inventory.append({
            "coach_number": coach.coach_number,
            "coach_class": coach.coach_class,
            "seats": [
                {
                    "seat_number": seat.seat_number,
                    "berth_type": seat.berth_type,
                }
                for seat in seats
            ],
        })

    return jsonify({
        "train_number": train.train_number,
        "train_name": train.name,
        "class": coach_class,
        "total_seats": total_seats,
        "coaches": inventory,
        "availability_status": "NOT_TRACKED_YET",
    }), 200

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import TrainSchedule
from app.services.fare import calculate_fare

fares_bp = Blueprint("fares", __name__, url_prefix="/api/fares")


@fares_bp.get("/quote")
def get_fare_quote():
    train_schedule_id = request.args.get("train_schedule_id", type=int)
    source_station_id = request.args.get("source_station_id", type=int)
    destination_station_id = request.args.get(
        "destination_station_id", type=int
    )
    coach_class = request.args.get("coach_class", "").upper()
    passengers = request.args.get("passengers", default=1, type=int)

    if (
        train_schedule_id is None
        or source_station_id is None
        or destination_station_id is None
    ):
        return jsonify({
            "error": "VALIDATION_ERROR",
            "message": "train_schedule_id, source_station_id, and "
                       "destination_station_id are required.",
        }), 400

    if coach_class not in {"SL", "3A", "2A", "1A"}:
        return jsonify({
            "error": "VALIDATION_ERROR",
            "message": "coach_class must be SL, 3A, 2A, or 1A.",
        }), 400

    if passengers is None or not 1 <= passengers <= 6:
        return jsonify({
            "error": "VALIDATION_ERROR",
            "message": "passengers must be between 1 and 6.",
        }), 400

    schedule = db.session.get(TrainSchedule, train_schedule_id)

    if schedule is None or schedule.status != "SCHEDULED":
        return jsonify({
            "error": "SCHEDULE_NOT_FOUND",
            "message": "Train schedule not found or cancelled.",
        }), 404

    try:
        fare_per_passenger = calculate_fare(
            train_id=schedule.train_id,
            source_station_id=source_station_id,
            destination_station_id=destination_station_id,
            coach_class=coach_class,
        )
    except ValueError as exc:
        return jsonify({"error": "FARE_ERROR", "message": str(exc)}), 400

    return jsonify({
        "train_schedule_id": train_schedule_id,
        "source_station_id": source_station_id,
        "destination_station_id": destination_station_id,
        "coach_class": coach_class,
        "passengers": passengers,
        "fare_per_passenger": str(fare_per_passenger),
        "total_fare": str(fare_per_passenger * passengers),
    }), 200

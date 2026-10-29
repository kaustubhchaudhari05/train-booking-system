from flask import Blueprint, jsonify, request

from app.services.availability import get_available_seats

availability_bp = Blueprint(
    "availability",
    __name__,
    url_prefix="/api/availability",
)


@availability_bp.get("/<int:train_schedule_id>")
def get_seat_availability(train_schedule_id):
    coach_class = request.args.get("coach_class", "").upper()
    source = request.args.get("source_stop_order", type=int)
    destination = request.args.get("destination_stop_order", type=int)

    if coach_class not in {"SL", "3A", "2A", "1A"}:
        return jsonify({
            "error": "VALIDATION_ERROR",
            "message": "coach_class must be SL, 3A, 2A, or 1A.",
        }), 400

    if source is None or destination is None:
        return jsonify({
            "error": "VALIDATION_ERROR",
            "message": "source_stop_order and destination_stop_order are required.",
        }), 400

    if source >= destination:
        return jsonify({
            "error": "VALIDATION_ERROR",
            "message": "Source stop must come before destination stop.",
        }), 400

    try:
        seats = get_available_seats(
            train_schedule_id=train_schedule_id,
            coach_class=coach_class,
            source_stop_order=source,
            destination_stop_order=destination,
        )
    except ValueError as exc:
        return jsonify({"error": "VALIDATION_ERROR", "message": str(exc)}), 400

    if seats is None:
        return jsonify({
            "error": "SCHEDULE_NOT_FOUND",
            "message": "Train schedule not found or cancelled.",
        }), 404

    return jsonify({
        "train_schedule_id": train_schedule_id,
        "coach_class": coach_class,
        "source_stop_order": source,
        "destination_stop_order": destination,
        "available_seats": [
            {
                "id": seat.id,
                "coach_id": seat.coach_id,
                "coach_number": seat.coach.coach_number,
                "seat_number": seat.seat_number,
                "berth_type": seat.berth_type,
            }
            for seat in seats
        ],
        "count": len(seats),
    }), 200
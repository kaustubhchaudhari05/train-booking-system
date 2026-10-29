
from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from app.services.booking import (
    BookingError,
    create_booking,
    confirm_booking,
)

booking_bp = Blueprint(
    "booking",
    __name__,
    url_prefix="/api/bookings",
)


@booking_bp.post("")
def create_booking_route():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "INVALID_JSON",
            "message": "Request body must be a JSON object.",
        }), 400

    required_fields = [
        "train_schedule_id",
        "source_station_id",
        "destination_station_id",
        "source_stop_order",
        "destination_stop_order",
        "coach_class",
        "passengers",
    ]

    missing = [
        field for field in required_fields
        if field not in data
    ]

    if missing:
        return jsonify({
            "error": "VALIDATION_ERROR",
            "message": "Missing required fields.",
            "fields": missing,
        }), 400

    try:
        result = create_booking(
            train_schedule_id=data["train_schedule_id"],
            source_station_id=data["source_station_id"],
            destination_station_id=data["destination_station_id"],
            source_stop_order=data["source_stop_order"],
            destination_stop_order=data["destination_stop_order"],
            coach_class=data["coach_class"],
            passengers=data["passengers"],
        )

        return jsonify(result), 201

    except BookingError as exc:
        return jsonify({
            "error": "BOOKING_ERROR",
            "message": str(exc),
        }), exc.status_code

    except SQLAlchemyError:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "DATABASE_ERROR",
            "message": "The booking could not be completed."
        }), 500

    except Exception:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred."
        }), 500


@booking_bp.post("/<int:booking_id>/confirm")
def confirm_booking_route(booking_id):
    try:
        result = confirm_booking(booking_id)
        return jsonify(result), 200

    except BookingError as exc:
        return jsonify({
            "error": "BOOKING_ERROR",
            "message": str(exc),
        }), exc.status_code

    except SQLAlchemyError:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "DATABASE_ERROR",
            "message": "The booking could not be confirmed.",
        }), 500

    except Exception:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred.",
        }), 500

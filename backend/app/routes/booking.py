
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import SQLAlchemyError

from app.auth import current_user_id

from app.services.booking import (
    BookingError,
    cancel_booking,
    cancel_passenger,
    create_booking,
    get_booking_by_reference,
    list_user_bookings,
)

booking_bp = Blueprint(
    "booking",
    __name__,
    url_prefix="/api/bookings",
)


@booking_bp.get("")
@jwt_required()
def list_bookings_route():
    try:
        return jsonify({
            "bookings": list_user_bookings(current_user_id()),
        }), 200

    except SQLAlchemyError:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "DATABASE_ERROR",
            "message": "Your bookings could not be loaded.",
        }), 500


@booking_bp.post("")
@jwt_required()
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
            user_id=current_user_id(),
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


@booking_bp.get("/<string:reference>")
@jwt_required()
def get_booking_route(reference):
    try:
        return jsonify(
            get_booking_by_reference(reference, current_user_id())
        ), 200

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
            "message": "The booking could not be loaded.",
        }), 500


@booking_bp.post("/<string:reference>/cancel")
@jwt_required()
def cancel_booking_route(reference):
    try:
        return jsonify(cancel_booking(reference, current_user_id())), 200

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
            "message": "The booking could not be cancelled.",
        }), 500

    except Exception:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred.",
        }), 500


@booking_bp.post("/<string:reference>/cancel-passenger")
@jwt_required()
def cancel_passenger_route(reference):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "INVALID_JSON",
            "message": "Request body must be a JSON object.",
        }), 400

    try:
        return jsonify(
            cancel_passenger(
                reference, data.get("passenger_name"), current_user_id()
            )
        ), 200

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
            "message": "The passenger could not be cancelled.",
        }), 500

    except Exception:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred.",
        }), 500

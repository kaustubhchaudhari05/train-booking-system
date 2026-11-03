import json

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import SQLAlchemyError

from app.auth import current_user_id

from app.services.payment import (
    PaymentError,
    create_payment_order,
    handle_webhook,
    verify_payment,
)

payments_bp = Blueprint(
    "payments",
    __name__,
    url_prefix="/api/payments",
)


def _error(exc):
    return jsonify({
        "error": exc.code,
        "message": str(exc),
    }), exc.status_code


def _json_body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


@payments_bp.post("/order")
@jwt_required()
def create_order_route():
    data = _json_body()

    if data is None:
        return jsonify({
            "error": "INVALID_JSON",
            "message": "Request body must be a JSON object.",
        }), 400

    try:
        return jsonify(create_payment_order(
            data.get("booking_id"), current_user_id()
        )), 201

    except PaymentError as exc:
        return _error(exc)

    except SQLAlchemyError:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "DATABASE_ERROR",
            "message": "The payment could not be started.",
        }), 500


@payments_bp.post("/verify")
@jwt_required()
def verify_payment_route():
    data = _json_body()

    if data is None:
        return jsonify({
            "error": "INVALID_JSON",
            "message": "Request body must be a JSON object.",
        }), 400

    try:
        return jsonify(verify_payment(
            data.get("razorpay_order_id"),
            data.get("razorpay_payment_id"),
            data.get("razorpay_signature"),
            current_user_id(),
        )), 200

    except PaymentError as exc:
        return _error(exc)

    except SQLAlchemyError:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "DATABASE_ERROR",
            "message": "The payment could not be verified.",
        }), 500


@payments_bp.post("/webhook")
def webhook_route():
    # The signature covers the exact raw body, so read it before parsing.
    raw_body = request.get_data()

    try:
        event = json.loads(raw_body)
    except ValueError:
        return jsonify({"error": "INVALID_JSON"}), 400

    try:
        status = handle_webhook(
            raw_body,
            request.headers.get("X-Razorpay-Signature"),
            event if isinstance(event, dict) else {},
        )
        return jsonify({"status": status}), 200

    except PaymentError as exc:
        return _error(exc)

    except SQLAlchemyError:
        # A 5xx makes Razorpay retry the webhook later.
        import traceback
        traceback.print_exc()
        return jsonify({"error": "DATABASE_ERROR"}), 500

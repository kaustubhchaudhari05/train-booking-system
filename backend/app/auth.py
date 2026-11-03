"""JWT setup shared by the app factory and the routes."""
from datetime import datetime, timedelta, timezone

from flask import jsonify
from flask_jwt_extended import (
    create_access_token,
    get_jwt,
    get_jwt_identity,
    set_access_cookies,
)

from app.extensions import jwt

# Tokens closer than this to expiry are renewed on the next request, so
# an active user is not logged out mid-booking.
REFRESH_WINDOW = timedelta(hours=2)


def current_user_id():
    """The logged-in user's id, or None. Use inside @jwt_required."""
    identity = get_jwt_identity()
    return int(identity) if identity is not None else None


def _unauthorized(message):
    return jsonify({
        "error": "UNAUTHORIZED",
        "message": message,
    }), 401


@jwt.unauthorized_loader
def _missing_token(reason):
    # Also used for a missing or wrong CSRF token.
    if "CSRF" in reason:
        return _unauthorized(
            "Your session check failed. Please log in again."
        )
    return _unauthorized("Please log in to continue.")


@jwt.expired_token_loader
def _expired_token(jwt_header, jwt_payload):
    return _unauthorized("Your session has expired. Please log in again.")


@jwt.invalid_token_loader
def _invalid_token(reason):
    return _unauthorized("Your session is invalid. Please log in again.")


def refresh_expiring_token(response):
    """after_request hook: re-issue the cookie when it is close to expiry."""
    try:
        claims = get_jwt()
    except RuntimeError:
        # This request did not go through @jwt_required.
        return response

    if not claims:
        return response

    expires_at = datetime.fromtimestamp(claims["exp"], timezone.utc)

    if expires_at - datetime.now(timezone.utc) < REFRESH_WINDOW:
        set_access_cookies(
            response, create_access_token(identity=claims["sub"])
        )

    return response

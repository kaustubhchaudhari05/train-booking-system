from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    set_access_cookies,
    unset_jwt_cookies,
)
from sqlalchemy.exc import SQLAlchemyError

from app.auth import current_user_id
from app.services.auth import (
    AuthError,
    authenticate,
    get_user,
    register_user,
)

auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/auth",
)


def _logged_in_response(user, status_code):
    response = jsonify({"user": user.to_dict()})
    set_access_cookies(response, create_access_token(identity=str(user.id)))
    return response, status_code


def _json_body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


def _invalid_json():
    return jsonify({
        "error": "INVALID_JSON",
        "message": "Request body must be a JSON object.",
    }), 400


@auth_bp.post("/register")
def register_route():
    data = _json_body()
    if data is None:
        return _invalid_json()

    try:
        user = register_user(
            data.get("name"), data.get("email"), data.get("password")
        )
        return _logged_in_response(user, 201)

    except AuthError as exc:
        return jsonify({
            "error": exc.code,
            "message": str(exc),
        }), exc.status_code

    except SQLAlchemyError:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "DATABASE_ERROR",
            "message": "The account could not be created.",
        }), 500


@auth_bp.post("/login")
def login_route():
    data = _json_body()
    if data is None:
        return _invalid_json()

    try:
        user = authenticate(data.get("email"), data.get("password"))
        return _logged_in_response(user, 200)

    except AuthError as exc:
        return jsonify({
            "error": exc.code,
            "message": str(exc),
        }), exc.status_code


@auth_bp.post("/logout")
def logout_route():
    # No login needed: clearing the cookies is always safe.
    response = jsonify({"user": None})
    unset_jwt_cookies(response)
    return response, 200


@auth_bp.get("/me")
@jwt_required(optional=True)
def me_route():
    # 200 with user null when logged out, so the app can check the
    # session on load without an error.
    user_id = current_user_id()
    user = get_user(user_id) if user_id is not None else None

    response = jsonify({"user": user.to_dict() if user else None})

    if user_id is not None and user is None:
        # The token names a user that no longer exists.
        unset_jwt_cookies(response)

    return response, 200

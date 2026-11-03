import re

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.user import User

# A practical check, not full RFC 5322; the address is not verified.
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128


class AuthError(Exception):
    def __init__(self, message, status_code=400, code="AUTH_ERROR"):
        super().__init__(message)
        self.status_code = status_code
        self.code = code


def _normalize_email(email):
    return email.strip().lower() if isinstance(email, str) else ""


def register_user(name, email, password):
    if not isinstance(name, str) or not name.strip():
        raise AuthError("Name is required.", code="VALIDATION_ERROR")

    if len(name.strip()) > 100:
        raise AuthError(
            "Name must be at most 100 characters.", code="VALIDATION_ERROR"
        )

    email = _normalize_email(email)

    if not EMAIL_PATTERN.match(email) or len(email) > 255:
        raise AuthError(
            "Enter a valid email address.", code="VALIDATION_ERROR"
        )

    if (
        not isinstance(password, str)
        or not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH
    ):
        raise AuthError(
            f"Password must be {MIN_PASSWORD_LENGTH} to "
            f"{MAX_PASSWORD_LENGTH} characters.",
            code="VALIDATION_ERROR",
        )

    try:
        existing = db.session.execute(
            db.select(User.id).filter_by(email=email)
        ).scalar_one_or_none()

        if existing is not None:
            raise AuthError(
                "An account with this email already exists.",
                409,
                "EMAIL_TAKEN",
            )

        user = User(name=name.strip(), email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    except IntegrityError as exc:
        # Two registrations for the same email at the same moment.
        db.session.rollback()
        raise AuthError(
            "An account with this email already exists.", 409, "EMAIL_TAKEN"
        ) from exc

    except Exception:
        db.session.rollback()
        raise


def authenticate(email, password):
    user = db.session.execute(
        db.select(User).filter_by(email=_normalize_email(email))
    ).scalar_one_or_none()

    # Same message either way, so the response does not reveal which
    # emails are registered.
    if (
        user is None
        or not isinstance(password, str)
        or not user.check_password(password)
    ):
        raise AuthError(
            "Incorrect email or password.", 401, "INVALID_CREDENTIALS"
        )

    return user


def get_user(user_id):
    return db.session.get(User, user_id)

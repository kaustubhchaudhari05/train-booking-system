import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Razorpay test-mode keys. Payments return 503 until the key ID and
    # secret are set; the webhook secret is only needed for webhooks.
    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
    RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
    RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")

    # Login uses a JWT in an httpOnly cookie. CSRF protection is the
    # double-submit kind: the frontend copies the readable
    # csrf_access_token cookie into the X-CSRF-TOKEN header on writes.
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)
    JWT_COOKIE_SAMESITE = "Lax"
    JWT_COOKIE_CSRF_PROTECT = True
    # Must be true in production (HTTPS); plain HTTP during development.
    JWT_COOKIE_SECURE = (
        os.getenv("JWT_COOKIE_SECURE", "false").lower() == "true"
    )

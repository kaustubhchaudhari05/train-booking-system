"""Minimal Razorpay REST client (orders, payments, signatures).

Uses only the standard library. Keys come from the environment through
`Config`; see `.env` for RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET and
RAZORPAY_WEBHOOK_SECRET (all test-mode values during development).
"""
import base64
import hashlib
import hmac
import json
import urllib.error
import urllib.request

from flask import current_app

API_BASE_URL = "https://api.razorpay.com/v1"
TIMEOUT_SECONDS = 15


class RazorpayError(Exception):
    pass


def key_id():
    return current_app.config.get("RAZORPAY_KEY_ID")


def _key_secret():
    return current_app.config.get("RAZORPAY_KEY_SECRET")


def is_configured():
    return bool(key_id() and _key_secret())


def _request(method, path, body=None):
    auth = base64.b64encode(
        f"{key_id()}:{_key_secret()}".encode()
    ).decode()

    request = urllib.request.Request(
        f"{API_BASE_URL}{path}",
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(
            request, timeout=TIMEOUT_SECONDS
        ) as response:
            return json.loads(response.read())

    except urllib.error.HTTPError as exc:
        try:
            detail = json.loads(exc.read())["error"]["description"]
        except Exception:
            detail = f"HTTP {exc.code}"
        raise RazorpayError(detail) from exc

    except (urllib.error.URLError, TimeoutError) as exc:
        raise RazorpayError("Could not reach Razorpay.") from exc


def create_order(amount_paise, currency, receipt, notes=None):
    return _request("POST", "/orders", {
        "amount": amount_paise,
        "currency": currency,
        "receipt": receipt,
        "notes": notes or {},
    })


def fetch_payment(payment_id):
    return _request("GET", f"/payments/{payment_id}")


def capture_payment(payment_id, amount_paise, currency):
    return _request("POST", f"/payments/{payment_id}/capture", {
        "amount": amount_paise,
        "currency": currency,
    })


def _hmac_hex(secret, message):
    return hmac.new(
        secret.encode(), message, hashlib.sha256
    ).hexdigest()


def verify_payment_signature(order_id, payment_id, signature):
    # Checkout signs "<order_id>|<payment_id>" with the key secret.
    expected = _hmac_hex(
        _key_secret(), f"{order_id}|{payment_id}".encode()
    )
    return hmac.compare_digest(expected, signature or "")


def verify_webhook_signature(raw_body, signature):
    secret = current_app.config.get("RAZORPAY_WEBHOOK_SECRET")
    if not secret:
        return False

    expected = _hmac_hex(secret, raw_body)
    return hmac.compare_digest(expected, signature or "")

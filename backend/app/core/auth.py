import base64
import binascii
import hashlib
import hmac
import json
import os
import time
from pathlib import Path
from dotenv import dotenv_values, load_dotenv

from fastapi import HTTPException, Request, Response

_ENV_PATH = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(_ENV_PATH)
_ENV_VALUES = dotenv_values(_ENV_PATH)


def configured_env(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value:
        return value
    return str(_ENV_VALUES.get(name) or default)

COOKIE_NAME = "nexus_session"
SESSION_SECONDS = 60 * 60 * 12


def _secret() -> bytes:
    secret = configured_env("NEXUS_SECRET_KEY").strip()
    if len(secret) < 32:
        raise HTTPException(status_code=503, detail="Authentication is not configured. Set NEXUS_SECRET_KEY (32+ characters).")
    return secret.encode()


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def create_session(email: str) -> str:
    payload = _b64(json.dumps({"sub": email, "exp": int(time.time()) + SESSION_SECONDS}).encode())
    signature = _b64(hmac.new(_secret(), payload.encode(), hashlib.sha256).digest())
    return f"{payload}.{signature}"


def read_session(token: str) -> str | None:
    try:
        payload, signature = token.split(".", 1)
        expected = _b64(hmac.new(_secret(), payload.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            return None
        decoded = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
        claims = json.loads(decoded)
        if not isinstance(claims, dict):
            return None
        if claims.get("exp", 0) <= time.time() or not isinstance(claims.get("sub"), str):
            return None
        return claims["sub"]
    except (ValueError, TypeError, UnicodeDecodeError, binascii.Error):
        return None


def require_session(request: Request) -> str:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        authorization = request.headers.get("authorization", "")
        if authorization.lower().startswith("bearer "):
            token = authorization[7:].strip()
    email = read_session(token) if token else None
    if not email:
        raise HTTPException(status_code=401, detail="Sign in to access NEXUS.")
    return email


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=SESSION_SECONDS,
        httponly=True,
        secure=os.getenv("NEXUS_COOKIE_SECURE", "false").lower() == "true",
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/", httponly=True, samesite="lax")

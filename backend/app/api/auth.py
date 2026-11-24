import hmac
import os

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from ..core.auth import clear_session_cookie, configured_env, create_session, require_session, set_session_cookie

router = APIRouter()


class LoginRequest(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str


@router.post("/login")
def login(payload: LoginRequest, response: Response):
    configured_email = configured_env("NEXUS_ADMIN_EMAIL").strip().lower()
    configured_password = configured_env("NEXUS_ADMIN_PASSWORD")
    if not configured_email or len(configured_password) < 12:
        raise HTTPException(
            status_code=503,
            detail="Boss account is not configured. Set NEXUS_ADMIN_EMAIL and a NEXUS_ADMIN_PASSWORD of at least 12 characters.",
        )
    if not hmac.compare_digest(payload.email.lower().encode(), configured_email.encode()) or not hmac.compare_digest(
        payload.password.encode(), configured_password.encode()
    ):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    token = create_session(configured_email)
    set_session_cookie(response, token)
    return {"user": {"email": configured_email, "name": "Boss", "role": "administrator"}}


@router.post("/logout")
def logout(response: Response):
    clear_session_cookie(response)
    return {"status": "signed_out"}


@router.get("/me")
def me(email: str = Depends(require_session)):
    return {"email": email, "name": "Boss", "role": "administrator"}

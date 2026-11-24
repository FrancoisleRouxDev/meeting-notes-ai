import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session as DbSession

from app.core.config import settings
from app.core.security import hash_password
from app.db import get_db
from app.models import PasswordResetToken, User, UserSession      

log = logging.getLogger(__name__)
router = APIRouter(prefix="/auth/password-reset", tags=["auth"])
RESET_MINUTES = 30

class ResetRequest(BaseModel):
    email: EmailStr

class ResetConfirm(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    new_password: str = Field(min_length=10, max_length=200)  # reuse your register rules

def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def _now() -> datetime:
    # SQLite returns naive datetimes, so store and compare naive UTC
    return datetime.now(timezone.utc).replace(tzinfo=None)

def send_reset_email(to: str, link: str) -> None:
    if not settings.resend_api_key:
        if settings.password_reset_dev_log:      # local development only
            log.warning("Password reset link for %s: %s", to, link)
        return
    httpx.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {settings.resend_api_key}"},
        json={
            "from": settings.mail_from,
            "to": [to],
            "subject": "Reset your Meeting Notes AI password",
            "text": f"Reset your password within {RESET_MINUTES} minutes:\n{link}\n\n"
                    "If you did not ask for this, you can ignore this email.",
        },
        timeout=10,
    )

@router.post("/request")
def request_reset(body: ResetRequest, db: DbSession = Depends(get_db)):
    user = db.scalar(select(User).where(
        User.email == body.email.lower(), User.deleted_at.is_(None)))
    if user:
        token = secrets.token_urlsafe(32)
        db.add(PasswordResetToken(
            user_id=user.id,
            token_hash=_hash(token),
            expires_at=_now() + timedelta(minutes=RESET_MINUTES),
        ))
        db.commit()
        link = f"{settings.public_app_url}/reset-password?token={token}"
        send_reset_email(user.email, link)
    return {"message": "If that email has an account, a reset link is on its way."}

@router.post("/confirm")
def confirm_reset(body: ResetConfirm, db: DbSession = Depends(get_db)):
    invalid = HTTPException(400, "This reset link is invalid or has expired.")
    record = db.scalar(select(PasswordResetToken).where(
        PasswordResetToken.token_hash == _hash(body.token)))
    if record is None or record.used_at is not None or record.expires_at < _now():
        raise invalid
    user = db.get(User, record.user_id)
    if user is None or user.deleted_at is not None:
        raise invalid

    now = _now()
    user.password_hash = hash_password(body.new_password)   # your existing argon2 helper
    record.used_at = now
    db.execute(update(PasswordResetToken)
               .where(PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None))
               .values(used_at=now))                         # invalidate any other links
    db.execute(delete(UserSession).where(UserSession.user_id == user.id))
    db.commit()
    return {"message": "Password updated. Please log in."}
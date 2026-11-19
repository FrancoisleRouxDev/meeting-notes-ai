from datetime import datetime, timezone

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_token
from app.db import get_db
from app.models import User, UserSession

SESSION_COOKIE = "session"


def get_current_user(
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE),
    db: Session = Depends(get_db),
) -> User:
    # Same error for every failure, so the response doesn't reveal why access was refused.
    unauthorized = HTTPException(status_code=401, detail="Not logged in")

    if not session_token:
        raise unauthorized

    session = db.scalar(
        select(UserSession).where(UserSession.token_hash == hash_token(session_token))
    )
    if session is None:
        raise unauthorized

    # SQLite returns datetimes without timezone info, so add UTC when it's missing.
    expires = session.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc):
        raise unauthorized

    user = db.get(User, session.user_id)
    # Deleted accounts are locked out even if they still hold a valid session.
    if user is None or user.deleted_at is not None:
        raise unauthorized
    return user

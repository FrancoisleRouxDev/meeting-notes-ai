from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import SESSION_COOKIE, get_current_user
from app.core.security import (
    hash_password,
    hash_token,
    new_session_token,
    verify_password,
)
from app.db import get_db
from app.models import User, UserSession
from app.schemas import LoginIn, RegisterIn, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _start_session(user: User, response: Response, db: Session) -> None:
    token = new_session_token()
    db.add(
        UserSession(
            token_hash=hash_token(token),
            user_id=user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.session_days),
        )
    )
    db.commit()
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,  # JavaScript on the page can't read the cookie
        samesite="lax",  # blocks the cookie on most cross-site form posts
        secure=settings.session_cookie_secure,
        max_age=settings.session_days * 24 * 3600,
    )


@router.post("/register", response_model=UserOut, status_code=201)
def register(body: RegisterIn, response: Response, db: Session = Depends(get_db)):
    user = User(email=body.email.lower(), password_hash=hash_password(body.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    db.refresh(user)
    _start_session(user, response, db)
    return user


@router.post("/login", response_model=UserOut)
def login(body: LoginIn, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(
        select(User).where(User.email == body.email.lower(), User.deleted_at.is_(None))
    )
    # One message for both "no such email" and "wrong password", so it doesn't reveal which.
    if user is None or not verify_password(user.password_hash, body.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    _start_session(user, response, db)
    return user


@router.post("/logout", status_code=204)
def logout(
    response: Response,
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE),
    db: Session = Depends(get_db),
):
    if session_token:
        db.execute(delete(UserSession).where(UserSession.token_hash == hash_token(session_token)))
        db.commit()
    response.delete_cookie(SESSION_COOKIE)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.delete("/me", status_code=204)
def delete_account(
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Soft delete: the user's meetings and action items stay in the database.
    user.deleted_at = datetime.now(timezone.utc)
    # Sessions are removed for real, so the account is logged out everywhere immediately.
    db.execute(delete(UserSession).where(UserSession.user_id == user.id))
    db.commit()
    response.delete_cookie(SESSION_COOKIE)

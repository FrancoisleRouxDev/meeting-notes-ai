from datetime import date, datetime, timezone

from sqlalchemy import JSON, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Unique across all users, including deleted ones. So a deleted email can't register again.
    # This is a deliberate simplification, noted in the README.
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    # Soft delete: the row stays, and every lookup filters out users where this is set.
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)


class UserSession(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    # We store a hash of the session token, never the token itself.
    # A leaked database can't be used to log in.
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Every meeting query filters on this. Ownership is decided on the server, never by the client.
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    meeting_date: Mapped[date] = mapped_column(Date)
    # Stored exactly as received, before any AI call. If the AI fails, the transcript is still here.
    transcript: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    # AI results. Only written when the whole analysis succeeds, so a failed run never leaves partial data.
    summary: Mapped[str | None] = mapped_column(Text, default=None)
    decisions: Mapped[list[str] | None] = mapped_column(JSON, default=None)
    # pending, done or failed. A failed meeting can be retried.
    analysis_status: Mapped[str] = mapped_column(String(20), default="pending")
    analysis_error: Mapped[str | None] = mapped_column(String(200), default=None)

    action_items: Mapped[list["ActionItem"]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan", order_by="ActionItem.id"
    )


class ActionItem(Base):
    __tablename__ = "action_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id"), index=True)
    text: Mapped[str] = mapped_column(String(500))
    # Blank unless the transcript names them. The AI never guesses an owner or a date.
    owner: Mapped[str | None] = mapped_column(String(100), default=None)
    due_date: Mapped[date | None] = mapped_column(Date, default=None)
    source_line: Mapped[int | None] = mapped_column(default=None)
    # to do, in progress or done. Users change this, and the AI always creates items as "to do".
    status: Mapped[str] = mapped_column(String(20), default="to do")

    meeting: Mapped[Meeting] = relationship(back_populates="action_items")
    
class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    

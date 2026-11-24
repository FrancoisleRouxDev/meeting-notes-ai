from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class SlackConnection(Base):
    """One Slack webhook per user. The URL is stored encrypted, never in plain text."""

    __tablename__ = "slack_connections"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    webhook_encrypted: Mapped[str] = mapped_column(String(1000))

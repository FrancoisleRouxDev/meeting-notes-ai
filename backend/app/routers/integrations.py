from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db import get_db
from app.models import User
from app.models_slack import SlackConnection
from app.routers.meetings import _get_owned_meeting
from app.services import crypto
from app.services.slack import SlackUnavailable, post_meeting_to_slack

router = APIRouter(prefix="/integrations/slack", tags=["integrations"])

WEBHOOK_PREFIX = "https://hooks.slack.com/services/"


class SlackConnectionIn(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def must_be_slack_webhook(cls, value: str) -> str:
        value = value.strip()
        if not value.startswith(WEBHOOK_PREFIX) or len(value) > 300:
            raise ValueError(f"Paste a Slack webhook URL that starts with {WEBHOOK_PREFIX}")
        return value


def _connection(user: User, db: Session) -> SlackConnection | None:
    return db.get(SlackConnection, user.id)


@router.get("/connection")
def get_connection(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Only whether a channel is connected is returned. The URL never leaves the server.
    return {"connected": _connection(user, db) is not None}


@router.put("/connection")
def save_connection(
    body: SlackConnectionIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        encrypted = crypto.encrypt(body.url)
    except crypto.EncryptionUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    connection = _connection(user, db)
    if connection is None:
        db.add(SlackConnection(user_id=user.id, webhook_encrypted=encrypted))
    else:
        connection.webhook_encrypted = encrypted
    db.commit()
    return {"connected": True}


@router.delete("/connection", status_code=204)
def remove_connection(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    connection = _connection(user, db)
    if connection is not None:
        db.delete(connection)
        db.commit()


@router.post("/share/{meeting_id}")
async def share_meeting(
    meeting_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Ownership of the meeting is checked first, then the user's own webhook is used.
    meeting = _get_owned_meeting(meeting_id, user, db)
    connection = _connection(user, db)
    if connection is None:
        raise HTTPException(status_code=409, detail="Connect your Slack channel on the Account page first")
    try:
        webhook_url = crypto.decrypt(connection.webhook_encrypted)
        await post_meeting_to_slack(meeting, webhook_url)
    except (crypto.EncryptionUnavailable, SlackUnavailable) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"sent": True}

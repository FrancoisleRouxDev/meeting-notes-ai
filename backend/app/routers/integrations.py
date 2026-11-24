from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db import get_db
from app.models import User
from app.routers.meetings import _get_owned_meeting
from app.services.slack import SlackUnavailable, post_meeting_to_slack

router = APIRouter(prefix="/meetings", tags=["integrations"])


@router.post("/{meeting_id}/share/slack")
async def share_meeting_to_slack(
    meeting_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Ownership is checked first, so one user can't post another user's meeting.
    meeting = _get_owned_meeting(meeting_id, user, db)
    try:
        await post_meeting_to_slack(meeting)
    except SlackUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"sent": True}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db import get_db
from app.models import ActionItem, Meeting, User
from app.schemas import ActionItemOut, ActionItemCreate, ActionItemUpdate

router = APIRouter(tags=["action items"])

def _get_owned_item(item_id: int, user: User, db: Session) -> ActionItem:
    # The join checks ownership on the server. An item in someone else's meeting
    # gets the same 404 as one that doesn't exist.
    item = db.scalar(
        select(ActionItem)
        .join(Meeting, ActionItem.meeting_id == Meeting.id)
        .where(ActionItem.id == item_id, Meeting.user_id == user.id)
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Action item not found")
    return item


@router.post("/meetings/{meeting_id}/action-items", response_model=ActionItemOut, status_code=201)
def add_action_item(
    meeting_id: int,
    body: ActionItemCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    meeting = _get_owned_meeting(meeting_id, user, db)
    item = ActionItem(meeting_id=meeting.id, **body.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/action-items/{item_id}", response_model=ActionItemOut)
def update_action_item(
    item_id: int,
    body: ActionItemUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = _get_owned_item(item_id, user, db)
    # Only the fields the client sent are changed.
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/action-items/{item_id}", status_code=204)
def delete_action_item(
    item_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = _get_owned_item(item_id, user, db)
    db.delete(item)
    db.commit()
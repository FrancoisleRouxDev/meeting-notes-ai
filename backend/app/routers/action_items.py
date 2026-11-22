from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db import get_db
from app.models import ActionItem, Meeting, User
from app.schemas import ActionItemOut, ActionItemCreate, ActionItemUpdate
from app.routers.meetings import _get_owned_meeting
from apps.schemas import (
    ALLOWED_STATUSES,
    ActionItemOut,
    ActionItemCreate,
    ActionItemUpdate,
    ActionItemWithMeeting,
)

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


@router.get("/action-items", response_model=list[ActionItemWithMeeting])
def list_action_items(
    status: str | None = None,
    owner: str | None = None,
    overdue: bool = False,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = (
        select(ActionItem, Meeting.title)
        .join(Meeting, ActionItem.meeting_id == Meeting.id)
        .where(Meeting.user_id == user.id)
    )

    if status is not None:
        if status not in ALLOWED_STATUSES:
            raise HTTPException(status_code=422, detail="status must be 'to do', 'in progress' or 'done'")
        query = query.where(ActionItem.status == status)
    else:
        # The default view is the open items: anything not yet done.
        query = query.where(ActionItem.status != "done")

    if owner is not None and owner.strip():
        query = query.where(func.lower(ActionItem.owner) == owner.strip().lower())

    if overdue:
        query = query.where(ActionItem.due_date < date.today(), ActionItem.status != "done")

    # Items with a due date come first, earliest first. Items without one come last.
    query = query.order_by(ActionItem.due_date.is_(None), ActionItem.due_date, ActionItem.id)

    rows = db.execute(query).all()
    return [
        {
            **ActionItemOut.model_validate(item).model_dump(),
            "meeting_id": item.meeting_id,
            "meeting_title": title,
        }
        for item, title in rows
    ]


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
    

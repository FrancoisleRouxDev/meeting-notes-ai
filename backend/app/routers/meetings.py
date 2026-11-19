from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db import get_db
from app.models import Meeting, User
from app.schemas import MeetingCreate, MeetingDetail, MeetingOut
from app.services.transcript import read_transcript_upload

router = APIRouter(prefix="/meetings", tags=["meetings"])


def _get_owned_meeting(meeting_id: int, user: User, db: Session) -> Meeting:
    # A meeting belonging to someone else gets the same 404 as one that doesn't exist.
    # That way, changing the ID in the URL reveals nothing.
    meeting = db.scalar(
        select(Meeting).where(Meeting.id == meeting_id, Meeting.user_id == user.id)
    )
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


def _save_meeting(title: str, meeting_date: date, transcript: str, user: User, db: Session) -> Meeting:
    # user_id comes from the logged-in session, never from the request body.
    meeting = Meeting(user_id=user.id, title=title, meeting_date=meeting_date, transcript=transcript)
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


@router.post("", response_model=MeetingDetail, status_code=201)
def create_meeting(
    body: MeetingCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _save_meeting(body.title, body.meeting_date, body.transcript, user, db)


@router.post("/upload", response_model=MeetingDetail, status_code=201)
async def upload_meeting(
    title: str = Form(min_length=1, max_length=200),
    meeting_date: date = Form(),
    file: UploadFile = File(),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    title = title.strip()
    if not title:
        raise HTTPException(status_code=422, detail="Title must not be blank")
    transcript = (await read_transcript_upload(file)).strip()
    if not transcript:
        raise HTTPException(status_code=422, detail="Transcript must not be blank")
    return _save_meeting(title, meeting_date, transcript, user, db)


@router.get("", response_model=list[MeetingOut])
def list_meetings(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(
        select(Meeting)
        .where(Meeting.user_id == user.id)
        .order_by(Meeting.meeting_date.desc(), Meeting.id.desc())
    ).all()


@router.get("/{meeting_id}", response_model=MeetingDetail)
def get_meeting(meeting_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _get_owned_meeting(meeting_id, user, db)

from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db import get_db
from app.models import ActionItem, Meeting, User
from app.schemas import MeetingCreate, MeetingDetail, MeetingOut, MeetingUpdate
from app.services.ai import AIInvalidOutput, AIUnavailable, analyse_transcript
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


@router.post("/{meeting_id}/analyse", response_model=MeetingDetail)
async def analyse_meeting(
    meeting_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    meeting = _get_owned_meeting(meeting_id, user, db)
    if meeting.analysis_status == "done":
        # Re-running would replace action items the user may have already edited.
        raise HTTPException(status_code=409, detail="This meeting has already been analysed")

    try:
        summary, decisions, items = await analyse_transcript(meeting.transcript, meeting.meeting_date)
    except (AIUnavailable, AIInvalidOutput) as exc:
        # The transcript is already saved. Record the failure so the user can retry.
        meeting.analysis_status = "failed"
        meeting.analysis_error = str(exc)[:200]
        db.commit()
        raise HTTPException(status_code=503, detail=str(exc))

    meeting.summary = summary
    meeting.decisions = decisions
    meeting.analysis_status = "done"
    meeting.analysis_error = None
    for item in items:
        db.add(
            ActionItem(
                meeting_id=meeting.id,
                text=item.text,
                owner=item.owner,
                due_date=item.due_date,
            )
        )
    db.commit()
    db.refresh(meeting)
    return meeting

@router.delete("/{meeting_id}", status_code=204)
def delete_meeting(
    meeting_id: int,
    confirm: bool = False,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Deleting is permament. The request must say it has been comfirmed.
    # The frontend shows the "are you sure?" dialog and then sends confirm=true.
    if not confirm: 
        raise HTTPException(status_code=400, detail="Set confirm=true to delete this meeting")
    meeting = _get_owned_meeting(meeting_id, user, db)
    # Action items are deleted with the meeting (cascade set in models.py)
    db.delete(meeting)
    db.commit()


@router.patch("/{meeting_id}", response_model=MeetingDetail)
def update_meeting(
    meeting_id: int,
    body: MeetingUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    meeting = _get_owned_meeting(meeting_id, user, db)
    # Only the fields the client sent are changed.
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(meeting, field, value)
    db.commit()
    db.refresh(meeting)
    return meeting

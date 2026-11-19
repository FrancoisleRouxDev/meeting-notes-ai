from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterIn(BaseModel):
    email: EmailStr
    # Length matters more than complexity rules. Limits stop oversized input.
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    # Never includes password_hash. Only fields listed here are sent to the client.
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str


class MeetingCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    meeting_date: date
    # 200,000 characters is roughly 30,000 words, far longer than a normal meeting.
    transcript: str = Field(min_length=1, max_length=200_000)

    @field_validator("title", "transcript")
    @classmethod
    def not_blank(cls, value: str) -> str:
        # min_length passes for "   ", so whitespace-only input is rejected here.
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class MeetingOut(BaseModel):
    # List view: no transcript, so the list stays small.
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    meeting_date: date
    created_at: datetime


class MeetingDetail(MeetingOut):
    # Detail view: adds the full original transcript.
    transcript: str

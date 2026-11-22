from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

class MeetingUpdate(BaseModel):
    # only the fields the client send are changed.
    title: str | None = Field(default=None, min_length=1, max_length=200)
    summary: str | None = Field(default=None, max_length=2000)
    decisions: list [str] | None = Field(default=None, max_legth=50)
    
    @field_validator("title", "summary")
    @classmethod
    def title_rules(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("cannot be empty")
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value
    
class ActionItemCreate(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    owner: str | None = Field(default=None, max_length=100)
    due_date: date | None = None
    status: str = "to do"

    @field_validator("text")
    @classmethod
    def text_rules(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("status")
    @classmethod
    def status_rules(cls, value: str) -> str:
        if value not in ALLOWED_STATUSES:
            raise ValueError("must be 'to do', 'in progress' or 'done'")
        return value


class ActionItemUpdate(BaseModel):
    # Fields left out of the request are not changed. Sending null for owner or due_date clears it.
    text: str | None = Field(default=None, min_length=1, max_length=500)
    owner: str | None = Field(default=None, max_length=100)
    due_date: date | None = None
    status: str | None = None

    @field_validator("text")
    @classmethod
    def text_rules(cls, value: str | None) -> str | None:
        # This only runs when the field is sent. Sending null here is refused.
        if value is None:
            raise ValueError("cannot be empty")
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("status")
    @classmethod
    def status_rules(cls, value: str | None) -> str | None:
        if value is None or value not in ALLOWED_STATUSES:
            raise ValueError("must be 'to do', 'in progress' or 'done'")
        return value
    
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
    # List view: no transcript or AI results, so the list stays small.
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    meeting_date: date
    created_at: datetime


class ActionItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    owner: str | None
    due_date: date | None
    status: str


class MeetingDetail(MeetingOut):
    transcript: str
    summary: str | None
    decisions: list[str] | None
    analysis_status: str
    analysis_error: str | None
    action_items: list[ActionItemOut]


# What the AI is asked to return. Pydantic checks every field, and the same models
# generate the JSON schema that is sent to OpenRouter.
class AISummary(BaseModel):
    summary: str = Field(min_length=1, max_length=2000)


class AIDecisions(BaseModel):
    decisions: list[str] = Field(max_length=30)
    
    @field_validator("decisions")
    @classmethod
    def clean_decisions(cls, items: list[str]) -> list[str]:
        #Some models prefix items with ":" or "-", this strips that.
        cleaned = [item.lstrip(" :-*•").strip() for item in items]
        return [item for item in cleaned if item]

class AIActionItem(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    owner: str | None = None
    due_date: date | None = None


class AIActionItems(BaseModel):
    action_items: list[AIActionItem] = Field(max_length=50)
    
class ActionitemWithMeeting(ActionItemOut):
    meeting_id: int
    meeting_title: str
    
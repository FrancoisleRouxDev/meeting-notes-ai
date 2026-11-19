from pydantic import BaseModel, ConfigDict, EmailStr, Field


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

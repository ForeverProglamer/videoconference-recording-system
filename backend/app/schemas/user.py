from datetime import datetime

from pydantic import BaseModel, Field

from app.utils.auth import (
    generate_session_token, generate_expiration_datetime
)


class SessionBase(BaseModel):
    token: str = Field(default_factory=generate_session_token)
    expires_at: datetime = Field(default_factory=generate_expiration_datetime)


class UserBase(BaseModel):
    login: str
    password: str


class UserCreate(UserBase):
    ...


class UserRead(UserBase):
    ...


class UserInDb(UserBase):
    id: int

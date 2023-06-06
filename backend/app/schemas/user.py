from datetime import datetime

from pydantic import BaseModel

from app.utils.auth import (
    generate_session_token, generate_expiration_datetime
)


class SessionBase(BaseModel):
    token: str = generate_session_token()
    expires_at: datetime = generate_expiration_datetime()


class UserBase(BaseModel):
    login: str
    password: str


class UserCreate(UserBase):
    ...


class UserRead(UserBase):
    ...


class UserInDb(UserBase):
    id: int

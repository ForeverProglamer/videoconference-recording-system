from pydantic import BaseModel


class UserBase(BaseModel):
    login: str
    password: str


class UserCreate(UserBase):
    ...


class UserRead(UserBase):
    id: int

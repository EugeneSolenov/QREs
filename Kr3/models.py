from typing import Literal

from pydantic import BaseModel as B, Field as F


Role = Literal["admin", "user", "guest"]


class UserBase(B):
    username: str = F(..., min_length=1, max_length=64)


class User(UserBase):
    password: str = F(..., min_length=1, max_length=128)
    role: Role = "user"


class UserInDB(UserBase):
    hashed_password: str
    role: Role = "user"


class LoginRequest(UserBase):
    password: str = F(..., min_length=1, max_length=128)


class Token(B):
    access_token: str
    token_type: str = "bearer"


class Message(B):
    message: str


class TodoCreate(B):
    title: str = F(..., min_length=1, max_length=200)
    description: str = F(..., min_length=1, max_length=1000)


class TodoUpdate(TodoCreate):
    completed: bool


class TodoOut(TodoUpdate):
    id: int

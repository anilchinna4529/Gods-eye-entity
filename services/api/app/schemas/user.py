from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import APIModel


class UserOut(APIModel):
    id: str
    email: EmailStr
    role: str
    is_active: bool


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="viewer")


class UserUpdate(BaseModel):
    role: str | None = None
    is_active: bool | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import APIModel


class AlertOut(APIModel):
    id: str
    kind: str
    severity: str
    title: str
    description: str
    status: str
    acked_by_user_id: str | None
    acked_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AlertCreate(BaseModel):
    kind: str = "generic"
    severity: str = Field(default="low")
    title: str = Field(min_length=1, max_length=255)
    description: str = ""


class AlertUpdate(BaseModel):
    status: str | None = None


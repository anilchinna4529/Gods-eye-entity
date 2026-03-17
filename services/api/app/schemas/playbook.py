from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import APIModel


class PlaybookOut(APIModel):
    id: str
    name: str
    description: str
    definition: dict[str, Any]
    enabled: bool
    created_at: datetime
    updated_at: datetime


class PlaybookCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = ""
    definition: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class PlaybookUpdate(BaseModel):
    description: str | None = None
    definition: dict[str, Any] | None = None
    enabled: bool | None = None


from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import APIModel


class FindingOut(APIModel):
    id: str
    asset_id: str | None
    title: str
    description: str
    severity: str
    status: str
    source: str | None
    evidence: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class FindingCreate(BaseModel):
    asset_id: str | None = None
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    severity: str = Field(default="medium")
    status: str = Field(default="open")
    source: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)


class FindingUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    severity: str | None = None
    status: str | None = None
    evidence: dict[str, Any] | None = None


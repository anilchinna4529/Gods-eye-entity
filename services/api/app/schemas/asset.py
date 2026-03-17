from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import APIModel


class AssetOut(APIModel):
    id: str
    hostname: str
    ip: str | None
    owner: str | None
    tags: list[str]
    meta: dict[str, Any] = Field(serialization_alias="metadata")
    last_seen: datetime | None
    created_at: datetime
    updated_at: datetime


class AssetCreate(BaseModel):
    hostname: str = Field(min_length=1, max_length=255)
    ip: str | None = Field(default=None, max_length=64)
    owner: str | None = Field(default=None, max_length=255)
    tags: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict, validation_alias="metadata")


class AssetUpdate(BaseModel):
    hostname: str | None = Field(default=None, min_length=1, max_length=255)
    ip: str | None = Field(default=None, max_length=64)
    owner: str | None = Field(default=None, max_length=255)
    tags: list[str] | None = None
    meta: dict[str, Any] | None = Field(default=None, validation_alias="metadata")
    last_seen: datetime | None = None


class RelationshipOut(APIModel):
    id: str
    from_asset_id: str
    to_asset_id: str
    kind: str
    meta: dict[str, Any] = Field(serialization_alias="metadata")


class RelationshipCreate(BaseModel):
    from_asset_id: str
    to_asset_id: str
    kind: str = "connected_to"
    meta: dict[str, Any] = Field(default_factory=dict, validation_alias="metadata")

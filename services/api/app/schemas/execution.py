from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.common import APIModel


class ExecutionOut(APIModel):
    id: str
    execution_type: str
    action: str | None
    status: str
    params: dict[str, Any]
    result: dict[str, Any]
    log: str
    playbook_id: str | None
    created_by_user_id: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class ExecutionCreate(BaseModel):
    execution_type: Literal["playbook", "action"] = "playbook"
    playbook_id: str | None = None
    action: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)


class ApprovalOut(APIModel):
    id: str
    execution_id: str
    status: str
    reason: str
    requested_by_user_id: str | None
    decided_by_user_id: str | None
    created_at: datetime
    decided_at: datetime | None


class ApprovalRequest(BaseModel):
    reason: str = ""


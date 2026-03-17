from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import write_audit_log
from app.core.config import settings
from app.db.models import Approval, Execution, Playbook, User
from app.db.session import get_db
from app.realtime.redis_bus import publish_event_sync
from app.schemas.execution import ApprovalOut, ApprovalRequest, ExecutionCreate, ExecutionOut
from app.security.deps import get_request_meta, require_roles
from app.tasks.tasks import run_execution


router = APIRouter()


@router.get("", response_model=list[ExecutionOut])
def list_executions(
    limit: int = 200,
    offset: int = 0,
    _: User = Depends(require_roles("admin", "analyst", "viewer")),
    db: Session = Depends(get_db),
) -> list[Execution]:
    stmt = select(Execution).order_by(Execution.created_at.desc()).limit(limit).offset(offset)
    return list(db.execute(stmt).scalars().all())


@router.post("", response_model=ExecutionOut, status_code=status.HTTP_201_CREATED)
def create_execution(
    payload: ExecutionCreate,
    request: Request,
    actor: User = Depends(require_roles("admin", "analyst")),
    db: Session = Depends(get_db),
) -> Execution:
    if payload.execution_type == "playbook":
        if not payload.playbook_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="playbook_id required")
        pb = db.get(Playbook, payload.playbook_id)
        if pb is None or not pb.enabled:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid playbook")

        requires_approval = bool((pb.definition or {}).get("requires_approval"))
        status_value = "requires_approval" if requires_approval else "queued"

        execution = Execution(
            execution_type="playbook",
            playbook_id=pb.id,
            params=payload.params,
            status=status_value,
            created_by_user_id=actor.id,
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)

        if requires_approval:
            approval = Approval(execution_id=execution.id, status="pending", requested_by_user_id=actor.id, reason="")
            db.add(approval)
            db.commit()
        else:
            if settings.environment != "test":
                run_execution.delay(execution.id)
    else:
        if not payload.action:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="action required")
        execution = Execution(
            execution_type="action",
            action=payload.action,
            params=payload.params,
            status="queued",
            created_by_user_id=actor.id,
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        if settings.environment != "test":
            run_execution.delay(execution.id)

    meta = get_request_meta(request)
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="executions.create",
        resource_type="execution",
        resource_id=execution.id,
        details={"type": execution.execution_type, "status": execution.status},
        ip=meta["ip"],
        user_agent=meta["user_agent"],
    )
    publish_event_sync({"type": "execution.updated", "data": {"id": execution.id, "status": execution.status}})
    return execution


@router.get("/{execution_id}", response_model=ExecutionOut)
def get_execution(
    execution_id: str, _: User = Depends(require_roles("admin", "analyst", "viewer")), db: Session = Depends(get_db)
) -> Execution:
    execution = db.get(Execution, execution_id)
    if execution is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return execution


@router.post("/{execution_id}/approve", response_model=ApprovalOut)
def approve_execution(
    execution_id: str,
    payload: ApprovalRequest,
    request: Request,
    actor: User = Depends(require_roles("admin", "analyst")),
    db: Session = Depends(get_db),
) -> Approval:
    execution = db.get(Execution, execution_id)
    if execution is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if execution.status != "requires_approval":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Execution does not require approval")

    approval = db.execute(select(Approval).where(Approval.execution_id == execution_id)).scalar_one_or_none()
    if approval is None:
        approval = Approval(execution_id=execution.id, status="pending", requested_by_user_id=execution.created_by_user_id)
        db.add(approval)
        db.commit()
        db.refresh(approval)

    approval.status = "approved"
    approval.decided_by_user_id = actor.id
    approval.reason = payload.reason
    approval.decided_at = datetime.now(timezone.utc)

    execution.status = "queued"
    db.commit()
    db.refresh(approval)

    meta = get_request_meta(request)
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="executions.approve",
        resource_type="execution",
        resource_id=execution.id,
        details={"approval_id": approval.id, "reason": payload.reason},
        ip=meta["ip"],
        user_agent=meta["user_agent"],
    )

    publish_event_sync({"type": "execution.updated", "data": {"id": execution.id, "status": execution.status}})
    if settings.environment != "test":
        run_execution.delay(execution.id)
    return approval

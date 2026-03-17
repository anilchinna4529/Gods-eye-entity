from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import write_audit_log
from app.db.models import Finding, User
from app.db.session import get_db
from app.realtime.redis_bus import publish_event_sync
from app.schemas.finding import FindingCreate, FindingOut, FindingUpdate
from app.security.deps import get_request_meta, require_roles


router = APIRouter()


@router.get("", response_model=list[FindingOut])
def list_findings(
    status_filter: str | None = None,
    severity: str | None = None,
    asset_id: str | None = None,
    limit: int = 200,
    offset: int = 0,
    _: User = Depends(require_roles("admin", "analyst", "viewer")),
    db: Session = Depends(get_db),
) -> list[Finding]:
    stmt = select(Finding).order_by(Finding.updated_at.desc()).limit(limit).offset(offset)
    if status_filter:
        stmt = stmt.where(Finding.status == status_filter)
    if severity:
        stmt = stmt.where(Finding.severity == severity)
    if asset_id:
        stmt = stmt.where(Finding.asset_id == asset_id)
    return list(db.execute(stmt).scalars().all())


@router.post("", response_model=FindingOut, status_code=status.HTTP_201_CREATED)
def create_finding(
    payload: FindingCreate,
    request: Request,
    actor: User = Depends(require_roles("admin", "analyst")),
    db: Session = Depends(get_db),
) -> Finding:
    finding = Finding(
        asset_id=payload.asset_id,
        title=payload.title,
        description=payload.description,
        severity=payload.severity,
        status=payload.status,
        source=payload.source,
        evidence=payload.evidence,
    )
    db.add(finding)
    db.commit()
    db.refresh(finding)

    meta = get_request_meta(request)
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="findings.create",
        resource_type="finding",
        resource_id=finding.id,
        details={"title": finding.title, "severity": finding.severity},
        ip=meta["ip"],
        user_agent=meta["user_agent"],
    )
    publish_event_sync({"type": "finding.created", "data": {"id": finding.id}})
    return finding


@router.get("/{finding_id}", response_model=FindingOut)
def get_finding(
    finding_id: str, _: User = Depends(require_roles("admin", "analyst", "viewer")), db: Session = Depends(get_db)
) -> Finding:
    finding = db.get(Finding, finding_id)
    if finding is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return finding


@router.patch("/{finding_id}", response_model=FindingOut)
def update_finding(
    finding_id: str,
    payload: FindingUpdate,
    request: Request,
    actor: User = Depends(require_roles("admin", "analyst")),
    db: Session = Depends(get_db),
) -> Finding:
    finding = db.get(Finding, finding_id)
    if finding is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(finding, field, value)

    db.commit()
    db.refresh(finding)

    meta = get_request_meta(request)
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="findings.update",
        resource_type="finding",
        resource_id=finding.id,
        details={"status": finding.status, "severity": finding.severity},
        ip=meta["ip"],
        user_agent=meta["user_agent"],
    )
    publish_event_sync({"type": "finding.updated", "data": {"id": finding.id}})
    return finding


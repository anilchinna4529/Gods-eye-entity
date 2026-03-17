from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import write_audit_log
from app.db.models import Alert, User
from app.db.session import get_db
from app.realtime.redis_bus import publish_event_sync
from app.schemas.alert import AlertCreate, AlertOut, AlertUpdate
from app.security.deps import get_request_meta, require_roles


router = APIRouter()


@router.get("", response_model=list[AlertOut])
def list_alerts(
    status_filter: str | None = None,
    limit: int = 200,
    offset: int = 0,
    _: User = Depends(require_roles("admin", "analyst", "viewer")),
    db: Session = Depends(get_db),
) -> list[Alert]:
    stmt = select(Alert).order_by(Alert.updated_at.desc()).limit(limit).offset(offset)
    if status_filter:
        stmt = stmt.where(Alert.status == status_filter)
    return list(db.execute(stmt).scalars().all())


@router.post("", response_model=AlertOut, status_code=status.HTTP_201_CREATED)
def create_alert(
    payload: AlertCreate,
    request: Request,
    actor: User = Depends(require_roles("admin", "analyst")),
    db: Session = Depends(get_db),
) -> Alert:
    alert = Alert(kind=payload.kind, severity=payload.severity, title=payload.title, description=payload.description)
    db.add(alert)
    db.commit()
    db.refresh(alert)

    meta = get_request_meta(request)
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="alerts.create",
        resource_type="alert",
        resource_id=alert.id,
        details={"title": alert.title, "severity": alert.severity},
        ip=meta["ip"],
        user_agent=meta["user_agent"],
    )
    publish_event_sync({"type": "alert.created", "data": {"id": alert.id}})
    return alert


@router.get("/{alert_id}", response_model=AlertOut)
def get_alert(alert_id: str, _: User = Depends(require_roles("admin", "analyst", "viewer")), db: Session = Depends(get_db)) -> Alert:
    alert = db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return alert


@router.patch("/{alert_id}", response_model=AlertOut)
def update_alert(
    alert_id: str,
    payload: AlertUpdate,
    request: Request,
    actor: User = Depends(require_roles("admin", "analyst")),
    db: Session = Depends(get_db),
) -> Alert:
    alert = db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    if payload.status is not None:
        alert.status = payload.status
        if payload.status == "acked":
            alert.acked_by_user_id = actor.id
            alert.acked_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(alert)

    meta = get_request_meta(request)
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="alerts.update",
        resource_type="alert",
        resource_id=alert.id,
        details={"status": alert.status},
        ip=meta["ip"],
        user_agent=meta["user_agent"],
    )
    publish_event_sync({"type": "alert.updated", "data": {"id": alert.id, "status": alert.status}})
    return alert


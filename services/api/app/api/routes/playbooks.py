from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import write_audit_log
from app.db.models import Playbook, User
from app.db.session import get_db
from app.realtime.redis_bus import publish_event_sync
from app.schemas.playbook import PlaybookCreate, PlaybookOut, PlaybookUpdate
from app.security.deps import get_request_meta, require_roles


router = APIRouter()


@router.get("", response_model=list[PlaybookOut])
def list_playbooks(_: User = Depends(require_roles("admin", "analyst", "viewer")), db: Session = Depends(get_db)) -> list[Playbook]:
    return list(db.execute(select(Playbook).order_by(Playbook.updated_at.desc())).scalars().all())


@router.post("", response_model=PlaybookOut, status_code=status.HTTP_201_CREATED)
def create_playbook(
    payload: PlaybookCreate,
    request: Request,
    actor: User = Depends(require_roles("admin", "analyst")),
    db: Session = Depends(get_db),
) -> Playbook:
    existing = db.execute(select(Playbook).where(Playbook.name == payload.name)).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Playbook name exists")

    pb = Playbook(name=payload.name, description=payload.description, definition=payload.definition, enabled=payload.enabled)
    db.add(pb)
    db.commit()
    db.refresh(pb)

    meta = get_request_meta(request)
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="playbooks.create",
        resource_type="playbook",
        resource_id=pb.id,
        details={"name": pb.name},
        ip=meta["ip"],
        user_agent=meta["user_agent"],
    )
    publish_event_sync({"type": "playbook.created", "data": {"id": pb.id, "name": pb.name}})
    return pb


@router.get("/{playbook_id}", response_model=PlaybookOut)
def get_playbook(playbook_id: str, _: User = Depends(require_roles("admin", "analyst", "viewer")), db: Session = Depends(get_db)) -> Playbook:
    pb = db.get(Playbook, playbook_id)
    if pb is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return pb


@router.patch("/{playbook_id}", response_model=PlaybookOut)
def update_playbook(
    playbook_id: str,
    payload: PlaybookUpdate,
    request: Request,
    actor: User = Depends(require_roles("admin", "analyst")),
    db: Session = Depends(get_db),
) -> Playbook:
    pb = db.get(Playbook, playbook_id)
    if pb is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(pb, field, value)

    db.commit()
    db.refresh(pb)

    meta = get_request_meta(request)
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="playbooks.update",
        resource_type="playbook",
        resource_id=pb.id,
        details={"enabled": pb.enabled},
        ip=meta["ip"],
        user_agent=meta["user_agent"],
    )
    publish_event_sync({"type": "playbook.updated", "data": {"id": pb.id}})
    return pb


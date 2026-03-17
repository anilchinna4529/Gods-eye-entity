from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.audit import write_audit_log
from app.db.models import Asset, Relationship, User
from app.db.session import get_db
from app.realtime.redis_bus import publish_event_sync
from app.schemas.asset import AssetCreate, AssetOut, AssetUpdate, RelationshipCreate, RelationshipOut
from app.security.deps import get_request_meta, require_roles


router = APIRouter()
relationships_router = APIRouter()


@router.get("", response_model=list[AssetOut])
def list_assets(
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
    _: User = Depends(require_roles("admin", "analyst", "viewer")),
    db: Session = Depends(get_db),
) -> list[Asset]:
    stmt = select(Asset).order_by(Asset.updated_at.desc()).limit(limit).offset(offset)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Asset.hostname.ilike(like), Asset.ip.ilike(like)))
    return list(db.execute(stmt).scalars().all())


@router.post("", response_model=AssetOut, status_code=status.HTTP_201_CREATED)
def create_asset(
    payload: AssetCreate,
    request: Request,
    actor: User = Depends(require_roles("admin", "analyst")),
    db: Session = Depends(get_db),
) -> Asset:
    asset = Asset(
        hostname=payload.hostname,
        ip=payload.ip,
        owner=payload.owner,
        tags=payload.tags,
        meta=payload.meta,
        last_seen=datetime.now(timezone.utc),
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    meta = get_request_meta(request)
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="assets.create",
        resource_type="asset",
        resource_id=asset.id,
        details={"hostname": asset.hostname, "ip": asset.ip},
        ip=meta["ip"],
        user_agent=meta["user_agent"],
    )

    publish_event_sync({"type": "asset.created", "data": {"id": asset.id, "hostname": asset.hostname, "ip": asset.ip}})
    return asset


@router.get("/{asset_id}", response_model=AssetOut)
def get_asset(asset_id: str, _: User = Depends(require_roles("admin", "analyst", "viewer")), db: Session = Depends(get_db)) -> Asset:
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return asset


@router.patch("/{asset_id}", response_model=AssetOut)
def update_asset(
    asset_id: str,
    payload: AssetUpdate,
    request: Request,
    actor: User = Depends(require_roles("admin", "analyst")),
    db: Session = Depends(get_db),
) -> Asset:
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(asset, field, value)

    db.commit()
    db.refresh(asset)

    meta = get_request_meta(request)
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="assets.update",
        resource_type="asset",
        resource_id=asset.id,
        details={"hostname": asset.hostname, "ip": asset.ip},
        ip=meta["ip"],
        user_agent=meta["user_agent"],
    )
    publish_event_sync({"type": "asset.updated", "data": {"id": asset.id}})
    return asset


@relationships_router.get("", response_model=list[RelationshipOut])
def list_relationships(_: User = Depends(require_roles("admin", "analyst", "viewer")), db: Session = Depends(get_db)) -> list[Relationship]:
    return list(db.execute(select(Relationship).order_by(Relationship.created_at.desc())).scalars().all())


@relationships_router.post("", response_model=RelationshipOut, status_code=status.HTTP_201_CREATED)
def create_relationship(
    payload: RelationshipCreate,
    request: Request,
    actor: User = Depends(require_roles("admin", "analyst")),
    db: Session = Depends(get_db),
) -> Relationship:
    if db.get(Asset, payload.from_asset_id) is None or db.get(Asset, payload.to_asset_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown asset id")

    rel = Relationship(
        from_asset_id=payload.from_asset_id,
        to_asset_id=payload.to_asset_id,
        kind=payload.kind,
        meta=payload.meta,
    )
    db.add(rel)
    db.commit()
    db.refresh(rel)

    meta = get_request_meta(request)
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="relationships.create",
        resource_type="relationship",
        resource_id=rel.id,
        details={"from": rel.from_asset_id, "to": rel.to_asset_id, "kind": rel.kind},
        ip=meta["ip"],
        user_agent=meta["user_agent"],
    )
    publish_event_sync({"type": "relationship.created", "data": {"id": rel.id}})
    return rel

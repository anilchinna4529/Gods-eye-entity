from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import write_audit_log
from app.db.models import User
from app.db.session import get_db
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.security.deps import get_request_meta, require_roles
from app.security.passwords import hash_password


router = APIRouter()


@router.get("", response_model=list[UserOut])
def list_users(_: User = Depends(require_roles("admin")), db: Session = Depends(get_db)) -> list[User]:
    return list(db.execute(select(User).order_by(User.created_at.desc())).scalars().all())


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    request: Request,
    actor: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> User:
    email = payload.email.strip().lower()
    existing = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    user = User(email=email, password_hash=hash_password(payload.password), role=payload.role, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)

    meta = get_request_meta(request)
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="users.create",
        resource_type="user",
        resource_id=user.id,
        details={"email": user.email, "role": user.role},
        ip=meta["ip"],
        user_agent=meta["user_agent"],
    )
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: str,
    payload: UserUpdate,
    request: Request,
    actor: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active

    db.commit()
    db.refresh(user)

    meta = get_request_meta(request)
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="users.update",
        resource_type="user",
        resource_id=user.id,
        details={"role": user.role, "is_active": user.is_active},
        ip=meta["ip"],
        user_agent=meta["user_agent"],
    )
    return user


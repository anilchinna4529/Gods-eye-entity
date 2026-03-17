from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import write_audit_log
from app.core.config import settings
from app.db.models import User
from app.db.session import get_db
from app.schemas.user import LoginRequest, UserOut
from app.security.deps import get_current_user, get_request_meta
from app.security.jwt import create_token
from app.security.passwords import verify_password


router = APIRouter()


@router.post("/login", response_model=UserOut)
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> User:
    email = payload.email.strip().lower()
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_token(user.id, role=user.role)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.session_cookie_secure,
        max_age=settings.jwt_exp_minutes * 60,
    )

    meta = get_request_meta(request)
    write_audit_log(
        db,
        actor_user_id=user.id,
        action="auth.login",
        details={"email": user.email},
        ip=meta["ip"],
        user_agent=meta["user_agent"],
    )
    return user


@router.post("/logout")
def logout(request: Request, response: Response, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    response.delete_cookie(key=settings.session_cookie_name)
    meta = get_request_meta(request)
    write_audit_log(
        db,
        actor_user_id=user.id,
        action="auth.logout",
        ip=meta["ip"],
        user_agent=meta["user_agent"],
    )
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user


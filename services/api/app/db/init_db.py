from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import User
from app.security.passwords import hash_password


def ensure_bootstrap_admin(db: Session) -> None:
    existing = db.execute(select(User).limit(1)).scalar_one_or_none()
    if existing is not None:
        return

    email = settings.bootstrap_admin_email.strip().lower()
    password = settings.bootstrap_admin_password
    admin = User(email=email, password_hash=hash_password(password), role="admin", is_active=True)
    db.add(admin)
    db.commit()


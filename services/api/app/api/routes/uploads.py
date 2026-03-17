from __future__ import annotations

import hashlib
import os
import uuid

from fastapi import APIRouter, Depends, File, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.audit import write_audit_log
from app.core.config import settings
from app.db.models import Upload, User
from app.db.session import get_db
from app.schemas.upload import UploadOut
from app.security.deps import get_request_meta, require_roles


router = APIRouter()


@router.post("", response_model=UploadOut, status_code=status.HTTP_201_CREATED)
def upload_file(
    request: Request,
    file: UploadFile = File(...),
    actor: User = Depends(require_roles("admin", "analyst")),
    db: Session = Depends(get_db),
) -> Upload:
    os.makedirs(settings.data_dir, exist_ok=True)
    safe_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename or "")[1]
    stored_name = f"{safe_id}{ext}"
    stored_path = os.path.join(settings.data_dir, stored_name)

    sha256 = hashlib.sha256()
    size = 0
    with open(stored_path, "wb") as f:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            sha256.update(chunk)
            f.write(chunk)

    upload = Upload(
        filename=file.filename or stored_name,
        content_type=file.content_type,
        path=stored_path,
        sha256=sha256.hexdigest(),
        size_bytes=size,
        uploaded_by_user_id=actor.id,
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)

    meta = get_request_meta(request)
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="uploads.create",
        resource_type="upload",
        resource_id=upload.id,
        details={"filename": upload.filename, "sha256": upload.sha256, "size_bytes": upload.size_bytes},
        ip=meta["ip"],
        user_agent=meta["user_agent"],
    )
    return upload


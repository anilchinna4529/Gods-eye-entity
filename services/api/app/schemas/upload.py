from __future__ import annotations

from datetime import datetime

from app.schemas.common import APIModel


class UploadOut(APIModel):
    id: str
    filename: str
    content_type: str | None
    sha256: str
    size_bytes: int
    created_at: datetime


from __future__ import annotations

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.api.router import api_router
from app.core.config import settings
from app.db.init_db import ensure_bootstrap_admin
from app.db.models import User
from app.db.session import SessionLocal
from app.realtime.manager import manager
from app.realtime.redis_subscriber import subscriber
from app.security.jwt import decode_token


app = FastAPI(title="Gods-eye API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.on_event("startup")
async def on_startup() -> None:
    db = SessionLocal()
    try:
        ensure_bootstrap_admin(db)
    finally:
        db.close()

    if settings.environment != "test":
        await subscriber.start()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    if settings.environment != "test":
        await subscriber.stop()


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True}


def _ws_is_authenticated(ws: WebSocket) -> bool:
    token = ws.cookies.get(settings.session_cookie_name)
    if not token:
        return False
    try:
        payload = decode_token(token)
    except Exception:  # noqa: BLE001
        return False
    user_id = payload.get("sub")
    if not user_id:
        return False

    db = SessionLocal()
    try:
        user = db.execute(select(User).where(User.id == user_id, User.is_active.is_(True))).scalar_one_or_none()
        return user is not None
    finally:
        db.close()


@app.websocket("/ws/events")
async def ws_events(ws: WebSocket) -> None:
    if not _ws_is_authenticated(ws):
        await ws.close(code=4401)
        return

    await manager.connect(ws)
    try:
        while True:
            # Consume incoming messages (client pings, etc.)
            await ws.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(ws)

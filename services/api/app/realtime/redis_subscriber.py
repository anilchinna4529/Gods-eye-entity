from __future__ import annotations

import asyncio
import json
from typing import Any

import redis.asyncio as redis_async

from app.core.config import settings
from app.realtime.manager import manager


class RedisSubscriber:
    def __init__(self) -> None:
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task is None:
            return
        try:
            await self._task
        finally:
            self._task = None

    async def _run(self) -> None:
        client = redis_async.Redis.from_url(settings.redis_url, decode_responses=True)
        pubsub = client.pubsub()
        await pubsub.subscribe(settings.events_channel)
        try:
            while not self._stop_event.is_set():
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message.get("type") == "message":
                    raw = message.get("data")
                    try:
                        event: dict[str, Any] = json.loads(raw) if isinstance(raw, str) else {"raw": raw}
                    except Exception:  # noqa: BLE001
                        event = {"type": "event.raw", "data": {"raw": raw}}
                    await manager.broadcast(event)
                await asyncio.sleep(0.05)
        finally:
            try:
                await pubsub.unsubscribe(settings.events_channel)
                await pubsub.close()
                await client.close()
            except Exception:  # noqa: BLE001
                pass


subscriber = RedisSubscriber()


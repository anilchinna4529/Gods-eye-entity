from __future__ import annotations

import json
from typing import Any

import redis

from app.core.config import settings


def publish_event_sync(event: dict[str, Any]) -> None:
    client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        client.publish(settings.events_channel, json.dumps(event))
    except Exception:  # noqa: BLE001
        # Best-effort: never fail the API request due to event fanout issues.
        return
    finally:
        try:
            client.close()
        except Exception:  # noqa: BLE001
            pass

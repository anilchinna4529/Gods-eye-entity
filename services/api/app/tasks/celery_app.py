from __future__ import annotations

from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "godseye",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.tasks"],
)
celery_app.conf.update(task_track_started=True)

celery_app.conf.beat_schedule = {
    "correlate-alerts-every-5m": {
        "task": "app.tasks.tasks.correlate_alerts_task",
        "schedule": 300.0,
    }
}


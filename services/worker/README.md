# Worker Service

The v1 worker and scheduler run the same backend codebase as `services/api` but execute different entrypoints:

- Worker: `celery -A app.tasks.celery_app worker`
- Scheduler: `celery -A app.tasks.celery_app beat`

This keeps the task allowlist, DB models, and event publishing consistent with the API.


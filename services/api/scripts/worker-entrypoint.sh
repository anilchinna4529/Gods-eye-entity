#!/usr/bin/env bash
set -euo pipefail

cd /app

echo "[worker] Starting celery worker..."
exec celery -A app.tasks.celery_app worker --loglevel=info

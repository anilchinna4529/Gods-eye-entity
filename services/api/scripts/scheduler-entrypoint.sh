#!/usr/bin/env bash
set -euo pipefail

cd /app

echo "[scheduler] Starting celery beat..."
exec celery -A app.tasks.celery_app beat --loglevel=info


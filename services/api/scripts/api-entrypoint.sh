#!/usr/bin/env bash
set -euo pipefail

cd /app

echo "[api] Running migrations..."
alembic upgrade head

echo "[api] Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000


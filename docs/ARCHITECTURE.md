# Architecture (Gods-eye-entity v1)

## Services

- `apps/web` (Next.js + Tailwind): Analyst dashboard UI.
- `services/api` (FastAPI): Core API, auth/RBAC, CRUD, WebSocket events.
- `services/worker` (Celery): Executes allowlisted defensive automations and scheduled jobs.
- `db` (Postgres): System of record for users, assets, findings, alerts, playbooks, executions, audit logs.
- `redis` (Redis): Task queue broker + event pub/sub for realtime updates.

## Data Flow

1. Analyst uses the web UI to create assets, acknowledge alerts, manage playbooks, and launch executions.
2. Web UI calls FastAPI endpoints; FastAPI enforces auth/RBAC and writes to Postgres.
3. When an execution is launched, FastAPI enqueues a Celery task via Redis.
4. Worker runs the allowlisted action(s), writes results to Postgres, and publishes realtime events to Redis pub/sub.
5. FastAPI subscribes to Redis pub/sub and pushes events to connected WebSocket clients.

## Trust Boundaries

- Browser <-> API: authenticated via httpOnly session cookie; CORS restricted.
- API/Worker <-> DB: private network; DB credentials from env.
- API/Worker <-> Redis: private network; used for queue and pub/sub.
- Worker actions: allowlisted operations only (no arbitrary shell execution).

## Event Types (WebSocket)

Events are JSON objects with `type` and `data`, e.g.:

- `execution.updated`
- `alert.created`, `alert.updated`
- `finding.created`, `finding.updated`
- `asset.created`, `asset.updated`


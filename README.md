# Gods-eye-entity (Defensive SOC Command Center)

Local-first Security Operations Command Center for **authorized defensive monitoring and automation**.

See `docs/SCOPE.md` for explicit scope boundaries and exclusions.

## Quickstart (Docker Compose)

1. Create `.env` from the template:

```powershell
Copy-Item .\infra\env.example .\.env
```

2. Start services:

```powershell
docker compose up --build
```

3. Open:

- Web UI: `http://localhost:3000`
- API: `http://localhost:8000`

The first run bootstraps an admin user using `BOOTSTRAP_ADMIN_EMAIL` and `BOOTSTRAP_ADMIN_PASSWORD` from `.env`.

## Optional: Observability Profile

Bring up Prometheus + Grafana stubs:

```powershell
docker compose --profile observability up --build
```

## Optional: SIEM/Search Profile

Bring up OpenSearch + OpenSearch Dashboards stubs:

```powershell
docker compose --profile siem up --build
```

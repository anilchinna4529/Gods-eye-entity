from fastapi import APIRouter

from app.api.routes import alerts, assets, auth, executions, findings, playbooks, uploads, users


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
api_router.include_router(assets.relationships_router, prefix="/relationships", tags=["relationships"])
api_router.include_router(findings.router, prefix="/findings", tags=["findings"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(playbooks.router, prefix="/playbooks", tags=["playbooks"])
api_router.include_router(executions.router, prefix="/executions", tags=["executions"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])


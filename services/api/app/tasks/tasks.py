from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from app.db.models import Execution, Playbook
from app.db.session import SessionLocal
from app.realtime.redis_bus import publish_event_sync
from app.tasks.actions import ActionError, run_allowlisted_action
from app.tasks.celery_app import celery_app


def _publish_execution(execution_id: str, status: str) -> None:
    publish_event_sync({"type": "execution.updated", "data": {"id": execution_id, "status": status}})


@celery_app.task(name="app.tasks.tasks.run_execution")
def run_execution(execution_id: str) -> dict[str, Any]:
    db = SessionLocal()
    try:
        execution = db.get(Execution, execution_id)
        if execution is None:
            return {"ok": False, "error": "not_found"}

        if execution.status not in {"queued", "running"}:
            return {"ok": False, "error": f"invalid_status:{execution.status}"}

        execution.status = "running"
        execution.started_at = datetime.now(timezone.utc)
        db.commit()
        _publish_execution(execution.id, execution.status)

        try:
            result: dict[str, Any] = {}
            if execution.execution_type == "action":
                if not execution.action:
                    raise ActionError("Missing action")
                result = run_allowlisted_action(db, execution.action, execution.params or {})
            else:
                if not execution.playbook_id:
                    raise ActionError("Missing playbook_id")
                pb = db.execute(select(Playbook).where(Playbook.id == execution.playbook_id)).scalar_one_or_none()
                if pb is None:
                    raise ActionError("Playbook not found")
                definition = pb.definition or {}
                steps = definition.get("steps") or []
                if not isinstance(steps, list):
                    raise ActionError("Invalid playbook definition")
                step_results: list[dict[str, Any]] = []
                for step in steps:
                    if not isinstance(step, dict):
                        continue
                    action = step.get("action")
                    params = step.get("params") or {}
                    if not isinstance(params, dict):
                        params = {}
                    merged = {**(execution.params or {}), **params}
                    step_results.append(
                        {
                            "action": action,
                            "result": run_allowlisted_action(db, str(action), merged),
                        }
                    )
                result = {"steps": step_results}

            execution.result = result
            execution.status = "succeeded"
            execution.finished_at = datetime.now(timezone.utc)
            db.commit()
            _publish_execution(execution.id, execution.status)
            return {"ok": True, "result": result}
        except Exception as exc:  # noqa: BLE001
            execution.status = "failed"
            execution.finished_at = datetime.now(timezone.utc)
            execution.log = (execution.log or "") + f"\n[error] {type(exc).__name__}: {exc}\n"
            db.commit()
            _publish_execution(execution.id, execution.status)
            return {"ok": False, "error": str(exc)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.tasks.correlate_alerts_task")
def correlate_alerts_task() -> dict[str, Any]:
    db = SessionLocal()
    try:
        result = run_allowlisted_action(db, "CORRELATE_ALERTS", {"threshold": 3})
        if result.get("alerts_created"):
            publish_event_sync({"type": "alert.correlation", "data": result})
        return {"ok": True, "result": result}
    finally:
        db.close()


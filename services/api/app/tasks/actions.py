from __future__ import annotations

import csv
import json
import os
import re
from collections.abc import Iterable
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Alert, Asset, Finding, ThreatIndicator, Upload


class ActionError(RuntimeError):
    pass


def _read_upload(db: Session, upload_id: str) -> Upload:
    upload = db.get(Upload, upload_id)
    if upload is None:
        raise ActionError("Unknown upload_id")
    if not os.path.exists(upload.path):
        raise ActionError("Uploaded file not found on disk")
    return upload


def _parse_assets_from_json(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, dict) and "assets" in data:
        data = data["assets"]
    if not isinstance(data, list):
        raise ActionError("Invalid JSON payload: expected list of assets")
    assets: list[dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        hostname = str(item.get("hostname") or "").strip()
        ip = str(item.get("ip") or "").strip() or None
        if not hostname:
            continue
        assets.append(
            {
                "hostname": hostname,
                "ip": ip,
                "owner": item.get("owner"),
                "tags": item.get("tags") or [],
                "metadata": item.get("metadata") or {},
            }
        )
    return assets


def _parse_assets_from_csv(path: str) -> list[dict[str, Any]]:
    assets: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            hostname = (row.get("hostname") or "").strip()
            ip = (row.get("ip") or "").strip() or None
            if not hostname:
                continue
            tags = [t.strip() for t in (row.get("tags") or "").split(",") if t.strip()]
            assets.append(
                {
                    "hostname": hostname,
                    "ip": ip,
                    "owner": row.get("owner") or None,
                    "tags": tags,
                    "metadata": {},
                }
            )
    return assets


def action_import_assets(db: Session, params: dict[str, Any]) -> dict[str, Any]:
    assets_in: list[dict[str, Any]] = []

    if "upload_id" in params:
        upload = _read_upload(db, str(params["upload_id"]))
        if upload.path.lower().endswith(".csv"):
            assets_in = _parse_assets_from_csv(upload.path)
        else:
            with open(upload.path, "r", encoding="utf-8") as f:
                assets_in = _parse_assets_from_json(json.load(f))
    else:
        assets_in = _parse_assets_from_json(params.get("assets", []))

    created = 0
    updated = 0
    for item in assets_in:
        hostname = item["hostname"]
        ip = item.get("ip")

        existing = None
        if ip:
            existing = db.execute(select(Asset).where(Asset.ip == ip)).scalar_one_or_none()
        if existing is None:
            existing = db.execute(select(Asset).where(Asset.hostname == hostname)).scalar_one_or_none()

        if existing is None:
            db.add(
                Asset(
                    hostname=hostname,
                    ip=ip,
                    owner=item.get("owner"),
                    tags=item.get("tags") or [],
                    meta=item.get("metadata") or {},
                )
            )
            created += 1
        else:
            existing.owner = item.get("owner") or existing.owner
            existing.tags = sorted(set((existing.tags or []) + (item.get("tags") or [])))
            existing.meta = {**(existing.meta or {}), **(item.get("metadata") or {})}
            if ip and not existing.ip:
                existing.ip = ip
            updated += 1

    db.commit()
    return {"created": created, "updated": updated, "total": len(assets_in)}


IOC_IP = re.compile(r"^(?:\\d{1,3}\\.){3}\\d{1,3}$")
IOC_HASH = re.compile(r"^[a-fA-F0-9]{32,64}$")
IOC_DOMAIN = re.compile(r"^(?=.{1,253}$)(?:[a-zA-Z0-9-]{1,63}\\.)+[a-zA-Z]{2,63}$")


def _iter_iocs(lines: Iterable[str]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for raw in lines:
        v = raw.strip()
        if not v:
            continue
        if IOC_IP.match(v):
            out.append(("ip", v))
        elif IOC_DOMAIN.match(v):
            out.append(("domain", v.lower()))
        elif IOC_HASH.match(v):
            out.append(("hash", v.lower()))
        else:
            out.append(("other", v))
    return out


def action_ingest_intel(db: Session, params: dict[str, Any]) -> dict[str, Any]:
    if "upload_id" not in params:
        raise ActionError("upload_id required")
    upload = _read_upload(db, str(params["upload_id"]))
    source = str(params.get("source") or upload.filename)

    indicators: list[tuple[str, str]] = []
    if upload.path.lower().endswith(".json"):
        with open(upload.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "indicators" in data:
            data = data["indicators"]
        if isinstance(data, list):
            indicators = _iter_iocs(str(x) for x in data)
        else:
            raise ActionError("Invalid JSON intel format")
    else:
        with open(upload.path, "r", encoding="utf-8") as f:
            indicators = _iter_iocs(f.readlines())

    inserted = 0
    for indicator_type, value in indicators:
        existing = db.execute(
            select(ThreatIndicator).where(
                ThreatIndicator.indicator_type == indicator_type,
                ThreatIndicator.value == value,
            )
        ).scalar_one_or_none()
        if existing is not None:
            continue
        db.add(
            ThreatIndicator(
                indicator_type=indicator_type,
                value=value,
                source=source,
                confidence=50,
                meta={},
            )
        )
        inserted += 1

    db.commit()
    return {"inserted": inserted, "total": len(indicators)}


SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("aws_access_key_id", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private_key", re.compile(r"BEGIN (?:RSA|OPENSSH|EC) PRIVATE KEY")),
    ("generic_password_assignment", re.compile(r"(?i)password\\s*[:=]\\s*[^\\s]{6,}")),
    ("bearer_token", re.compile(r"(?i)authorization\\s*:\\s*bearer\\s+[A-Za-z0-9\\-\\._~\\+\\/]+=*")),
]


def action_config_scan(db: Session, params: dict[str, Any]) -> dict[str, Any]:
    if "upload_id" not in params:
        raise ActionError("upload_id required")
    upload = _read_upload(db, str(params["upload_id"]))
    asset_id = params.get("asset_id")
    source = str(params.get("source") or "config_scan")

    with open(upload.path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    hits: list[dict[str, Any]] = []
    for name, pattern in SECRET_PATTERNS:
        if pattern.search(content):
            hits.append({"rule": name})

    created = 0
    for hit in hits:
        title = f"Potential secret detected ({hit['rule']})"
        db.add(
            Finding(
                asset_id=asset_id,
                title=title,
                description=(
                    "File scan detected a pattern that may indicate a secret or sensitive token. "
                    "Review and rotate credentials if needed."
                ),
                severity="high",
                status="open",
                source=source,
                evidence={"upload_id": upload.id, "sha256": upload.sha256, "rule": hit["rule"]},
            )
        )
        created += 1

    db.commit()
    return {"findings_created": created, "rules_triggered": hits}


def action_correlate_alerts(db: Session, params: dict[str, Any]) -> dict[str, Any]:
    threshold = int(params.get("threshold") or 3)
    stmt = select(Finding).where(Finding.status == "open", Finding.severity.in_(["high", "critical"]))
    findings = list(db.execute(stmt).scalars().all())

    by_asset: dict[str, int] = {}
    for finding in findings:
        if not finding.asset_id:
            continue
        by_asset[finding.asset_id] = by_asset.get(finding.asset_id, 0) + 1

    created = 0
    for asset_id, count in by_asset.items():
        if count < threshold:
            continue
        title = f"High severity findings threshold exceeded ({count})"
        existing = db.execute(
            select(Alert).where(Alert.kind == "correlation", Alert.title == title, Alert.status == "open")
        ).scalar_one_or_none()
        if existing is not None:
            continue
        db.add(
            Alert(
                kind="correlation",
                severity="medium",
                title=title,
                description=f"Asset {asset_id} has {count} open high/critical findings. Triage and remediate.",
                status="open",
            )
        )
        created += 1

    db.commit()
    return {"alerts_created": created}


ALLOWLIST = {
    "IMPORT_ASSETS": action_import_assets,
    "INGEST_INTEL": action_ingest_intel,
    "CONFIG_SCAN": action_config_scan,
    "CORRELATE_ALERTS": action_correlate_alerts,
}


def run_allowlisted_action(db: Session, action: str, params: dict[str, Any]) -> dict[str, Any]:
    action_key = (action or "").strip().upper()
    if action_key not in ALLOWLIST:
        raise ActionError("Action not allowed")
    return ALLOWLIST[action_key](db, params)

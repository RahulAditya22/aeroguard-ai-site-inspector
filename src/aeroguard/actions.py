"""Deterministic response routing and incident persistence."""

import csv
import json
from pathlib import Path

import requests

from .config import Settings
from .models import IncidentRecord, InspectionResult, Severity

SEVERITY_RANK = {
    Severity.NONE: 0,
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}

CSV_FIELDS = [
    "timestamp_utc",
    "image_name",
    "threat_detected",
    "threat_type",
    "severity",
    "confidence",
    "description",
    "recommended_action",
    "observations",
    "uncertainties",
    "automated_action",
]


def route_action(result: InspectionResult, minimum_alert_severity: str = "high") -> str:
    threshold = Severity(minimum_alert_severity.lower())
    if not result.threat_detected or result.severity == Severity.NONE:
        return "no_alert"
    if SEVERITY_RANK[result.severity] >= SEVERITY_RANK[threshold]:
        return "alert_and_log"
    return "log_for_review"


def append_incident_csv(path: str | Path, record: IncidentRecord) -> None:
    csv_path = Path(path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    exists = csv_path.exists() and csv_path.stat().st_size > 0
    row = record.model_dump(mode="json")
    row["observations"] = json.dumps(row["observations"], ensure_ascii=False)
    row["uncertainties"] = json.dumps(row["uncertainties"], ensure_ascii=False)
    with csv_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def write_incident_json(path: str | Path, record: IncidentRecord) -> None:
    json_path = Path(path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(record.model_dump_json(indent=2), encoding="utf-8")


def send_webhook(settings: Settings, record: IncidentRecord) -> bool:
    """Send a compact alert. Returns False when webhook alerts are disabled."""
    if not settings.alert_webhook_url:
        return False

    payload = {
        "source": "AeroGuard AI",
        "event": "aerial_site_incident",
        "severity": record.severity.value,
        "threat_type": record.threat_type.value,
        "image_name": record.image_name,
        "confidence": record.confidence,
        "description": record.description,
        "recommended_action": record.recommended_action,
    }
    response = requests.post(
        settings.alert_webhook_url,
        json=payload,
        timeout=settings.request_timeout_seconds,
    )
    response.raise_for_status()
    return True

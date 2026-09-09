import csv

from aeroguard.actions import append_incident_csv, route_action, send_webhook
from aeroguard.config import Settings
from aeroguard.models import IncidentRecord, InspectionResult, Severity, ThreatType


def result(severity: Severity, detected: bool = True) -> InspectionResult:
    return InspectionResult(
        threat_detected=detected,
        threat_type=ThreatType.OTHER_HAZARD if detected else ThreatType.NONE,
        severity=severity,
        confidence=0.9,
        description="Test condition.",
        recommended_action="Review the image.",
    )


def test_action_routing():
    assert route_action(result(Severity.NONE, False)) == "no_alert"
    assert route_action(result(Severity.MEDIUM)) == "log_for_review"
    assert route_action(result(Severity.HIGH)) == "alert_and_log"
    assert route_action(result(Severity.CRITICAL)) == "alert_and_log"


def test_csv_logging(tmp_path):
    record = IncidentRecord.from_inspection("site.jpg", result(Severity.HIGH), "alert_and_log")
    path = tmp_path / "incidents.csv"
    append_incident_csv(path, record)
    append_incident_csv(path, record)

    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    assert rows[0]["severity"] == "high"


def test_webhook_disabled_returns_false(tmp_path):
    settings = Settings(
        gemini_api_key="",
        alert_webhook_url="",
        data_dir=tmp_path / "data",
        report_dir=tmp_path / "reports",
    )
    record = IncidentRecord.from_inspection("site.jpg", result(Severity.HIGH), "alert_and_log")
    assert send_webhook(settings, record) is False

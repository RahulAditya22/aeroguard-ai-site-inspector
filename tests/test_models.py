from aeroguard.models import InspectionResult, Severity, ThreatType


def test_valid_inspection_result():
    result = InspectionResult(
        threat_detected=True,
        threat_type=ThreatType.FIRE_OR_SMOKE,
        severity=Severity.HIGH,
        confidence=0.88,
        description="Visible smoke near a structure.",
        recommended_action="Alert site personnel and inspect immediately.",
        observations=["smoke", "structure"],
        uncertainties=[],
    )
    assert result.confidence == 0.88


def test_confidence_is_bounded():
    data = {
        "threat_detected": False,
        "threat_type": "none",
        "severity": "none",
        "confidence": 1.2,
        "description": "No clear threat visible.",
        "recommended_action": "No action required.",
    }
    try:
        InspectionResult.model_validate(data)
    except Exception:
        return
    raise AssertionError("Out-of-range confidence should be rejected")


def test_threat_fields_must_be_consistent():
    data = {
        "threat_detected": False,
        "threat_type": "fire_or_smoke",
        "severity": "none",
        "confidence": 0.9,
        "description": "No threat.",
        "recommended_action": "No action required.",
    }
    try:
        InspectionResult.model_validate(data)
    except Exception:
        return
    raise AssertionError("Threat fields should be consistent")

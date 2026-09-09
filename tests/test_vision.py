from types import SimpleNamespace

import pytest

from aeroguard.config import Settings
from aeroguard.models import InspectionResult, Severity, ThreatType
from aeroguard.vision import GeminiVisionClient


class FakeGenerateContent:
    def __init__(self, failures=0):
        self.failures = failures
        self.calls = 0

    def __call__(self, **kwargs):
        self.calls += 1
        if self.calls <= self.failures:
            raise RuntimeError("503 UNAVAILABLE: temporary overload")
        return SimpleNamespace(
            parsed=InspectionResult(
                threat_detected=True,
                threat_type=ThreatType.FIRE_OR_SMOKE,
                severity=Severity.CRITICAL,
                confidence=0.99,
                description="Visible fire.",
                recommended_action="Alert emergency responders.",
                observations=["flames"],
                uncertainties=[],
            )
        )


def make_client():
    client = object.__new__(GeminiVisionClient)
    client.settings = Settings(gemini_api_key="test-key")
    client.client = SimpleNamespace(models=SimpleNamespace())
    return client


def test_transient_error_retries_and_succeeds(monkeypatch):
    client = make_client()
    fake_call = FakeGenerateContent(failures=2)
    client.client.models.generate_content = fake_call
    delays = []
    monkeypatch.setattr("aeroguard.vision.time.sleep", delays.append)

    response = client._generate_content_with_retry(contents=[], config=None)

    assert response.parsed.threat_type == ThreatType.FIRE_OR_SMOKE
    assert fake_call.calls == 3
    assert delays == [1.0, 2.0]


def test_transient_error_fails_after_max_retries(monkeypatch):
    client = make_client()
    fake_call = FakeGenerateContent(failures=10)
    client.client.models.generate_content = fake_call
    monkeypatch.setattr("aeroguard.vision.time.sleep", lambda _: None)

    with pytest.raises(RuntimeError, match="503 UNAVAILABLE"):
        client._generate_content_with_retry(contents=[], config=None)

    assert fake_call.calls == 4

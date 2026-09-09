from io import BytesIO

from PIL import Image

from aeroguard.models import IncidentRecord, Severity, ThreatType
from aeroguard.web import create_app


def make_image_bytes() -> bytes:
    image = Image.new("RGB", (16, 16), "white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


class FakePipeline:
    def __init__(self, record):
        self.record = record
        self.seen_path = None

    def inspect_one(self, image_path):
        self.seen_path = image_path
        return self.record


def make_settings(tmp_path):
    from aeroguard.config import Settings

    return Settings(
        gemini_api_key="test-key",
        data_dir=tmp_path / "data",
        report_dir=tmp_path / "reports",
        max_image_mb=1,
    )


def test_health_endpoint(tmp_path):
    app = create_app(make_settings(tmp_path), FakePipeline(None))
    response = app.test_client().get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_upload_inspects_image_without_exposing_provider_credentials(tmp_path):
    record = IncidentRecord(
        image_name="site.png",
        threat_detected=True,
        threat_type=ThreatType.FIRE_OR_SMOKE,
        severity=Severity.CRITICAL,
        confidence=0.99,
        description="Active fire detected.",
        recommended_action="Evacuate and alert emergency services.",
        observations=["Visible flames"],
        uncertainties=[],
        automated_action="alert_and_log",
    )
    pipeline = FakePipeline(record)
    app = create_app(make_settings(tmp_path), pipeline)

    response = app.test_client().post(
        "/api/inspect",
        data={"image": (BytesIO(make_image_bytes()), "site.png")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["threat_type"] == "fire_or_smoke"
    assert payload["severity"] == "critical"
    assert "api_key" not in response.get_data(as_text=True).lower()
    assert pipeline.seen_path is not None
    assert not pipeline.seen_path.exists()


def test_rejects_unsupported_file(tmp_path):
    app = create_app(make_settings(tmp_path), FakePipeline(None))
    response = app.test_client().post(
        "/api/inspect",
        data={"image": (BytesIO(b"not an image"), "notes.txt")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert "Unsupported image type" in response.get_json()["error"]


def test_missing_image_is_rejected(tmp_path):
    app = create_app(make_settings(tmp_path), FakePipeline(None))
    response = app.test_client().post("/api/inspect")
    assert response.status_code == 400
    assert "select an image" in response.get_json()["error"]

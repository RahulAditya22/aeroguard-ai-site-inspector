from pathlib import Path

from PIL import Image

from aeroguard.config import Settings
from aeroguard.models import InspectionResult, Severity, ThreatType
from aeroguard.pipeline import InspectionPipeline


class FakeVisionClient:
    def inspect(self, image_path: Path, mime_type: str) -> InspectionResult:
        assert image_path.exists()
        assert mime_type == "image/jpeg"
        return InspectionResult(
            threat_detected=True,
            threat_type=ThreatType.PERSON_IN_RESTRICTED_ZONE,
            severity=Severity.HIGH,
            confidence=0.92,
            description="Person appears inside a visibly marked restricted area.",
            recommended_action="Alert site security and review the image.",
            observations=["person", "restricted boundary"],
            uncertainties=["Exact intent cannot be determined from the image."],
        )


def test_pipeline_without_api_call(tmp_path):
    image_path = tmp_path / "site.jpg"
    Image.new("RGB", (160, 120), "white").save(image_path, format="JPEG")

    settings = Settings(
        gemini_api_key="",
        data_dir=tmp_path / "data",
        report_dir=tmp_path / "reports",
    )
    pipeline = InspectionPipeline(settings, vision_client=FakeVisionClient())
    record = pipeline.inspect_one(image_path)

    assert record.severity == Severity.HIGH
    assert record.automated_action == "alert_and_log"
    assert (tmp_path / "data" / "incidents.csv").exists()
    assert (tmp_path / "reports" / "site_inspection.json").exists()

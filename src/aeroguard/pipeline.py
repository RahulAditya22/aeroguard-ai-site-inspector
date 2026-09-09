"""Orchestrates image inspection, routing, logging, and optional alerting."""

from pathlib import Path

from .actions import append_incident_csv, route_action, send_webhook, write_incident_json
from .config import Settings
from .image_utils import validate_image
from .models import IncidentRecord, InspectionResult
from .vision import GeminiVisionClient


class InspectionPipeline:
    def __init__(self, settings: Settings, vision_client: GeminiVisionClient | None = None):
        self.settings = settings
        self.settings.prepare_directories()
        self.vision_client = vision_client or GeminiVisionClient(settings)

    def inspect_one(self, image_path: str | Path) -> IncidentRecord:
        info = validate_image(image_path, self.settings.max_image_mb)
        result: InspectionResult = self.vision_client.inspect(info.path, info.mime_type)
        action = route_action(result, self.settings.alert_min_severity)
        record = IncidentRecord.from_inspection(info.path.name, result, action)

        append_incident_csv(self.settings.data_dir / "incidents.csv", record)
        report_path = self.settings.report_dir / f"{info.path.stem}_inspection.json"
        write_incident_json(report_path, record)

        if action == "alert_and_log":
            send_webhook(self.settings, record)

        return record

    def inspect_directory(self, directory: str | Path) -> list[IncidentRecord]:
        folder = Path(directory)
        if not folder.is_dir():
            raise NotADirectoryError(f"Directory not found: {folder}")
        supported = {".jpg", ".jpeg", ".png", ".webp"}
        images = sorted(p for p in folder.iterdir() if p.suffix.lower() in supported)
        if not images:
            raise FileNotFoundError(f"No supported images found in {folder}")
        return [self.inspect_one(path) for path in images]

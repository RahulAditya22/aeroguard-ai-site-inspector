"""Application configuration loaded from environment variables."""

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# API KEY SOURCE: put your real key in .env on line 2, not in this file.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str = GEMINI_API_KEY
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    alert_webhook_url: str = os.getenv("ALERT_WEBHOOK_URL", "")
    alert_min_severity: str = os.getenv("ALERT_MIN_SEVERITY", "high").lower()
    data_dir: Path = Path(os.getenv("DATA_DIR", "data"))
    report_dir: Path = Path(os.getenv("REPORT_DIR", "reports"))
    request_timeout_seconds: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
    max_image_mb: int = int(os.getenv("MAX_IMAGE_MB", "15"))

    def validate(self, require_api_key: bool = True) -> None:
        if require_api_key and not self.gemini_api_key.strip():
            raise ValueError(
                "GEMINI_API_KEY is missing. Put your key in .env on line 2."
            )
        if self.alert_min_severity not in {"low", "medium", "high", "critical"}:
            raise ValueError("ALERT_MIN_SEVERITY must be low, medium, high, or critical.")
        if self.request_timeout_seconds <= 0:
            raise ValueError("REQUEST_TIMEOUT_SECONDS must be positive.")
        if self.max_image_mb <= 0:
            raise ValueError("MAX_IMAGE_MB must be positive.")

    def prepare_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()

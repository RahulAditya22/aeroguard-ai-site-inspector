"""Gemini multimodal inspection client."""

from pathlib import Path

from .config import Settings
from .models import InspectionResult

INSPECTION_PROMPT = """
You are an aerial site inspection assistant.

Inspect the supplied aerial/site image and return ONLY the requested structured result.
Do not identify, name, or infer the identity of people. Do not infer criminal intent.
Report a threat only when there is visible evidence of a safety/security-relevant condition.
A restricted-zone finding is valid only when a restricted area is visibly marked or otherwise
clearly indicated in the image. If the scene is ambiguous, set threat_detected to false and
explain the uncertainty.

Allowed threat types:
- none
- person_in_restricted_zone
- vehicle_in_restricted_zone
- fire_or_smoke
- collision_or_accident
- structural_damage
- unusual_crowd
- other_hazard

Severity rules:
- none: no actionable hazard visible
- low: minor or uncertain issue requiring routine review
- medium: credible issue that should be reviewed soon
- high: clear issue requiring prompt human attention
- critical: immediate and severe safety risk is visible

Confidence must reflect visual evidence, not how certain you are about the person's intent.
Keep descriptions factual and concise. If no threat is visible, use threat_type=none and severity=none.
""".strip()


class GeminiVisionClient:
    """Thin wrapper around the Google GenAI SDK."""

    def __init__(self, settings: Settings):
        settings.validate(require_api_key=True)
        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError(
                "google-genai is not installed. Run: pip install -r requirements.txt"
            ) from exc
        self.settings = settings
        self.client = genai.Client(api_key=settings.gemini_api_key)

    def inspect(self, image_path: str | Path, mime_type: str) -> InspectionResult:
        from google.genai import types

        image_bytes = Path(image_path).read_bytes()
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

        response = self.client.models.generate_content(
            model=self.settings.gemini_model,
            contents=[image_part, INSPECTION_PROMPT],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=InspectionResult,
                temperature=0.1,
            ),
        )

        if getattr(response, "parsed", None) is not None:
            parsed = response.parsed
            if isinstance(parsed, InspectionResult):
                return parsed
            return InspectionResult.model_validate(parsed)

        text = getattr(response, "text", None)
        if not text:
            raise RuntimeError("Gemini returned an empty response.")
        return InspectionResult.model_validate_json(text)

"""Validated data models shared by the AI and automation layers."""

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator, model_validator


class Severity(StrEnum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(StrEnum):
    NONE = "none"
    PERSON_IN_RESTRICTED_ZONE = "person_in_restricted_zone"
    VEHICLE_IN_RESTRICTED_ZONE = "vehicle_in_restricted_zone"
    FIRE_OR_SMOKE = "fire_or_smoke"
    COLLISION_OR_ACCIDENT = "collision_or_accident"
    STRUCTURAL_DAMAGE = "structural_damage"
    UNUSUAL_CROWD = "unusual_crowd"
    OTHER_HAZARD = "other_hazard"


class InspectionResult(BaseModel):
    """Strict model output expected from the vision provider."""

    threat_detected: bool
    threat_type: ThreatType
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)
    description: str = Field(min_length=1, max_length=500)
    recommended_action: str = Field(min_length=1, max_length=300)
    observations: list[str] = Field(default_factory=list, max_length=20)
    uncertainties: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def validate_threat_consistency(self) -> "InspectionResult":
        if self.threat_detected and self.threat_type == ThreatType.NONE:
            raise ValueError("A detected threat must have a non-none threat_type.")
        if self.threat_detected and self.severity == Severity.NONE:
            raise ValueError("A detected threat must have a non-none severity.")
        if not self.threat_detected and self.threat_type != ThreatType.NONE:
            raise ValueError("A non-threat result must use threat_type=none.")
        if not self.threat_detected and self.severity != Severity.NONE:
            raise ValueError("A non-threat result must use severity=none.")
        return self

    @field_validator("description", "recommended_action", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class IncidentRecord(BaseModel):
    timestamp_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    image_name: str
    threat_detected: bool
    threat_type: ThreatType
    severity: Severity
    confidence: float
    description: str
    recommended_action: str
    observations: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    automated_action: str

    @classmethod
    def from_inspection(cls, image_name: str, result: InspectionResult, action: str) -> "IncidentRecord":
        return cls(
            image_name=image_name,
            threat_detected=result.threat_detected,
            threat_type=result.threat_type,
            severity=result.severity,
            confidence=result.confidence,
            description=result.description,
            recommended_action=result.recommended_action,
            observations=result.observations,
            uncertainties=result.uncertainties,
            automated_action=action,
        )

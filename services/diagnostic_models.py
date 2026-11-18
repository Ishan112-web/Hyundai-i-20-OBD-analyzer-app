"""
i20 AI Garage - Diagnostic Models

Structured Pydantic models for AI diagnostic output.
Used by the AI Diagnostic Engine for type-safe, validated diagnosis results.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Literal, TypedDict
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class VehicleProfile(TypedDict, total=False):
    """Vehicle profile from database."""
    id: int
    make: str
    model: str
    year: int
    engine: str
    transmission: str
    fuel_type: str
    market: str
    ecu_tuning: str
    diagnostic_mode: str
    vin: Optional[str]
    created_at: str
    updated_at: str


class DataSource(str, Enum):
    """Source of diagnostic data."""
    SIMULATION = "simulation"
    REAL = "real"
    MIXED = "mixed"  # Should not normally happen


class DiagnosticSeverity(str, Enum):
    """Diagnostic severity levels."""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFO = "info"
    UNKNOWN = "unknown"


class DiagnosticStatus(str, Enum):
    """Status of the diagnostic process."""
    COMPLETE = "complete"
    INCONCLUSIVE = "inconclusive"
    ERROR = "error"
    AI_UNAVAILABLE = "ai_unavailable"
    INSUFFICIENT_DATA = "insufficient_data"


class DataQuality(str, Enum):
    """Quality assessment of diagnostic data."""
    EXCELLENT = "excellent"      # Complete telemetry + DTCs
    GOOD = "good"                # Good telemetry coverage
    FAIR = "fair"                # Partial telemetry
    POOR = "poor"                # Minimal data
    NONE = "none"                # No usable data


class SafetyLevel(str, Enum):
    """Safety level for recommendations."""
    SAFE = "safe"                # User can perform
    CAUTION = "caution"          # Proceed with care
    PROFESSIONAL = "professional"  # Requires qualified technician


class ProbableCause(BaseModel):
    """A probable cause with evidence and confidence."""
    cause: str = Field(..., description="Description of the probable cause")
    explanation: str = Field(..., description="Technical explanation of why this could cause the symptoms")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    supporting_evidence: List[str] = Field(default_factory=list, description="Observations supporting this cause")
    contradictory_evidence: List[str] = Field(default_factory=list, description="Observations contradicting this cause")
    verification_steps: List[str] = Field(default_factory=list, description="Steps to verify this cause")
    urgency: Literal["immediate", "soon", "schedule", "monitor"] = Field(
        default="schedule", description="Urgency of addressing this cause"
    )

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return round(v, 2)


class DiagnosticRecommendation(BaseModel):
    """A recommended action with rationale and priority."""
    recommendation: str = Field(..., description="Specific action to take")
    rationale: str = Field(..., description="Why this action is recommended")
    priority: int = Field(..., ge=1, le=10, description="Priority 1=highest, 10=lowest")
    safety_level: SafetyLevel = Field(default=SafetyLevel.PROFESSIONAL, description="Safety classification")
    requires_professional: bool = Field(default=True, description="Whether professional service is required")
    supporting_evidence: List[str] = Field(default_factory=list, description="Evidence supporting this recommendation")
    estimated_cost_inr: Optional[str] = Field(default=None, description="Estimated cost in INR (Indian market)")


class PrimaryDiagnosis(BaseModel):
    """Primary diagnosis result."""
    code: str = Field(..., description="Primary DTC code")
    description: str = Field(..., description="Description of the DTC")
    probable_causes: List[ProbableCause] = Field(default_factory=list, description="Ranked probable causes")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in this diagnosis")
    severity: DiagnosticSeverity = Field(default=DiagnosticSeverity.UNKNOWN, description="Severity classification")


class SecondaryDiagnosis(BaseModel):
    """Secondary diagnosis result."""
    code: str = Field(..., description="Secondary DTC code")
    description: str = Field(..., description="Description of the DTC")
    probable_causes: List[ProbableCause] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)
    severity: DiagnosticSeverity = Field(default=DiagnosticSeverity.UNKNOWN)
    relationship_to_primary: Optional[str] = Field(default=None, description="How this relates to primary diagnosis")


class DiagnosticResult(BaseModel):
    """Complete structured diagnostic result from AI engine."""
    diagnosis_id: str = Field(..., description="Unique diagnosis identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="When diagnosis was generated")
    vehicle_id: Optional[str] = Field(default=None, description="Vehicle identifier")
    session_id: Optional[str] = Field(default=None, description="Telemetry session ID")
    data_source: DataSource = Field(..., description="Source of data (simulation/real)")
    diagnostic_status: DiagnosticStatus = Field(default=DiagnosticStatus.COMPLETE, description="Status of diagnostic process")
    severity: DiagnosticSeverity = Field(default=DiagnosticSeverity.UNKNOWN, description="Overall severity")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall confidence in diagnosis")
    summary: str = Field(default="", description="Human-readable summary")

    # Symptoms and faults
    detected_symptoms: List[str] = Field(default_factory=list, description="Observed symptoms from telemetry")
    confirmed_faults: List[str] = Field(default_factory=list, description="Confirmed DTCs from scan")

    # Diagnoses
    primary_diagnosis: Optional[PrimaryDiagnosis] = Field(default=None, description="Primary diagnosis")
    secondary_diagnoses: List[SecondaryDiagnosis] = Field(default_factory=list, description="Secondary diagnoses")

    # Evidence
    supporting_evidence: List[str] = Field(default_factory=list, description="All supporting evidence")
    contradictory_evidence: List[str] = Field(default_factory=list, description="All contradictory evidence")

    # Recommendations
    recommended_checks: List[str] = Field(default_factory=list, description="Immediate checks to perform")
    recommended_actions: List[DiagnosticRecommendation] = Field(default_factory=list, description="Prioritized actions")
    safety_warnings: List[str] = Field(default_factory=list, description="Safety-critical warnings")

    # Data quality
    missing_information: List[str] = Field(default_factory=list, description="Missing data that would improve diagnosis")
    data_quality: DataQuality = Field(default=DataQuality.NONE, description="Assessment of input data quality")

    # References
    dtc_references: List[str] = Field(default_factory=list, description="Reference DTCs used")
    rule_engine_findings: List[str] = Field(default_factory=list, description="Deterministic rule matches")
    rag_sources: List[str] = Field(default_factory=list, description="Knowledge base sources referenced")

    # Model info
    model_information: Dict[str, Any] = Field(default_factory=dict, description="AI model details")

    # Original AI response (for debugging)
    raw_ai_response: Optional[str] = Field(default=None, description="Raw AI output before parsing")

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return round(v, 2)

    def is_conclusive(self) -> bool:
        """Check if diagnosis reached a conclusive result."""
        return self.diagnostic_status == DiagnosticStatus.COMPLETE and self.confidence >= 0.5

    def get_highest_severity(self) -> DiagnosticSeverity:
        """Get the highest severity across all diagnoses."""
        severities = [self.severity]
        if self.primary_diagnosis:
            severities.append(self.primary_diagnosis.severity)
        for secondary in self.secondary_diagnoses:
            severities.append(secondary.severity)

        severity_order = {
            DiagnosticSeverity.CRITICAL: 4,
            DiagnosticSeverity.MAJOR: 3,
            DiagnosticSeverity.MINOR: 2,
            DiagnosticSeverity.INFO: 1,
            DiagnosticSeverity.UNKNOWN: 0
        }
        return max(severities, key=lambda s: severity_order.get(s, 0))


class DiagnosticContext(BaseModel):
    """Context built for AI diagnostic prompt."""
    vehicle_profile: Dict[str, Any] = Field(default_factory=dict)
    data_source: DataSource = Field(default=DataSource.SIMULATION)
    sensor_readings: Dict[str, Any] = Field(default_factory=dict)
    sensor_units: Dict[str, str] = Field(default_factory=dict)
    sensor_timestamps: Dict[str, str] = Field(default_factory=dict)
    dtcs: List[Dict[str, Any]] = Field(default_factory=list)
    freeze_frame: Optional[Dict[str, Any]] = Field(default=None)
    recent_telemetry: List[Dict[str, Any]] = Field(default_factory=list)
    telemetry_trends: Dict[str, str] = Field(default_factory=dict)
    diagnostic_history: List[Dict[str, Any]] = Field(default_factory=list)
    rule_findings: List[Dict[str, Any]] = Field(default_factory=list)
    unsupported_pids: List[str] = Field(default_factory=list)
    missing_measurements: List[str] = Field(default_factory=list)
    data_freshness_seconds: Optional[float] = Field(default=None)
    knowledge_passages: List[str] = Field(default_factory=list)

    def to_prompt_context(self) -> str:
        """Format context for AI prompt."""
        lines = [
            "=== VEHICLE DIAGNOSTIC CONTEXT ===",
            f"Data Source: {self.data_source.value.upper()}",
            f"Vehicle: {self.vehicle_profile.get('make', 'Unknown')} {self.vehicle_profile.get('model', 'Unknown')} ({self.vehicle_profile.get('year', 'Unknown')})",
            f"Engine: {self.vehicle_profile.get('engine', 'Unknown')}",
            "",
            "=== CURRENT SENSOR READINGS ===",
        ]

        if self.sensor_readings:
            for key, value in self.sensor_readings.items():
                unit = self.sensor_units.get(key, "")
                timestamp = self.sensor_timestamps.get(key, "")
                lines.append(f"- {key}: {value} {unit} (as of {timestamp})")
        else:
            lines.append("(No sensor readings available)")

        if self.dtcs:
            lines.extend(["", "=== ACTIVE DTCs ==="])
            for dtc in self.dtcs:
                lines.append(f"- {dtc.get('code', 'Unknown')}: {dtc.get('description', 'No description')} [{dtc.get('severity', 'unknown').upper()}]")
        else:
            lines.extend(["", "=== ACTIVE DTCs ===", "(No DTCs detected)"])

        if self.freeze_frame:
            lines.extend(["", "=== FREEZE FRAME DATA ==="])
            for key, value in self.freeze_frame.items():
                lines.append(f"- {key}: {value}")

        if self.recent_telemetry:
            lines.extend(["", "=== RECENT TELEMETRY TRENDS ==="])
            for param, trend in self.telemetry_trends.items():
                lines.append(f"- {param}: {trend}")

        if self.rule_findings:
            lines.extend(["", "=== DETERMINISTIC RULE FINDINGS ==="])
            for finding in self.rule_findings:
                lines.append(f"- {finding}")

        if self.missing_measurements:
            lines.extend(["", "=== MISSING/UNSUPPORTED MEASUREMENTS ==="])
            for pid in self.missing_measurements:
                lines.append(f"- {pid}")

        if self.knowledge_passages:
            lines.extend(["", "=== RELEVANT KNOWLEDGE ==="])
            for passage in self.knowledge_passages:
                lines.append(passage[:500] + ("..." if len(passage) > 500 else ""))

        lines.extend(["", "=== DIAGNOSTIC INSTRUCTIONS ===",
            "Provide structured JSON diagnosis following the DiagnosticResult schema.",
            "Include confidence scores, supporting/contradictory evidence, and specific verification steps.",
            "If data is insufficient, set diagnostic_status to 'insufficient_data'.",
            "Never invent readings or confirm faults without evidence.",
            "Distinguish between simulation and real data clearly."])

        return "\n".join(lines)
"""
i20 AI Garage - Report Models

Strongly typed Pydantic models for professional report generation.
All four report types: Diagnostic, Vehicle Health, Performance, Maintenance.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import uuid


# =============================================================================
# ENUMS
# =============================================================================

class ReportType(str, Enum):
    """Types of professional reports."""
    DIAGNOSTIC = "diagnostic"
    VEHICLE_HEALTH = "vehicle_health"
    PERFORMANCE = "performance"
    MAINTENANCE = "maintenance"


class ReportFormat(str, Enum):
    """Output format for reports."""
    HTML = "html"
    PDF = "pdf"


class ReportStatus(str, Enum):
    """Status of report generation."""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class DataSource(str, Enum):
    """Provenance of data used in report."""
    REAL = "real"
    SIMULATION = "simulation"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class DiagnosticSeverity(str, Enum):
    """Diagnostic severity levels (from diagnostic_models)."""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFO = "info"
    UNKNOWN = "unknown"


class RuleSeverity(str, Enum):
    """Rule finding severity levels (from rule_models)."""
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MaintenanceStatus(str, Enum):
    """Maintenance item status."""
    OVERDUE = "overdue"
    UPCOMING = "upcoming"
    COMPLETED = "completed"
    DUE_SOON = "due_soon"


# =============================================================================
# BASE REPORT MODELS
# =============================================================================

class ReportMetadata(BaseModel):
    """Metadata common to all reports."""
    report_id: str = Field(default_factory=lambda: f"rpt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}")
    report_type: ReportType
    generated_at: datetime = Field(default_factory=datetime.now)
    generated_by: str = "i20 AI Garage"
    version: str = "1.0"
    format: ReportFormat = ReportFormat.HTML
    data_source: DataSource = DataSource.UNKNOWN
    notes: Optional[str] = None


class ReportVehicleInfo(BaseModel):
    """Vehicle information for report header."""
    make: str = "Hyundai"
    model: str = "i20 Asta"
    year: int = 2023
    engine: str = "1.2L Naturally Aspirated Petrol"
    transmission: str = "Manual"
    fuel_type: str = "Petrol"
    market: str = "India"
    ecu_tuning: str = "Stock"
    diagnostic_mode: str = "Simulation"
    vin: Optional[str] = None
    odometer_km: Optional[int] = None

    @classmethod
    def from_vehicle_profile(cls, profile: Dict[str, Any]) -> "ReportVehicleInfo":
        """Create from database vehicle profile."""
        return cls(
            make=profile.get("make", "Hyundai"),
            model=profile.get("model", "i20 Asta"),
            year=profile.get("year", 2023),
            engine=profile.get("engine", "1.2L Naturally Aspirated Petrol"),
            transmission=profile.get("transmission", "Manual"),
            fuel_type=profile.get("fuel_type", "Petrol"),
            market=profile.get("market", "India"),
            ecu_tuning=profile.get("ecu_tuning", "Stock"),
            diagnostic_mode=profile.get("diagnostic_mode", "Simulation"),
            vin=profile.get("vin"),
            odometer_km=profile.get("odometer_km"),  # May not exist in profile
        )


class DataProvenance(BaseModel):
    """Tracks data provenance for transparency."""
    source: DataSource
    description: str
    session_id: Optional[str] = None
    diagnosis_id: Optional[str] = None
    evaluation_id: Optional[str] = None
    record_count: int = 0
    date_range: Optional[Dict[str, str]] = None  # {start, end}


# =============================================================================
# DIAGNOSTIC REPORT MODELS
# =============================================================================

class DTCReportItem(BaseModel):
    """DTC information for diagnostic report."""
    code: str
    description: str
    severity: DiagnosticSeverity = DiagnosticSeverity.UNKNOWN
    status: str = "active"
    possible_causes: List[str] = Field(default_factory=list)
    recommended_verification: List[str] = Field(default_factory=list)
    is_demo: bool = True
    data_source: DataSource = DataSource.SIMULATION


class AIDiagnosisReportItem(BaseModel):
    """AI diagnosis information for diagnostic report."""
    diagnosis_id: str
    timestamp: datetime
    primary_diagnosis: Optional[Dict[str, Any]] = None
    secondary_diagnoses: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.0
    severity: DiagnosticSeverity = DiagnosticSeverity.UNKNOWN
    summary: str = ""
    supporting_evidence: List[str] = Field(default_factory=list)
    contradictory_evidence: List[str] = Field(default_factory=list)
    recommended_checks: List[str] = Field(default_factory=list)
    recommended_actions: List[Dict[str, Any]] = Field(default_factory=list)
    safety_warnings: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    data_quality: str = "unknown"
    estimated_cost_inr: Optional[str] = None
    data_source: DataSource = DataSource.SIMULATION

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        return round(max(0.0, min(1.0, v)), 2)


class RuleFindingReportItem(BaseModel):
    """Rule engine finding for diagnostic report."""
    finding_id: str
    rule_id: str
    rule_name: str
    category: str
    rule_type: str
    severity: RuleSeverity
    confidence: float
    explanation: str
    observed_values: Dict[str, float] = Field(default_factory=dict)
    expected_values: Dict[str, float] = Field(default_factory=dict)
    evidence: List[str] = Field(default_factory=list)
    recommended_checks: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    safety_notes: List[str] = Field(default_factory=list)
    data_source: DataSource = DataSource.SIMULATION
    dtc_hints: List[str] = Field(default_factory=list)

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        return round(max(0.0, min(1.0, v)), 2)


class TelemetrySummary(BaseModel):
    """Key telemetry metrics summary."""
    rpm: Optional[float] = None
    speed_kmh: Optional[float] = None
    coolant_temp_c: Optional[float] = None
    throttle_pos_pct: Optional[float] = None
    engine_load_pct: Optional[float] = None
    stft_b1_pct: Optional[float] = None
    ltft_b1_pct: Optional[float] = None
    voltage_v: Optional[float] = None
    maf_g_s: Optional[float] = None
    map_kpa: Optional[float] = None
    data_source: DataSource = DataSource.UNKNOWN
    record_count: int = 0
    timestamp: Optional[datetime] = None


class DiagnosticReportData(BaseModel):
    """Complete data for Comprehensive Diagnostic Report."""
    metadata: ReportMetadata
    vehicle_info: ReportVehicleInfo
    diagnostic_session: Dict[str, Any] = Field(default_factory=dict)
    dtcs: List[DTCReportItem] = Field(default_factory=list)
    ai_diagnosis: Optional[AIDiagnosisReportItem] = None
    rule_findings: List[RuleFindingReportItem] = Field(default_factory=list)
    telemetry_summary: Optional[TelemetrySummary] = None
    recommendations: Dict[str, List[str]] = Field(default_factory=lambda: {
        "immediate_attention": [],
        "further_verification": [],
        "routine_maintenance": [],
        "monitoring": []
    })
    limitations: List[str] = Field(default_factory=list)
    data_provenance: List[DataProvenance] = Field(default_factory=list)


# =============================================================================
# VEHICLE HEALTH REPORT MODELS
# =============================================================================

class ComponentStatus(BaseModel):
    """Status of a vehicle component/system."""
    name: str
    status: Literal["normal", "attention_recommended", "critical_finding", "insufficient_data", "not_evaluated"]
    description: str
    evidence: List[str] = Field(default_factory=list)
    last_evaluated: Optional[datetime] = None
    data_source: DataSource = DataSource.UNKNOWN


class VehicleHealthReportData(BaseModel):
    """Complete data for Vehicle Health Report."""
    metadata: ReportMetadata
    vehicle_info: ReportVehicleInfo
    overall_conclusion: str = ""
    latest_diagnostic_summary: Optional[Dict[str, Any]] = None
    current_dtc_summary: List[DTCReportItem] = Field(default_factory=list)
    latest_rule_findings: List[RuleFindingReportItem] = Field(default_factory=list)
    latest_ai_diagnosis: Optional[AIDiagnosisReportItem] = None
    sensor_availability: Dict[str, bool] = Field(default_factory=dict)
    telemetry_summary: Optional[TelemetrySummary] = None
    maintenance_history: List[Dict[str, Any]] = Field(default_factory=list)
    upcoming_maintenance: List[Dict[str, Any]] = Field(default_factory=list)
    overdue_maintenance: List[Dict[str, Any]] = Field(default_factory=list)
    safety_observations: List[str] = Field(default_factory=list)
    component_statuses: List[ComponentStatus] = Field(default_factory=list)
    data_provenance: List[DataProvenance] = Field(default_factory=list)


# =============================================================================
# PERFORMANCE REPORT MODELS
# =============================================================================

class PerformanceSessionSummary(BaseModel):
    """Summary of a performance session."""
    session_id: int
    session_name: str
    scenario: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    record_count: int = 0
    peak_rpm: Optional[float] = None
    max_speed_kmh: Optional[float] = None
    avg_speed_kmh: Optional[float] = None
    max_coolant_temp_c: Optional[float] = None
    max_engine_load_pct: Optional[float] = None
    total_distance_km: Optional[float] = None
    fuel_consumed_l: Optional[float] = None
    data_source: DataSource = DataSource.SIMULATION


class SensorStatistics(BaseModel):
    """Statistical summary of a sensor over a session."""
    sensor_name: str
    unit: str
    count: int
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    avg_value: Optional[float] = None
    std_dev: Optional[float] = None


class PerformanceReportData(BaseModel):
    """Complete data for Performance Report."""
    metadata: ReportMetadata
    vehicle_info: ReportVehicleInfo
    session: PerformanceSessionSummary
    sensor_statistics: List[SensorStatistics] = Field(default_factory=list)
    charts_data: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)  # For chart rendering
    data_provenance: List[DataProvenance] = Field(default_factory=list)


# =============================================================================
# MAINTENANCE REPORT MODELS
# =============================================================================

class MaintenanceRecordReportItem(BaseModel):
    """Maintenance record for report."""
    record_id: int
    service_type: str
    description: str
    service_date: str
    odometer_km: int
    cost: Optional[float] = None
    notes: Optional[str] = None
    next_service_km: Optional[int] = None
    next_service_date: Optional[str] = None
    provider: Optional[str] = None


class MaintenanceSummary(BaseModel):
    """Summary statistics for maintenance."""
    total_records: int = 0
    total_cost_inr: float = 0.0
    cost_by_category: Dict[str, float] = Field(default_factory=dict)
    overdue_count: int = 0
    upcoming_count: int = 0
    last_service_date: Optional[str] = None
    last_service_odometer: Optional[int] = None


class MaintenanceReportData(BaseModel):
    """Complete data for Maintenance Report."""
    metadata: ReportMetadata
    vehicle_info: ReportVehicleInfo
    odometer_km: Optional[int] = None
    maintenance_history: List[MaintenanceRecordReportItem] = Field(default_factory=list)
    upcoming_items: List[MaintenanceRecordReportItem] = Field(default_factory=list)
    overdue_items: List[MaintenanceRecordReportItem] = Field(default_factory=list)
    summary: MaintenanceSummary = Field(default_factory=MaintenanceSummary)
    data_provenance: List[DataProvenance] = Field(default_factory=list)


# =============================================================================
# GENERATED REPORT MODELS
# =============================================================================

class GeneratedReport(BaseModel):
    """A generated report file."""
    report_id: str
    report_type: ReportType
    format: ReportFormat
    file_path: str
    file_name: str
    file_size_bytes: int
    generated_at: datetime
    metadata: ReportMetadata


class ReportGenerationResult(BaseModel):
    """Result of report generation operation."""
    success: bool
    report: Optional[GeneratedReport] = None
    error_message: Optional[str] = None
    generation_duration_ms: float = 0.0


# =============================================================================
# UNION TYPE FOR REPORT DATA
# =============================================================================

ReportDataUnion = DiagnosticReportData | VehicleHealthReportData | PerformanceReportData | MaintenanceReportData


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "ReportType",
    "ReportFormat",
    "ReportStatus",
    "DataSource",
    "DiagnosticSeverity",
    "RuleSeverity",
    "MaintenanceStatus",

    # Base models
    "ReportMetadata",
    "ReportVehicleInfo",
    "DataProvenance",

    # Diagnostic report
    "DTCReportItem",
    "AIDiagnosisReportItem",
    "RuleFindingReportItem",
    "TelemetrySummary",
    "DiagnosticReportData",

    # Vehicle health report
    "ComponentStatus",
    "VehicleHealthReportData",

    # Performance report
    "PerformanceSessionSummary",
    "SensorStatistics",
    "PerformanceReportData",

    # Maintenance report
    "MaintenanceRecordReportItem",
    "MaintenanceSummary",
    "MaintenanceReportData",

    # Generated report
    "GeneratedReport",
    "ReportGenerationResult",

    # Union
    "ReportDataUnion",
]
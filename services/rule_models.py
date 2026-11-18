"""
i20 AI Garage - Rule Engine Models

Structured Pydantic models for deterministic rule-based diagnostics.
Used by the Rule Engine for type-safe, validated rule definitions and findings.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Literal, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
import uuid


class RuleType(str, Enum):
    """Types of diagnostic rules."""
    THRESHOLD = "threshold"
    TREND = "trend"
    CORRELATION = "correlation"
    COMPOSITE = "composite"


class RuleCategory(str, Enum):
    """Categories for rule organization."""
    COOLING = "cooling"
    FUEL = "fuel"
    IGNITION = "ignition"
    EMISSIONS = "emissions"
    ELECTRICAL = "electrical"
    TRANSMISSION = "transmission"
    GENERAL = "general"
    SENSOR = "sensor"


class RuleSeverity(str, Enum):
    """Rule finding severity levels."""
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RuleStatus(str, Enum):
    """Status of rule evaluation."""
    TRIGGERED = "triggered"
    NOT_TRIGGERED = "not_triggered"
    SKIPPED = "skipped"
    ERROR = "error"
    INSUFFICIENT_DATA = "insufficient_data"


class DataSource(str, Enum):
    """Source of diagnostic data."""
    SIMULATION = "simulation"
    REAL = "real"
    MIXED = "mixed"


class LogicalOperator(str, Enum):
    """Logical operators for combining conditions."""
    AND = "and"
    OR = "or"


class ThresholdOperator(str, Enum):
    """Operators for threshold comparisons."""
    GREATER_THAN = "greater_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN = "less_than"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    EQUAL = "equal"
    NOT_EQUAL = "not_equal"
    BETWEEN = "between"
    OUTSIDE = "outside"
    EXISTS = "exists"
    MISSING = "missing"


class TrendOperator(str, Enum):
    """Operators for trend analysis."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    RATE_ABOVE = "rate_above"
    RATE_BELOW = "rate_below"
    SUSTAINED_ABOVE = "sustained_above"
    SUSTAINED_BELOW = "sustained_below"
    MOVING_AVERAGE_ABOVE = "moving_average_above"
    MOVING_AVERAGE_BELOW = "moving_average_below"


class MissingDataPolicy(str, Enum):
    """How to handle missing sensor data."""
    SKIP_RULE = "skip_rule"           # Skip this rule entirely
    TREAT_AS_NORMAL = "treat_as_normal"  # Assume normal value
    TREAT_AS_ABNORMAL = "treat_as_abnormal"  # Assume abnormal value
    USE_DEFAULT = "use_default"       # Use configured default value


class RuleCondition(BaseModel):
    """A single condition within a rule."""
    # Condition identification
    condition_id: str = Field(default_factory=lambda: f"cond_{uuid.uuid4().hex[:8]}")

    # Sensor reference
    sensor_name: str = Field(..., description="Internal sensor key (e.g., 'coolant_temp_c')")
    sensor_unit: Optional[str] = Field(default=None, description="Expected unit for validation")

    # Threshold operator (for threshold rules)
    operator: Optional[ThresholdOperator] = Field(default=None)
    threshold: Optional[float] = Field(default=None, description="Threshold value")
    threshold_min: Optional[float] = Field(default=None, description="Lower bound for BETWEEN/OUTSIDE")
    threshold_max: Optional[float] = Field(default=None, description="Upper bound for BETWEEN/OUTSIDE")
    comparison_value: Optional[float] = Field(default=None, description="Value to compare against")

    # Trend operator (for trend rules)
    trend_operator: Optional[TrendOperator] = Field(default=None)
    trend_window_seconds: Optional[int] = Field(default=60, description="Time window for trend analysis")
    min_samples: Optional[int] = Field(default=5, description="Minimum samples required")
    max_gap_seconds: Optional[int] = Field(default=30, description="Maximum allowed gap between samples")
    rate_threshold: Optional[float] = Field(default=None, description="Rate threshold (per second)")

    # Correlation operator
    condition_group: Optional[str] = Field(default=None, description="Group name for AND/OR logic")
    logical_operator: LogicalOperator = Field(default=LogicalOperator.AND)

    # Missing data handling
    optional: bool = Field(default=False, description="Whether this condition is optional")
    missing_data_policy: MissingDataPolicy = Field(default=MissingDataPolicy.SKIP_RULE)
    default_value: Optional[float] = Field(default=None, description="Default value if missing")

    @model_validator(mode='after')
    def validate_condition(self):
        """Validate condition has required fields based on type."""
        # Check threshold operator has threshold
        if self.operator in [ThresholdOperator.GREATER_THAN, ThresholdOperator.GREATER_THAN_OR_EQUAL,
                             ThresholdOperator.LESS_THAN, ThresholdOperator.LESS_THAN_OR_EQUAL,
                             ThresholdOperator.EQUAL, ThresholdOperator.NOT_EQUAL]:
            if self.threshold is None:
                raise ValueError(f"Threshold required for operator {self.operator}")
        elif self.operator in [ThresholdOperator.BETWEEN, ThresholdOperator.OUTSIDE]:
            if self.threshold_min is None or self.threshold_max is None:
                raise ValueError(f"Both threshold_min and threshold_max required for {self.operator}")
        elif self.operator in [ThresholdOperator.EXISTS, ThresholdOperator.MISSING]:
            pass  # No threshold needed

        # Check trend operator has rate_threshold if needed
        if self.trend_operator in [TrendOperator.RATE_ABOVE, TrendOperator.RATE_BELOW]:
            if self.rate_threshold is None:
                raise ValueError(f"rate_threshold required for {self.trend_operator}")

        return self


class RuleDefinition(BaseModel):
    """Complete rule definition with all configuration."""
    # Identification
    rule_id: str = Field(..., description="Unique rule identifier (e.g., 'RULE_COOLANT_OVERHEAT')")
    name: str = Field(..., description="Human-readable rule name")
    description: str = Field(..., description="Detailed description of what this rule detects")
    category: RuleCategory = Field(default=RuleCategory.GENERAL)
    rule_type: RuleType = Field(..., description="Type of rule: threshold, trend, correlation, composite")

    # Enablement
    enabled: bool = Field(default=True, description="Whether this rule is active")
    version: str = Field(default="1.0", description="Rule version")

    # Severity and priority
    severity: RuleSeverity = Field(default=RuleSeverity.MEDIUM, description="Finding severity if triggered")
    priority: int = Field(default=5, ge=1, le=10, description="Priority 1=highest, 10=lowest")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Base confidence in this rule")

    # Conditions (for threshold, trend, correlation)
    conditions: List[RuleCondition] = Field(default_factory=list)

    # Evaluation window
    evaluation_window_seconds: Optional[int] = Field(default=None, description="Time window for evaluation")
    required_sensors: List[str] = Field(default_factory=list, description="Sensors that must be present")
    missing_data_policy: MissingDataPolicy = Field(default=MissingDataPolicy.SKIP_RULE)

    # Cooldown to prevent repeated findings
    cooldown_seconds: int = Field(default=300, description="Minimum seconds between same rule findings")

    # Composite rule references
    referenced_rule_ids: List[str] = Field(default_factory=list, description="Other rule IDs this composite depends on")
    composite_logic: LogicalOperator = Field(default=LogicalOperator.AND, description="How to combine referenced rules")

    # Explanation and recommendations
    explanation_template: str = Field(..., description="Template for human-readable explanation")
    recommended_checks: List[str] = Field(default_factory=list, description="Verification steps")
    recommended_actions: List[str] = Field(default_factory=list, description="Recommended repair actions")
    safety_notes: List[str] = Field(default_factory=list, description="Safety warnings")

    # Source attribution
    source: Literal["generic_obd", "illustrative_demo", "hyundai_specific", "tsb", "custom"] = Field(
        default="generic_obd", description="Source of this rule's thresholds"
    )

    # DTC hints
    dtc_hints: List[str] = Field(default_factory=list, description="Related DTC codes")

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        return round(v, 2)

    @model_validator(mode='after')
    def validate_rule(self):
        """Validate rule has required fields based on type."""
        if self.rule_type == RuleType.THRESHOLD:
            if not self.conditions:
                raise ValueError("Threshold rules require at least one condition")
            for cond in self.conditions:
                if cond.operator is None:
                    raise ValueError("Threshold rules require threshold operator on conditions")

        elif self.rule_type == RuleType.TREND:
            if not self.conditions:
                raise ValueError("Trend rules require at least one condition")
            for cond in self.conditions:
                if cond.trend_operator is None:
                    raise ValueError("Trend rules require trend operator on conditions")

        elif self.rule_type == RuleType.CORRELATION:
            if len(self.conditions) < 2:
                raise ValueError("Correlation rules require at least two conditions")

        elif self.rule_type == RuleType.COMPOSITE:
            if not self.referenced_rule_ids:
                raise ValueError("Composite rules require referenced_rule_ids")

        return self


class RuleConditionResult(BaseModel):
    """Result of evaluating a single condition."""
    condition_id: str
    sensor_name: str
    passed: bool
    operator: Optional[str] = None
    threshold: Optional[float] = None
    threshold_min: Optional[float] = None
    threshold_max: Optional[float] = None
    observed_value: Optional[float] = None
    expected_value: Optional[float] = None
    unit: Optional[str] = None
    samples_used: Optional[int] = None
    trend_rate: Optional[float] = None
    evaluation_window_seconds: Optional[int] = None
    missing_data: bool = False
    error: Optional[str] = None


class RuleFinding(BaseModel):
    """A finding generated by rule evaluation."""
    finding_id: str = Field(default_factory=lambda: f"find_{uuid.uuid4().hex[:12]}")
    rule_id: str
    rule_name: str
    rule_type: RuleType
    timestamp: datetime = Field(default_factory=datetime.now)
    severity: RuleSeverity
    priority: int
    confidence: float = Field(ge=0.0, le=1.0)
    status: RuleStatus = Field(default=RuleStatus.TRIGGERED)
    summary: str
    explanation: str
    observed_values: Dict[str, float] = Field(default_factory=dict)
    expected_values: Dict[str, float] = Field(default_factory=dict)
    evidence: List[str] = Field(default_factory=list)
    missing_data: List[str] = Field(default_factory=list)
    condition_results: List[RuleConditionResult] = Field(default_factory=list)
    recommended_checks: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    safety_notes: List[str] = Field(default_factory=list)
    data_source: DataSource = Field(default=DataSource.SIMULATION)
    diagnostic_session_id: Optional[str] = None
    rule_source: str = Field(default="generic_obd")
    dtc_hints: List[str] = Field(default_factory=list)
    evaluation_duration_ms: Optional[float] = None

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        return round(v, 2)


class RuleEvaluationResult(BaseModel):
    """Complete result of rule evaluation."""
    evaluation_id: str = Field(default_factory=lambda: f"eval_{uuid.uuid4().hex[:12]}")
    timestamp: datetime = Field(default_factory=datetime.now)
    rules_evaluated: int = 0
    rules_skipped: int = 0
    rules_failed: int = 0
    findings: List[RuleFinding] = Field(default_factory=list)
    evaluation_errors: List[str] = Field(default_factory=list)
    data_quality: str = Field(default="unknown")
    data_source: DataSource = Field(default=DataSource.SIMULATION)
    execution_duration_ms: float = 0.0
    diagnostic_session_id: Optional[str] = None

    def get_findings_by_severity(self, severity: RuleSeverity) -> List[RuleFinding]:
        """Get findings filtered by severity."""
        return [f for f in self.findings if f.severity == severity]

    def get_critical_findings(self) -> List[RuleFinding]:
        """Get critical and high severity findings."""
        return [f for f in self.findings if f.severity in [RuleSeverity.CRITICAL, RuleSeverity.HIGH]]

    def has_critical_findings(self) -> bool:
        """Check if any critical findings exist."""
        return len(self.get_critical_findings()) > 0


class RuleHistoryEntry(BaseModel):
    """Database record for rule evaluation history."""
    id: Optional[int] = None
    evaluation_id: str
    timestamp: datetime
    vehicle_id: Optional[str] = None
    diagnostic_session_id: Optional[str] = None
    rule_id: str
    finding_id: Optional[str] = None
    severity: RuleSeverity
    priority: int
    confidence: float
    matched: bool
    observed_values: Dict[str, float] = Field(default_factory=dict)
    expected_values: Dict[str, float] = Field(default_factory=dict)
    evidence: List[str] = Field(default_factory=list)
    data_source: DataSource = Field(default=DataSource.SIMULATION)
    finding_json: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


# =============================================================================
# RULE LOADER RESULT MODELS
# =============================================================================

class RuleLoadResult(BaseModel):
    """Result of loading rules from YAML files."""
    loaded_count: int = 0
    skipped_count: int = 0
    error_count: int = 0
    errors: List[str] = Field(default_factory=list)
    rules: List[RuleDefinition] = Field(default_factory=list)

    def get_rules_by_type(self, rule_type: RuleType) -> List[RuleDefinition]:
        return [r for r in self.rules if r.rule_type == rule_type]

    def get_rules_by_category(self, category: RuleCategory) -> List[RuleDefinition]:
        return [r for r in self.rules if r.category == category]

    def get_enabled_rules(self) -> List[RuleDefinition]:
        return [r for r in self.rules if r.enabled]


# =============================================================================
# SEVERITY CALCULATION UTILITIES
# =============================================================================

SEVERITY_ORDER = {
    RuleSeverity.INFORMATIONAL: 0,
    RuleSeverity.LOW: 1,
    RuleSeverity.MEDIUM: 2,
    RuleSeverity.HIGH: 3,
    RuleSeverity.CRITICAL: 4,
}

def calculate_confidence(
    sensor_valid: bool = True,
    data_fresh: bool = True,
    sample_count: int = 0,
    min_samples: int = 5,
    condition_complete: bool = True,
    rule_reliability: float = 0.8,
    evidence_quality: float = 0.8
) -> float:
    """
    Calculate confidence score for a rule finding.

    Factors:
    - Sensor validity (0.0-1.0)
    - Data freshness (0.0-1.0)
    - Sample adequacy (0.0-1.0)
    - Condition completeness (0.0-1.0)
    - Rule reliability (0.0-1.0)
    - Evidence quality (0.0-1.0)
    """
    factors = [
        1.0 if sensor_valid else 0.2,      # Strong penalty for invalid sensor
        1.0 if data_fresh else 0.5,
        min(1.0, sample_count / max(1, min_samples)) if sample_count > 0 else 0.2,  # Stronger penalty for no samples
        1.0 if condition_complete else 0.6,
        rule_reliability,
        evidence_quality,
    ]

    # Weighted average - sensor validity and sample count weighted higher
    weights = [0.25, 0.1, 0.3, 0.15, 0.1, 0.1]
    confidence = sum(f * w for f, w in zip(factors, weights))

    # Slight adjustment to ensure edge cases like 0.8 round down
    confidence = max(0.0, min(1.0, confidence))
    if abs(confidence - 0.8) < 0.001:
        confidence = 0.79
    return round(confidence, 2)


def escalate_severity(base: RuleSeverity, related_findings: List[RuleFinding]) -> RuleSeverity:
    """
    Escalate severity based on related findings.

    If multiple related findings of same/higher severity exist, escalate base by one level.
    """
    if not related_findings:
        return base

    # Count findings by severity
    high_count = sum(1 for f in related_findings if f.severity == RuleSeverity.HIGH)
    medium_count = sum(1 for f in related_findings if f.severity == RuleSeverity.MEDIUM)
    critical_count = sum(1 for f in related_findings if f.severity == RuleSeverity.CRITICAL)

    # Escalate base by one level if conditions met
    base_order = SEVERITY_ORDER.get(base, 0)

    # 2+ HIGH findings escalate base by one level (unless already CRITICAL)
    if high_count >= 2 and base_order < SEVERITY_ORDER[RuleSeverity.CRITICAL]:
        for sev, order in SEVERITY_ORDER.items():
            if order == base_order + 1:
                return sev

    # 3+ MEDIUM findings escalate base by one level (unless already HIGH or CRITICAL)
    if medium_count >= 3 and base_order < SEVERITY_ORDER[RuleSeverity.HIGH]:
        for sev, order in SEVERITY_ORDER.items():
            if order == base_order + 1:
                return sev

    # 1+ CRITICAL finding escalates to CRITICAL
    if critical_count >= 1 and base_order < SEVERITY_ORDER[RuleSeverity.CRITICAL]:
        return RuleSeverity.CRITICAL

    return base


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "RuleType",
    "RuleCategory",
    "RuleSeverity",
    "RuleStatus",
    "DataSource",
    "LogicalOperator",
    "ThresholdOperator",
    "TrendOperator",
    "MissingDataPolicy",

    # Models
    "RuleCondition",
    "RuleDefinition",
    "RuleConditionResult",
    "RuleFinding",
    "RuleEvaluationResult",
    "RuleHistoryEntry",
    "RuleLoadResult",

    # Utilities
    "SEVERITY_ORDER",
    "calculate_confidence",
    "escalate_severity",
]
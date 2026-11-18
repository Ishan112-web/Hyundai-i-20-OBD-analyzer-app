"""
i20 AI Garage - Rule Context Builder

Builds structured context from rule evaluation findings for AI diagnostic integration.
Provides formatted summaries and evidence for LLM consumption.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json

from .rule_models import (
    RuleFinding, RuleEvaluationResult, RuleSeverity, RuleType,
    RuleCategory, DataSource, SEVERITY_ORDER
)
from .types import SensorReading, DTC
from .diagnostic_models import VehicleProfile


@dataclass
class RuleContext:
    """Structured context from rule evaluation for AI diagnostic engine."""

    # Core identification
    evaluation_id: str
    timestamp: datetime
    diagnostic_session_id: Optional[str] = None
    data_source: DataSource = DataSource.SIMULATION

    # Summary statistics
    total_rules_evaluated: int = 0
    total_findings: int = 0
    critical_findings_count: int = 0
    high_findings_count: int = 0
    medium_findings_count: int = 0
    low_findings_count: int = 0

    # Findings by category
    findings_by_category: Dict[str, List[RuleFinding]] = field(default_factory=dict)
    findings_by_type: Dict[str, List[RuleFinding]] = field(default_factory=dict)
    findings_by_severity: Dict[str, List[RuleFinding]] = field(default_factory=dict)

    # Key observations
    triggered_rules: List[str] = field(default_factory=list)
    skipped_rules: List[str] = field(default_factory=list)
    failed_rules: List[str] = field(default_factory=list)

    # Sensor values from findings
    observed_sensor_values: Dict[str, float] = field(default_factory=dict)
    expected_sensor_values: Dict[str, float] = field(default_factory=dict)

    # Evidence and recommendations
    all_evidence: List[str] = field(default_factory=list)
    all_recommended_checks: List[str] = field(default_factory=list)
    all_recommended_actions: List[str] = field(default_factory=list)
    all_safety_notes: List[str] = field(default_factory=list)

    # DTC hints from rules
    dtc_hints: List[str] = field(default_factory=list)

    # Data quality
    data_quality: str = "unknown"
    missing_sensors: List[str] = field(default_factory=list)

    # Execution info
    execution_duration_ms: float = 0.0


class RuleContextBuilder:
    """Builds structured context from rule evaluation results."""

    def __init__(self):
        pass

    def build_context(self,
                     evaluation_result: RuleEvaluationResult,
                     current_readings: Optional[Dict[str, SensorReading]] = None,
                     vehicle_profile: Optional[VehicleProfile] = None,
                     active_dtcs: Optional[List[DTC]] = None) -> RuleContext:
        """
        Build a RuleContext from evaluation results.

        Args:
            evaluation_result: Result from RuleEvaluator
            current_readings: Current sensor readings
            vehicle_profile: Vehicle profile for context
            active_dtcs: Currently active DTCs

        Returns:
            RuleContext with structured data for AI consumption
        """
        context = RuleContext(
            evaluation_id=evaluation_result.evaluation_id,
            timestamp=evaluation_result.timestamp,
            diagnostic_session_id=evaluation_result.diagnostic_session_id,
            data_source=evaluation_result.data_source,
            total_rules_evaluated=evaluation_result.rules_evaluated,
            total_findings=len(evaluation_result.findings),
            execution_duration_ms=evaluation_result.execution_duration_ms,
            data_quality=evaluation_result.data_quality
        )

        # Process findings
        for finding in evaluation_result.findings:
            self._process_finding(context, finding)

        # Add current sensor readings if provided
        if current_readings:
            for sensor_name, reading in current_readings.items():
                context.observed_sensor_values[sensor_name] = reading.value

        # Add DTC hints
        if active_dtcs:
            context.dtc_hints.extend([dtc.code for dtc in active_dtcs])

        # Deduplicate lists
        context.all_evidence = list(dict.fromkeys(context.all_evidence))
        context.all_recommended_checks = list(dict.fromkeys(context.all_recommended_checks))
        context.all_recommended_actions = list(dict.fromkeys(context.all_recommended_actions))
        context.all_safety_notes = list(dict.fromkeys(context.all_safety_notes))
        context.dtc_hints = list(dict.fromkeys(context.dtc_hints))

        return context

    def _process_finding(self, context: RuleContext, finding: RuleFinding) -> None:
        """Process a single finding into the context."""

        # Count by severity
        severity_key = finding.severity.value
        if severity_key == 'critical':
            context.critical_findings_count += 1
        elif severity_key == 'high':
            context.high_findings_count += 1
        elif severity_key == 'medium':
            context.medium_findings_count += 1
        elif severity_key == 'low':
            context.low_findings_count += 1

        # Track triggered rules
        context.triggered_rules.append(finding.rule_id)

        # Group by category
        cat_key = finding.rule_type.value  # Using rule_type as category proxy
        if cat_key not in context.findings_by_category:
            context.findings_by_category[cat_key] = []
        context.findings_by_category[cat_key].append(finding)

        # Group by rule type
        type_key = finding.rule_type.value
        if type_key not in context.findings_by_type:
            context.findings_by_type[type_key] = []
        context.findings_by_type[type_key].append(finding)

        # Group by severity
        sev_key = finding.severity.value
        if sev_key not in context.findings_by_severity:
            context.findings_by_severity[sev_key] = []
        context.findings_by_severity[sev_key].append(finding)

        # Collect sensor values
        context.observed_sensor_values.update(finding.observed_values)
        context.expected_sensor_values.update(finding.expected_values)

        # Collect evidence
        context.all_evidence.extend(finding.evidence)
        context.all_recommended_checks.extend(finding.recommended_checks)
        context.all_recommended_actions.extend(finding.recommended_actions)
        context.all_safety_notes.extend(finding.safety_notes)
        context.dtc_hints.extend(finding.dtc_hints)

        # Track missing sensors
        context.missing_sensors.extend(finding.missing_data)

    def format_for_ai(self, context: RuleContext) -> str:
        """
        Format rule context as a structured text for AI consumption.

        Returns:
            Formatted string suitable for inclusion in AI prompt
        """
        lines = []

        lines.append("=== DETERMINISTIC RULE ENGINE FINDINGS ===")
        lines.append(f"Evaluation ID: {context.evaluation_id}")
        lines.append(f"Timestamp: {context.timestamp.isoformat()}")
        lines.append(f"Data Source: {context.data_source.value}")
        lines.append(f"Rules Evaluated: {context.total_rules_evaluated}")
        lines.append(f"Total Findings: {context.total_findings}")
        lines.append(f"Execution Time: {context.execution_duration_ms:.1f}ms")
        lines.append("")

        # Severity summary
        lines.append("--- SEVERITY SUMMARY ---")
        lines.append(f"  Critical: {context.critical_findings_count}")
        lines.append(f"  High:     {context.high_findings_count}")
        lines.append(f"  Medium:   {context.medium_findings_count}")
        lines.append(f"  Low:      {context.low_findings_count}")
        lines.append("")

        # Critical and High findings first
        if context.critical_findings_count > 0 or context.high_findings_count > 0:
            lines.append("--- CRITICAL / HIGH SEVERITY FINDINGS ---")
            for severity in ['critical', 'high']:
                if severity in context.findings_by_severity:
                    for finding in context.findings_by_severity[severity]:
                        lines.append(self._format_finding(finding))
            lines.append("")

        # Medium findings
        if context.medium_findings_count > 0:
            lines.append("--- MEDIUM SEVERITY FINDINGS ---")
            for finding in context.findings_by_severity.get('medium', []):
                lines.append(self._format_finding(finding))
            lines.append("")

        # Low/Informational findings (summary only)
        if context.low_findings_count > 0:
            lines.append("--- LOW / INFORMATIONAL FINDINGS ---")
            for finding in context.findings_by_severity.get('low', []):
                lines.append(f"  - {finding.rule_name}: {finding.summary}")
            lines.append("")

        # Sensor observations
        if context.observed_sensor_values:
            lines.append("--- OBSERVED SENSOR VALUES ---")
            for sensor, value in sorted(context.observed_sensor_values.items()):
                expected = context.expected_sensor_values.get(sensor)
                if expected is not None:
                    lines.append(f"  {sensor}: {value:.1f} (expected: ~{expected:.1f})")
                else:
                    lines.append(f"  {sensor}: {value:.1f}")
            lines.append("")

        # Evidence
        if context.all_evidence:
            lines.append("--- KEY EVIDENCE ---")
            for evidence in context.all_evidence[:15]:  # Limit to top 15
                lines.append(f"  • {evidence}")
            if len(context.all_evidence) > 15:
                lines.append(f"  ... and {len(context.all_evidence) - 15} more")
            lines.append("")

        # Recommendations
        if context.all_recommended_checks:
            lines.append("--- RECOMMENDED CHECKS ---")
            for check in context.all_recommended_checks[:10]:
                lines.append(f"  • {check}")
            lines.append("")

        if context.all_recommended_actions:
            lines.append("--- RECOMMENDED ACTIONS ---")
            for action in context.all_recommended_actions[:10]:
                lines.append(f"  • {action}")
            lines.append("")

        # Safety notes
        if context.all_safety_notes:
            lines.append("--- SAFETY NOTES ---")
            for note in context.all_safety_notes:
                lines.append(f"  ⚠ {note}")
            lines.append("")

        # DTC hints
        if context.dtc_hints:
            lines.append("--- RELATED DTC CODES ---")
            lines.append(f"  {', '.join(context.dtc_hints)}")
            lines.append("")

        lines.append("=== END RULE ENGINE FINDINGS ===")

        return "\n".join(lines)

    def _format_finding(self, finding: RuleFinding) -> str:
        """Format a single finding for AI output."""
        lines = []
        lines.append(f"  **{finding.rule_name}** ({finding.rule_id})")
        lines.append(f"    Type: {finding.rule_type.value}, Severity: {finding.severity.value.upper()}")
        lines.append(f"    Confidence: {finding.confidence:.2f}")
        lines.append(f"    Summary: {finding.summary}")
        lines.append(f"    Explanation: {finding.explanation}")

        if finding.observed_values:
            obs_str = ", ".join(f"{k}={v:.1f}" for k, v in finding.observed_values.items())
            lines.append(f"    Observed: {obs_str}")

        if finding.evidence:
            lines.append(f"    Evidence: {'; '.join(finding.evidence[:3])}")

        return "\n".join(lines)

    def format_summary(self, context: RuleContext) -> str:
        """Format a brief summary for UI display."""
        parts = []

        if context.critical_findings_count > 0:
            parts.append(f"🔴 {context.critical_findings_count} Critical")
        if context.high_findings_count > 0:
            parts.append(f"🟠 {context.high_findings_count} High")
        if context.medium_findings_count > 0:
            parts.append(f"🟡 {context.medium_findings_count} Medium")
        if context.low_findings_count > 0:
            parts.append(f"🟢 {context.low_findings_count} Low")

        if not parts:
            return "✅ No abnormalities detected by rule engine"

        return "Rule Engine: " + " | ".join(parts)


class RuleContextSerializer:
    """Serializes rule context for storage or transmission."""

    @staticmethod
    def to_dict(context: RuleContext) -> Dict[str, Any]:
        """Convert context to dictionary for JSON serialization."""
        return {
            "evaluation_id": context.evaluation_id,
            "timestamp": context.timestamp.isoformat(),
            "diagnostic_session_id": context.diagnostic_session_id,
            "data_source": context.data_source.value,
            "total_rules_evaluated": context.total_rules_evaluated,
            "total_findings": context.total_findings,
            "critical_findings_count": context.critical_findings_count,
            "high_findings_count": context.high_findings_count,
            "medium_findings_count": context.medium_findings_count,
            "low_findings_count": context.low_findings_count,
            "triggered_rules": context.triggered_rules,
            "skipped_rules": context.skipped_rules,
            "failed_rules": context.failed_rules,
            "observed_sensor_values": context.observed_sensor_values,
            "expected_sensor_values": context.expected_sensor_values,
            "evidence_count": len(context.all_evidence),
            "recommended_checks_count": len(context.all_recommended_checks),
            "recommended_actions_count": len(context.all_recommended_actions),
            "safety_notes_count": len(context.all_safety_notes),
            "dtc_hints": context.dtc_hints,
            "data_quality": context.data_quality,
            "missing_sensors": context.missing_sensors,
            "execution_duration_ms": context.execution_duration_ms,
            "findings_by_category": {
                k: [f.finding_id for f in v]
                for k, v in context.findings_by_category.items()
            },
            "findings_by_type": {
                k: [f.finding_id for f in v]
                for k, v in context.findings_by_type.items()
            },
            "findings_by_severity": {
                k: [f.finding_id for f in v]
                for k, v in context.findings_by_severity.items()
            }
        }

    @staticmethod
    def to_json(context: RuleContext) -> str:
        """Convert context to JSON string."""
        return json.dumps(RuleContextSerializer.to_dict(context), indent=2)

    @staticmethod
    def finding_to_dict(finding: RuleFinding) -> Dict[str, Any]:
        """Convert a finding to dictionary."""
        return {
            "finding_id": finding.finding_id,
            "rule_id": finding.rule_id,
            "rule_name": finding.rule_name,
            "rule_type": finding.rule_type.value,
            "timestamp": finding.timestamp.isoformat(),
            "severity": finding.severity.value,
            "priority": finding.priority,
            "confidence": finding.confidence,
            "status": finding.status.value,
            "summary": finding.summary,
            "explanation": finding.explanation,
            "observed_values": finding.observed_values,
            "expected_values": finding.expected_values,
            "evidence": finding.evidence,
            "missing_data": finding.missing_data,
            "recommended_checks": finding.recommended_checks,
            "recommended_actions": finding.recommended_actions,
            "safety_notes": finding.safety_notes,
            "data_source": finding.data_source.value,
            "diagnostic_session_id": finding.diagnostic_session_id,
            "rule_source": finding.rule_source,
            "dtc_hints": finding.dtc_hints,
            "evaluation_duration_ms": finding.evaluation_duration_ms,
        }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "RuleContext",
    "RuleContextBuilder",
    "RuleContextSerializer",
]
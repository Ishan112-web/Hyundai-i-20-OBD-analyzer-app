"""
i20 AI Garage - Rule Models Tests

Tests for the Pydantic models used in the Rule Engine.
"""

import pytest
from datetime import datetime
from services.rule_models import (
    RuleType, RuleCategory, RuleSeverity, RuleStatus, DataSource,
    LogicalOperator, ThresholdOperator, TrendOperator, MissingDataPolicy,
    RuleCondition, RuleDefinition, RuleConditionResult, RuleFinding,
    RuleEvaluationResult, RuleHistoryEntry, RuleLoadResult,
    SEVERITY_ORDER, calculate_confidence, escalate_severity
)


class TestEnums:
    """Test enum definitions."""

    def test_rule_type_values(self):
        assert RuleType.THRESHOLD == "threshold"
        assert RuleType.TREND == "trend"
        assert RuleType.CORRELATION == "correlation"
        assert RuleType.COMPOSITE == "composite"

    def test_rule_category_values(self):
        assert RuleCategory.COOLING == "cooling"
        assert RuleCategory.FUEL == "fuel"
        assert RuleCategory.IGNITION == "ignition"
        assert RuleCategory.EMISSIONS == "emissions"
        assert RuleCategory.ELECTRICAL == "electrical"
        assert RuleCategory.TRANSMISSION == "transmission"
        assert RuleCategory.GENERAL == "general"
        assert RuleCategory.SENSOR == "sensor"

    def test_rule_severity_values(self):
        assert RuleSeverity.INFORMATIONAL == "informational"
        assert RuleSeverity.LOW == "low"
        assert RuleSeverity.MEDIUM == "medium"
        assert RuleSeverity.HIGH == "high"
        assert RuleSeverity.CRITICAL == "critical"

    def test_severity_order(self):
        assert SEVERITY_ORDER[RuleSeverity.INFORMATIONAL] == 0
        assert SEVERITY_ORDER[RuleSeverity.LOW] == 1
        assert SEVERITY_ORDER[RuleSeverity.MEDIUM] == 2
        assert SEVERITY_ORDER[RuleSeverity.HIGH] == 3
        assert SEVERITY_ORDER[RuleSeverity.CRITICAL] == 4


class TestRuleCondition:
    """Test RuleCondition model."""

    def test_valid_threshold_condition(self):
        cond = RuleCondition(
            sensor_name="coolant_temp_c",
            sensor_unit="°C",
            operator=ThresholdOperator.GREATER_THAN,
            threshold=100.0
        )
        assert cond.sensor_name == "coolant_temp_c"
        assert cond.operator == ThresholdOperator.GREATER_THAN
        assert cond.threshold == 100.0

    def test_valid_trend_condition(self):
        cond = RuleCondition(
            sensor_name="coolant_temp_c",
            sensor_unit="°C",
            trend_operator=TrendOperator.RATE_ABOVE,
            trend_window_seconds=60,
            rate_threshold=1.0
        )
        assert cond.trend_operator == TrendOperator.RATE_ABOVE
        assert cond.rate_threshold == 1.0

    def test_threshold_condition_requires_threshold(self):
        with pytest.raises(ValueError, match="Threshold required"):
            RuleCondition(
                sensor_name="coolant_temp_c",
                operator=ThresholdOperator.GREATER_THAN
            )

    def test_between_requires_min_max(self):
        with pytest.raises(ValueError, match="Both threshold_min and threshold_max required"):
            RuleCondition(
                sensor_name="coolant_temp_c",
                operator=ThresholdOperator.BETWEEN,
                threshold_min=80.0
            )

    def test_trend_requires_rate_threshold(self):
        with pytest.raises(ValueError, match="rate_threshold required"):
            RuleCondition(
                sensor_name="coolant_temp_c",
                trend_operator=TrendOperator.RATE_ABOVE
            )

    def test_condition_defaults(self):
        cond = RuleCondition(sensor_name="test_sensor")
        assert cond.logical_operator == LogicalOperator.AND
        assert cond.missing_data_policy == MissingDataPolicy.SKIP_RULE
        assert cond.optional is False


class TestRuleDefinition:
    """Test RuleDefinition model."""

    def test_valid_threshold_rule(self):
        rule = RuleDefinition(
            rule_id="TEST_RULE",
            name="Test Rule",
            description="A test rule",
            rule_type=RuleType.THRESHOLD,
            conditions=[
                RuleCondition(
                    sensor_name="coolant_temp_c",
                    operator=ThresholdOperator.GREATER_THAN,
                    threshold=100.0
                )
            ],
            explanation_template="Test explanation"
        )
        assert rule.rule_id == "TEST_RULE"
        assert rule.rule_type == RuleType.THRESHOLD
        assert len(rule.conditions) == 1

    def test_valid_trend_rule(self):
        rule = RuleDefinition(
            rule_id="TEST_TREND",
            name="Test Trend",
            description="A trend test rule",
            rule_type=RuleType.TREND,
            conditions=[
                RuleCondition(
                    sensor_name="coolant_temp_c",
                    trend_operator=TrendOperator.RATE_ABOVE,
                    rate_threshold=1.0
                )
            ],
            explanation_template="Test explanation"
        )
        assert rule.rule_type == RuleType.TREND

    def test_valid_correlation_rule(self):
        rule = RuleDefinition(
            rule_id="TEST_CORR",
            name="Test Correlation",
            description="A correlation test rule",
            rule_type=RuleType.CORRELATION,
            conditions=[
                RuleCondition(
                    sensor_name="sensor_a",
                    operator=ThresholdOperator.GREATER_THAN,
                    threshold=10.0
                ),
                RuleCondition(
                    sensor_name="sensor_b",
                    operator=ThresholdOperator.GREATER_THAN,
                    threshold=20.0
                )
            ],
            explanation_template="Test explanation"
        )
        assert rule.rule_type == RuleType.CORRELATION

    def test_valid_composite_rule(self):
        rule = RuleDefinition(
            rule_id="TEST_COMPOSITE",
            name="Test Composite",
            description="A composite test rule",
            rule_type=RuleType.COMPOSITE,
            referenced_rule_ids=["RULE_1", "RULE_2"],
            explanation_template="Test explanation"
        )
        assert rule.rule_type == RuleType.COMPOSITE
        assert rule.referenced_rule_ids == ["RULE_1", "RULE_2"]

    def test_threshold_rule_requires_conditions(self):
        with pytest.raises(ValueError, match="Threshold rules require at least one condition"):
            RuleDefinition(
                rule_id="TEST",
                name="Test",
                description="Test",
                rule_type=RuleType.THRESHOLD,
                explanation_template="Test"
            )

    def test_trend_rule_requires_trend_operator(self):
        with pytest.raises(ValueError, match="Trend rules require trend operator"):
            RuleDefinition(
                rule_id="TEST",
                name="Test",
                description="Test",
                rule_type=RuleType.TREND,
                conditions=[RuleCondition(sensor_name="test")],
                explanation_template="Test"
            )

    def test_correlation_rule_requires_two_conditions(self):
        with pytest.raises(ValueError, match="Correlation rules require at least two conditions"):
            RuleDefinition(
                rule_id="TEST",
                name="Test",
                description="Test",
                rule_type=RuleType.CORRELATION,
                conditions=[RuleCondition(
                    sensor_name="test",
                    operator=ThresholdOperator.GREATER_THAN,
                    threshold=10.0
                )],
                explanation_template="Test"
            )

    def test_composite_rule_requires_references(self):
        with pytest.raises(ValueError, match="Composite rules require referenced_rule_ids"):
            RuleDefinition(
                rule_id="TEST",
                name="Test",
                description="Test",
                rule_type=RuleType.COMPOSITE,
                explanation_template="Test"
            )

    def test_confidence_rounding(self):
        rule = RuleDefinition(
            rule_id="TEST",
            name="Test",
            description="Test",
            rule_type=RuleType.THRESHOLD,
            confidence=0.777,
            conditions=[
                RuleCondition(
                    sensor_name="test",
                    operator=ThresholdOperator.GREATER_THAN,
                    threshold=10.0
                )
            ],
            explanation_template="Test"
        )
        assert rule.confidence == 0.78

    def test_priority_validation(self):
        with pytest.raises(ValueError):
            RuleDefinition(
                rule_id="TEST",
                name="Test",
                description="Test",
                rule_type=RuleType.THRESHOLD,
                priority=15,
                conditions=[
                    RuleCondition(
                        sensor_name="test",
                        operator=ThresholdOperator.GREATER_THAN,
                        threshold=10.0
                    )
                ],
                explanation_template="Test"
            )


class TestRuleFinding:
    """Test RuleFinding model."""

    def test_finding_creation(self):
        finding = RuleFinding(
            rule_id="TEST_RULE",
            rule_name="Test Rule",
            rule_type=RuleType.THRESHOLD,
            severity=RuleSeverity.HIGH,
            priority=2,
            confidence=0.9,
            summary="Test finding",
            explanation="Test explanation",
            observed_values={"coolant_temp_c": 110.0},
            expected_values={"coolant_temp_c": 100.0},
            evidence=["Temp > 100"],
            recommended_checks=["Check coolant"],
            recommended_actions=["Replace thermostat"],
            safety_notes=["Hot coolant burns"]
        )
        assert finding.rule_id == "TEST_RULE"
        assert finding.confidence == 0.9
        assert finding.status == RuleStatus.TRIGGERED

    def test_finding_confidence_rounding(self):
        finding = RuleFinding(
            rule_id="TEST",
            rule_name="Test",
            rule_type=RuleType.THRESHOLD,
            severity=RuleSeverity.MEDIUM,
            priority=5,
            confidence=0.555,
            summary="Test",
            explanation="Test"
        )
        assert finding.confidence == 0.56


class TestRuleEvaluationResult:
    """Test RuleEvaluationResult model."""

    def test_evaluation_result(self):
        result = RuleEvaluationResult(
            rules_evaluated=10,
            rules_skipped=2,
            rules_failed=1,
            findings=[],
            data_source=DataSource.SIMULATION
        )
        assert result.rules_evaluated == 10
        assert result.get_critical_findings() == []
        assert result.has_critical_findings() is False


class TestCalculateConfidence:
    """Test confidence calculation."""

    def test_full_confidence(self):
        conf = calculate_confidence(
            sensor_valid=True,
            data_fresh=True,
            sample_count=10,
            min_samples=5,
            condition_complete=True,
            rule_reliability=0.9,
            evidence_quality=0.9
        )
        assert 0.8 <= conf <= 1.0

    def test_missing_sensor_reduces_confidence(self):
        conf = calculate_confidence(
            sensor_valid=False,
            data_fresh=True,
            sample_count=10,
            min_samples=5,
            condition_complete=True,
            rule_reliability=0.9,
            evidence_quality=0.9
        )
        assert conf < 0.8

    def test_insufficient_samples(self):
        conf = calculate_confidence(
            sensor_valid=True,
            data_fresh=True,
            sample_count=2,
            min_samples=5,
            condition_complete=True,
            rule_reliability=0.9,
            evidence_quality=0.9
        )
        assert conf < 0.8


class TestEscalateSeverity:
    """Test severity escalation."""

    def test_no_escalation_without_findings(self):
        sev = escalate_severity(RuleSeverity.MEDIUM, [])
        assert sev == RuleSeverity.MEDIUM

    def test_escalation_with_high_findings(self):
        findings = [
            RuleFinding(
                rule_id="R1", rule_name="R1", rule_type=RuleType.THRESHOLD,
                severity=RuleSeverity.HIGH, priority=2, confidence=0.9,
                summary="", explanation=""
            ),
            RuleFinding(
                rule_id="R2", rule_name="R2", rule_type=RuleType.THRESHOLD,
                severity=RuleSeverity.HIGH, priority=2, confidence=0.9,
                summary="", explanation=""
            )
        ]
        sev = escalate_severity(RuleSeverity.MEDIUM, findings)
        assert sev == RuleSeverity.HIGH

    def test_escalation_with_medium_findings(self):
        findings = [
            RuleFinding(
                rule_id=f"R{i}", rule_name=f"R{i}", rule_type=RuleType.THRESHOLD,
                severity=RuleSeverity.MEDIUM, priority=5, confidence=0.8,
                summary="", explanation=""
            )
            for i in range(3)
        ]
        sev = escalate_severity(RuleSeverity.LOW, findings)
        assert sev == RuleSeverity.MEDIUM


class TestRuleLoadResult:
    """Test RuleLoadResult model."""

    def test_load_result(self):
        result = RuleLoadResult(
            loaded_count=5,
            skipped_count=1,
            error_count=0,
            rules=[]
        )
        assert result.loaded_count == 5
        assert result.get_enabled_rules() == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""
i20 AI Garage - Rule Context Tests

Tests for the rule context building and serialization.
"""

import pytest
from datetime import datetime
from services.rule_context import RuleContext, RuleContextBuilder, RuleContextSerializer
from services.rule_models import (
    RuleFinding, RuleEvaluationResult, RuleType, RuleSeverity,
    RuleStatus, DataSource
)
from services.types import SensorReading, DTC
from services.diagnostic_models import VehicleProfile


class TestRuleContextBuilder:
    """Test RuleContextBuilder."""

    def setup_method(self):
        self.builder = RuleContextBuilder()

    def test_build_context_empty(self):
        """Test building context from empty evaluation."""
        eval_result = RuleEvaluationResult(
            evaluation_id="eval_test",
            timestamp=datetime.now(),
            rules_evaluated=0,
            data_source=DataSource.SIMULATION
        )

        context = self.builder.build_context(eval_result)

        assert context.evaluation_id == "eval_test"
        assert context.total_rules_evaluated == 0
        assert context.total_findings == 0
        assert context.critical_findings_count == 0

    def test_build_context_with_findings(self):
        """Test building context with findings of various severities."""
        findings = [
            RuleFinding(
                rule_id="CRITICAL_RULE",
                rule_name="Critical Rule",
                rule_type=RuleType.THRESHOLD,
                severity=RuleSeverity.CRITICAL,
                priority=1,
                confidence=0.95,
                status=RuleStatus.TRIGGERED,
                summary="Critical issue",
                explanation="Critical explanation",
                observed_values={"sensor_a": 100.0},
                expected_values={"sensor_a": 50.0},
                evidence=["Evidence 1"],
                recommended_checks=["Check A"],
                recommended_actions=["Action A"],
                safety_notes=["Safety A"],
                dtc_hints=["P0001"],
                data_source=DataSource.SIMULATION
            ),
            RuleFinding(
                rule_id="HIGH_RULE",
                rule_name="High Rule",
                rule_type=RuleType.THRESHOLD,
                severity=RuleSeverity.HIGH,
                priority=2,
                confidence=0.9,
                status=RuleStatus.TRIGGERED,
                summary="High issue",
                explanation="High explanation",
                observed_values={"sensor_b": 200.0},
                evidence=["Evidence 2"],
                data_source=DataSource.SIMULATION
            ),
            RuleFinding(
                rule_id="MEDIUM_RULE",
                rule_name="Medium Rule",
                rule_type=RuleType.TREND,
                severity=RuleSeverity.MEDIUM,
                priority=5,
                confidence=0.8,
                status=RuleStatus.TRIGGERED,
                summary="Medium issue",
                explanation="Medium explanation",
                data_source=DataSource.SIMULATION
            ),
            RuleFinding(
                rule_id="LOW_RULE",
                rule_name="Low Rule",
                rule_type=RuleType.CORRELATION,
                severity=RuleSeverity.LOW,
                priority=8,
                confidence=0.7,
                status=RuleStatus.TRIGGERED,
                summary="Low issue",
                explanation="Low explanation",
                data_source=DataSource.SIMULATION
            )
        ]

        eval_result = RuleEvaluationResult(
            evaluation_id="eval_test",
            timestamp=datetime.now(),
            rules_evaluated=10,
            findings=findings,
            data_source=DataSource.SIMULATION,
            execution_duration_ms=15.5
        )

        context = self.builder.build_context(eval_result)

        assert context.total_rules_evaluated == 10
        assert context.total_findings == 4
        assert context.critical_findings_count == 1
        assert context.high_findings_count == 1
        assert context.medium_findings_count == 1
        assert context.low_findings_count == 1
        assert context.execution_duration_ms == 15.5

        # Check sensor values collected
        assert "sensor_a" in context.observed_sensor_values
        assert "sensor_b" in context.observed_sensor_values
        assert context.observed_sensor_values["sensor_a"] == 100.0

        # Check evidence collected
        assert "Evidence 1" in context.all_evidence
        assert "Evidence 2" in context.all_evidence

        # Check recommendations collected
        assert "Check A" in context.all_recommended_checks
        assert "Action A" in context.all_recommended_actions

        # Check safety notes
        assert "Safety A" in context.all_safety_notes

        # Check DTC hints
        assert "P0001" in context.dtc_hints

        # Check triggered rules
        assert "CRITICAL_RULE" in context.triggered_rules
        assert "HIGH_RULE" in context.triggered_rules
        assert "MEDIUM_RULE" in context.triggered_rules
        assert "LOW_RULE" in context.triggered_rules

    def test_build_context_with_readings_and_dtcs(self):
        """Test building context with current readings and DTCs."""
        findings = [
            RuleFinding(
                rule_id="TEST_RULE",
                rule_name="Test Rule",
                rule_type=RuleType.THRESHOLD,
                severity=RuleSeverity.HIGH,
                priority=2,
                confidence=0.9,
                status=RuleStatus.TRIGGERED,
                summary="Test",
                explanation="Test",
                observed_values={"coolant_temp_c": 110.0},
                evidence=["Temp > 105"],
                data_source=DataSource.SIMULATION
            )
        ]

        eval_result = RuleEvaluationResult(
            evaluation_id="eval_test",
            timestamp=datetime.now(),
            rules_evaluated=1,
            findings=findings,
            data_source=DataSource.SIMULATION
        )

        current_readings = {
            "coolant_temp_c": SensorReading(pid="coolant_temp_c", name="coolant_temp_c", value=110.0, unit="°C", timestamp=datetime.now(), is_simulated=True),
            "engine_rpm": SensorReading(pid="engine_rpm", name="engine_rpm", value=800, unit="RPM", timestamp=datetime.now(), is_simulated=True),
            "vehicle_speed_kmh": SensorReading(pid="vehicle_speed_kmh", name="vehicle_speed_kmh", value=0, unit="km/h", timestamp=datetime.now(), is_simulated=True)
        }

        active_dtcs = [
            DTC(code="P0217", description="Engine Overheat", severity="high", status="active"),
            DTC(code="P0128", description="Coolant Thermostat", severity="medium", status="pending")
        ]

        vehicle_profile = VehicleProfile(vin="TESTVIN123", make="Hyundai", model="i20", year=2020)

        context = self.builder.build_context(
            eval_result,
            current_readings=current_readings,
            active_dtcs=active_dtcs,
            vehicle_profile=vehicle_profile
        )

        # Check readings included
        assert "coolant_temp_c" in context.observed_sensor_values
        assert "engine_rpm" in context.observed_sensor_values
        assert "vehicle_speed_kmh" in context.observed_sensor_values

        # Check DTC hints included
        assert "P0217" in context.dtc_hints
        assert "P0128" in context.dtc_hints

    def test_deduplication(self):
        """Test that lists are deduplicated."""
        findings = [
            RuleFinding(
                rule_id="RULE_1",
                rule_name="Rule 1",
                rule_type=RuleType.THRESHOLD,
                severity=RuleSeverity.HIGH,
                priority=2,
                confidence=0.9,
                status=RuleStatus.TRIGGERED,
                summary="Test",
                explanation="Test",
                evidence=["Duplicate Evidence", "Duplicate Evidence"],
                recommended_checks=["Duplicate Check", "Duplicate Check"],
                recommended_actions=["Duplicate Action", "Duplicate Action"],
                safety_notes=["Duplicate Safety", "Duplicate Safety"],
                dtc_hints=["P0001", "P0001"],
                data_source=DataSource.SIMULATION
            )
        ]

        eval_result = RuleEvaluationResult(
            evaluation_id="eval_test",
            timestamp=datetime.now(),
            rules_evaluated=1,
            findings=findings,
            data_source=DataSource.SIMULATION
        )

        context = self.builder.build_context(eval_result)

        assert context.all_evidence.count("Duplicate Evidence") == 1
        assert context.all_recommended_checks.count("Duplicate Check") == 1
        assert context.all_recommended_actions.count("Duplicate Action") == 1
        assert context.all_safety_notes.count("Duplicate Safety") == 1
        assert context.dtc_hints.count("P0001") == 1

    def test_format_for_ai(self):
        """Test AI formatting."""
        findings = [
            RuleFinding(
                rule_id="CRITICAL_RULE",
                rule_name="Critical Rule",
                rule_type=RuleType.THRESHOLD,
                severity=RuleSeverity.CRITICAL,
                priority=1,
                confidence=0.95,
                status=RuleStatus.TRIGGERED,
                summary="Critical issue",
                explanation="Critical explanation",
                observed_values={"sensor_a": 100.0},
                evidence=["Evidence 1", "Evidence 2"],
                data_source=DataSource.SIMULATION
            )
        ]

        eval_result = RuleEvaluationResult(
            evaluation_id="eval_test",
            timestamp=datetime.now(),
            rules_evaluated=5,
            findings=findings,
            data_source=DataSource.SIMULATION,
            execution_duration_ms=10.0
        )

        context = self.builder.build_context(eval_result)
        ai_text = self.builder.format_for_ai(context)

        assert "DETERMINISTIC RULE ENGINE FINDINGS" in ai_text
        assert "eval_test" in ai_text
        assert "CRITICAL" in ai_text
        assert "Critical Rule" in ai_text
        assert "Evidence 1" in ai_text
        assert "END RULE ENGINE FINDINGS" in ai_text

    def test_format_summary(self):
        """Test summary formatting for UI."""
        # No findings
        eval_result = RuleEvaluationResult(
            evaluation_id="eval_test",
            timestamp=datetime.now(),
            rules_evaluated=5,
            findings=[],
            data_source=DataSource.SIMULATION
        )

        context = self.builder.build_context(eval_result)
        summary = self.builder.format_summary(context)

        assert "No abnormalities detected" in summary

        # With findings
        findings = [
            RuleFinding(
                rule_id="RULE_1", rule_name="Rule 1", rule_type=RuleType.THRESHOLD,
                severity=RuleSeverity.CRITICAL, priority=1, confidence=0.9,
                status=RuleStatus.TRIGGERED, summary="", explanation="",
                data_source=DataSource.SIMULATION
            ),
            RuleFinding(
                rule_id="RULE_2", rule_name="Rule 2", rule_type=RuleType.THRESHOLD,
                severity=RuleSeverity.HIGH, priority=2, confidence=0.9,
                status=RuleStatus.TRIGGERED, summary="", explanation="",
                data_source=DataSource.SIMULATION
            )
        ]

        eval_result = RuleEvaluationResult(
            evaluation_id="eval_test",
            timestamp=datetime.now(),
            rules_evaluated=5,
            findings=findings,
            data_source=DataSource.SIMULATION
        )

        context = self.builder.build_context(eval_result)
        summary = self.builder.format_summary(context)

        assert "🔴 1 Critical" in summary
        assert "🟠 1 High" in summary


class TestRuleContextSerializer:
    """Test RuleContextSerializer."""

    def test_context_to_dict(self):
        """Test context serialization to dict."""
        context = RuleContext(
            evaluation_id="eval_test",
            timestamp=datetime.now(),
            total_rules_evaluated=5,
            total_findings=2,
            critical_findings_count=1,
            high_findings_count=1,
            data_source=DataSource.SIMULATION,
            triggered_rules=["RULE_1", "RULE_2"],
            observed_sensor_values={"sensor_a": 100.0},
            all_evidence=["Evidence 1"],
            dtc_hints=["P0001"],
            execution_duration_ms=15.0
        )

        data = RuleContextSerializer.to_dict(context)

        assert data["evaluation_id"] == "eval_test"
        assert data["total_rules_evaluated"] == 5
        assert data["total_findings"] == 2
        assert data["critical_findings_count"] == 1
        assert data["data_source"] == "simulation"
        assert data["triggered_rules"] == ["RULE_1", "RULE_2"]
        assert data["observed_sensor_values"]["sensor_a"] == 100.0

    def test_context_to_json(self):
        """Test context serialization to JSON."""
        context = RuleContext(
            evaluation_id="eval_test",
            timestamp=datetime.now(),
            total_rules_evaluated=5,
            data_source=DataSource.SIMULATION
        )

        json_str = RuleContextSerializer.to_json(context)

        assert "eval_test" in json_str
        assert "simulation" in json_str

    def test_finding_to_dict(self):
        """Test finding serialization to dict."""
        finding = RuleFinding(
            rule_id="TEST_RULE",
            rule_name="Test Rule",
            rule_type=RuleType.THRESHOLD,
            timestamp=datetime.now(),
            severity=RuleSeverity.HIGH,
            priority=2,
            confidence=0.9,
            status=RuleStatus.TRIGGERED,
            summary="Test summary",
            explanation="Test explanation",
            observed_values={"sensor_a": 100.0},
            expected_values={"sensor_a": 50.0},
            evidence=["Evidence 1"],
            missing_data=["sensor_b"],
            recommended_checks=["Check A"],
            recommended_actions=["Action A"],
            safety_notes=["Safety A"],
            data_source=DataSource.SIMULATION,
            diagnostic_session_id="session_123",
            rule_source="generic_obd",
            dtc_hints=["P0001"],
            evaluation_duration_ms=5.0
        )

        data = RuleContextSerializer.finding_to_dict(finding)

        assert data["rule_id"] == "TEST_RULE"
        assert data["rule_name"] == "Test Rule"
        assert data["rule_type"] == "threshold"
        assert data["severity"] == "high"
        assert data["confidence"] == 0.9
        assert data["status"] == "triggered"
        assert data["summary"] == "Test summary"
        assert data["observed_values"]["sensor_a"] == 100.0
        assert data["evidence"] == ["Evidence 1"]
        assert data["dtc_hints"] == ["P0001"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
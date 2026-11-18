"""
i20 AI Garage - Rule Evaluator Tests

Tests for the rule evaluation engine with all 4 evaluator types.
"""

import pytest
from datetime import datetime, timedelta
from services.rule_evaluator import (
    SensorHistory, ThresholdEvaluator, TrendEvaluator,
    CorrelationEvaluator, CompositeEvaluator, RuleEvaluator
)
from services.rule_models import (
    RuleDefinition, RuleCondition, RuleType, RuleSeverity,
    RuleStatus, DataSource, LogicalOperator, ThresholdOperator,
    TrendOperator, MissingDataPolicy
)
from services.types import SensorReading


def make_reading(name: str, value: float, unit: str = "", is_simulated: bool = True) -> SensorReading:
    """Helper to create SensorReading with correct interface."""
    return SensorReading(
        pid=name,
        name=name,
        value=value,
        unit=unit,
        timestamp=datetime.now(),
        is_simulated=is_simulated
    )


def make_reading_ts(name: str, value: float, unit: str, ts: datetime, is_simulated: bool = True) -> SensorReading:
    """Helper to create SensorReading with specific timestamp."""
    return SensorReading(
        pid=name,
        name=name,
        value=value,
        unit=unit,
        timestamp=ts,
        is_simulated=is_simulated
    )


class TestSensorHistory:
    """Test SensorHistory class."""

    def test_add_reading(self):
        history = SensorHistory()
        reading = make_reading("coolant_temp_c", 90.0, "°C")
        history.add_reading(reading)
        assert len(history.readings) == 1

    def test_get_values(self):
        history = SensorHistory()
        now = datetime.now()

        for i in range(5):
            reading = make_reading_ts("coolant_temp_c", 80.0 + i, "°C", now - timedelta(seconds=60 - i * 10))
            history.add_reading(reading)

        values = history.get_values("coolant_temp_c", window_seconds=120)
        assert len(values) == 5
        assert values == [80.0, 81.0, 82.0, 83.0, 84.0]

    def test_has_sufficient_data(self):
        history = SensorHistory()
        now = datetime.now()

        for i in range(3):
            reading = make_reading_ts("coolant_temp_c", 80.0 + i, "°C", now - timedelta(seconds=30 - i * 10))
            history.add_reading(reading)

        assert history.has_sufficient_data("coolant_temp_c", min_samples=3, window_seconds=60)
        assert not history.has_sufficient_data("coolant_temp_c", min_samples=5, window_seconds=60)

    def test_calculate_trend_rate(self):
        history = SensorHistory()
        now = datetime.now()

        # Create readings with a known slope (1°C per second)
        for i in range(10):
            reading = make_reading_ts("coolant_temp_c", 80.0 + i * 1.0, "°C", now - timedelta(seconds=10 - i))
            history.add_reading(reading)

        rate = history.calculate_trend_rate("coolant_temp_c", window_seconds=15)
        # Should be approximately 1.0 (1°C per second)
        assert rate is not None
        assert 0.8 < rate < 1.2

    def test_calculate_moving_average(self):
        history = SensorHistory()
        now = datetime.now()

        for i in range(5):
            reading = make_reading_ts("coolant_temp_c", 90.0, "°C", now - timedelta(seconds=10 - i * 2))
            history.add_reading(reading)

        avg = history.calculate_moving_average("coolant_temp_c", window_seconds=20)
        assert avg == 90.0

    def test_prune_old_readings(self):
        history = SensorHistory(max_age_seconds=60)
        now = datetime.now()

        # Old reading (should be pruned)
        old_reading = make_reading_ts("coolant_temp_c", 50.0, "°C", now - timedelta(seconds=120))
        history.add_reading(old_reading)

        # New reading
        new_reading = make_reading("coolant_temp_c", 90.0, "°C")
        history.add_reading(new_reading)

        # Old reading should be pruned
        assert len(history.readings) == 1
        assert history.readings[0].value == 90.0


class TestThresholdEvaluator:
    """Test ThresholdEvaluator."""

    def setup_method(self):
        self.history = SensorHistory()
        self.evaluator = ThresholdEvaluator(self.history)
        self.evaluator.data_source = DataSource.SIMULATION

    def test_evaluate_greater_than(self):
        rule = RuleDefinition(
            rule_id="TEST",
            name="Test",
            description="Test",
            rule_type=RuleType.THRESHOLD,
            conditions=[
                RuleCondition(
                    sensor_name="coolant_temp_c",
                    sensor_unit="°C",
                    operator=ThresholdOperator.GREATER_THAN,
                    threshold=100.0
                )
            ],
            explanation_template="Test"
        )

        readings = {
            "coolant_temp_c": make_reading("coolant_temp_c", 105.0, "°C")
        }

        matched, results, observed = self.evaluator.evaluate(rule, readings)
        assert matched is True
        assert results[0].passed is True
        assert results[0].observed_value == 105.0

    def test_evaluate_less_than(self):
        rule = RuleDefinition(
            rule_id="TEST",
            name="Test",
            description="Test",
            rule_type=RuleType.THRESHOLD,
            conditions=[
                RuleCondition(
                    sensor_name="coolant_temp_c",
                    sensor_unit="°C",
                    operator=ThresholdOperator.LESS_THAN,
                    threshold=80.0
                )
            ],
            explanation_template="Test"
        )

        readings = {
            "coolant_temp_c": make_reading("coolant_temp_c", 75.0, "°C")
        }

        matched, results, observed = self.evaluator.evaluate(rule, readings)
        assert matched is True
        assert results[0].passed is True

    def test_evaluate_between(self):
        rule = RuleDefinition(
            rule_id="TEST",
            name="Test",
            description="Test",
            rule_type=RuleType.THRESHOLD,
            conditions=[
                RuleCondition(
                    sensor_name="coolant_temp_c",
                    sensor_unit="°C",
                    operator=ThresholdOperator.BETWEEN,
                    threshold_min=80.0,
                    threshold_max=100.0
                )
            ],
            explanation_template="Test"
        )

        # Within range
        readings = {
            "coolant_temp_c": make_reading("coolant_temp_c", 90.0, "°C")
        }

        matched, results, observed = self.evaluator.evaluate(rule, readings)
        assert matched is True

        # Outside range (below)
        readings["coolant_temp_c"].value = 70.0
        matched, results, observed = self.evaluator.evaluate(rule, readings)
        assert matched is False

    def test_evaluate_missing_sensor_with_policy(self):
        rule = RuleDefinition(
            rule_id="TEST",
            name="Test",
            description="Test",
            rule_type=RuleType.THRESHOLD,
            conditions=[
                RuleCondition(
                    sensor_name="missing_sensor",
                    sensor_unit="°C",
                    operator=ThresholdOperator.GREATER_THAN,
                    threshold=100.0,
                    missing_data_policy=MissingDataPolicy.TREAT_AS_NORMAL,
                    default_value=90.0
                )
            ],
            explanation_template="Test"
        )

        readings = {}

        matched, results, observed = self.evaluator.evaluate(rule, readings)
        assert matched is False  # 90 < 100
        assert results[0].missing_data is True

    def test_evaluate_optional_condition(self):
        rule = RuleDefinition(
            rule_id="TEST",
            name="Test",
            description="Test",
            rule_type=RuleType.THRESHOLD,
            conditions=[
                RuleCondition(
                    sensor_name="required_sensor",
                    operator=ThresholdOperator.GREATER_THAN,
                    threshold=100.0
                ),
                RuleCondition(
                    sensor_name="optional_sensor",
                    operator=ThresholdOperator.GREATER_THAN,
                    threshold=100.0,
                    optional=True
                )
            ],
            explanation_template="Test"
        )

        # Required fails, optional missing
        readings = {
            "required_sensor": make_reading("required_sensor", 50.0)
        }

        matched, results, observed = self.evaluator.evaluate(rule, readings)
        assert matched is False  # Required condition failed

    def test_evaluate_logical_groups(self):
        rule = RuleDefinition(
            rule_id="TEST",
            name="Test",
            description="Test",
            rule_type=RuleType.THRESHOLD,
            conditions=[
                RuleCondition(
                    sensor_name="sensor_a",
                    operator=ThresholdOperator.GREATER_THAN,
                    threshold=50.0,
                    condition_group="group1",
                    logical_operator=LogicalOperator.AND
                ),
                RuleCondition(
                    sensor_name="sensor_b",
                    operator=ThresholdOperator.GREATER_THAN,
                    threshold=50.0,
                    condition_group="group1",
                    logical_operator=LogicalOperator.AND
                ),
                RuleCondition(
                    sensor_name="sensor_c",
                    operator=ThresholdOperator.GREATER_THAN,
                    threshold=50.0,
                    condition_group="group2",
                    logical_operator=LogicalOperator.OR
                ),
                RuleCondition(
                    sensor_name="sensor_d",
                    operator=ThresholdOperator.GREATER_THAN,
                    threshold=50.0,
                    condition_group="group2",
                    logical_operator=LogicalOperator.OR
                )
            ],
            explanation_template="Test"
        )

        # Both group1 pass, one group2 passes
        readings = {
            "sensor_a": make_reading("sensor_a", 60.0),
            "sensor_b": make_reading("sensor_b", 60.0),
            "sensor_c": make_reading("sensor_c", 40.0),
            "sensor_d": make_reading("sensor_d", 60.0),
        }

        matched, results, observed = self.evaluator.evaluate(rule, readings)
        assert matched is True  # group1 AND, group2 OR

        # Group1 fails
        readings["sensor_a"].value = 40.0
        matched, results, observed = self.evaluator.evaluate(rule, readings)
        assert matched is False


class TestTrendEvaluator:
    """Test TrendEvaluator."""

    def setup_method(self):
        self.history = SensorHistory()
        self.evaluator = TrendEvaluator(self.history)
        self.evaluator.data_source = DataSource.SIMULATION

    def test_evaluate_rate_above(self):
        now = datetime.now()
        # Add readings with increasing trend (2°C per second)
        for i in range(10):
            reading = make_reading_ts("coolant_temp_c", 80.0 + i * 2.0, "°C", now - timedelta(seconds=10 - i))
            self.history.add_reading(reading)

        rule = RuleDefinition(
            rule_id="TEST",
            name="Test",
            description="Test",
            rule_type=RuleType.TREND,
            conditions=[
                RuleCondition(
                    sensor_name="coolant_temp_c",
                    sensor_unit="°C",
                    trend_operator=TrendOperator.RATE_ABOVE,
                    trend_window_seconds=15,
                    min_samples=5,
                    rate_threshold=1.0
                )
            ],
            explanation_template="Test"
        )

        readings = {
            "coolant_temp_c": make_reading_ts("coolant_temp_c", 100.0, "°C", now)
        }

        matched, results, observed = self.evaluator.evaluate(rule, readings)
        assert matched is True
        assert results[0].trend_rate is not None
        assert results[0].trend_rate > 1.0

    def test_evaluate_sustained_above(self):
        now = datetime.now()
        # All readings above threshold
        for i in range(5):
            reading = make_reading_ts("coolant_temp_c", 105.0, "°C", now - timedelta(seconds=10 - i * 2))
            self.history.add_reading(reading)

        rule = RuleDefinition(
            rule_id="TEST",
            name="Test",
            description="Test",
            rule_type=RuleType.TREND,
            conditions=[
                RuleCondition(
                    sensor_name="coolant_temp_c",
                    sensor_unit="°C",
                    trend_operator=TrendOperator.SUSTAINED_ABOVE,
                    trend_window_seconds=15,
                    min_samples=5,
                    rate_threshold=100.0
                )
            ],
            explanation_template="Test"
        )

        readings = {
            "coolant_temp_c": make_reading_ts("coolant_temp_c", 105.0, "°C", now)
        }

        matched, results, observed = self.evaluator.evaluate(rule, readings)
        assert matched is True

    def test_evaluate_moving_average_above(self):
        now = datetime.now()
        # Average of 5 readings = 105.0
        for i in range(5):
            reading = make_reading_ts("coolant_temp_c", 105.0, "°C", now - timedelta(seconds=10 - i * 2))
            self.history.add_reading(reading)

        rule = RuleDefinition(
            rule_id="TEST",
            name="Test",
            description="Test",
            rule_type=RuleType.TREND,
            conditions=[
                RuleCondition(
                    sensor_name="coolant_temp_c",
                    sensor_unit="°C",
                    trend_operator=TrendOperator.MOVING_AVERAGE_ABOVE,
                    trend_window_seconds=15,
                    min_samples=5,
                    rate_threshold=100.0
                )
            ],
            explanation_template="Test"
        )

        readings = {
            "coolant_temp_c": make_reading_ts("coolant_temp_c", 105.0, "°C", now)
        }

        matched, results, observed = self.evaluator.evaluate(rule, readings)
        assert matched is True
        assert results[0].trend_rate == 105.0  # Moving average


class TestCorrelationEvaluator:
    """Test CorrelationEvaluator."""

    def setup_method(self):
        self.history = SensorHistory()
        self.evaluator = CorrelationEvaluator(self.history)
        self.evaluator.data_source = DataSource.SIMULATION

    def test_evaluate_all_conditions_pass(self):
        rule = RuleDefinition(
            rule_id="TEST",
            name="Test",
            description="Test",
            rule_type=RuleType.CORRELATION,
            conditions=[
                RuleCondition(
                    sensor_name="sensor_a",
                    operator=ThresholdOperator.GREATER_THAN,
                    threshold=50.0
                ),
                RuleCondition(
                    sensor_name="sensor_b",
                    operator=ThresholdOperator.GREATER_THAN,
                    threshold=50.0
                )
            ],
            explanation_template="Test"
        )

        readings = {
            "sensor_a": make_reading("sensor_a", 60.0),
            "sensor_b": make_reading("sensor_b", 60.0),
        }

        matched, results, observed = self.evaluator.evaluate(rule, readings)
        assert matched is True
        assert all(r.passed for r in results)

    def test_evaluate_one_condition_fails(self):
        rule = RuleDefinition(
            rule_id="TEST",
            name="Test",
            description="Test",
            rule_type=RuleType.CORRELATION,
            conditions=[
                RuleCondition(
                    sensor_name="sensor_a",
                    operator=ThresholdOperator.GREATER_THAN,
                    threshold=50.0
                ),
                RuleCondition(
                    sensor_name="sensor_b",
                    operator=ThresholdOperator.GREATER_THAN,
                    threshold=50.0
                )
            ],
            explanation_template="Test"
        )

        readings = {
            "sensor_a": make_reading("sensor_a", 60.0),
            "sensor_b": make_reading("sensor_b", 40.0),
        }

        matched, results, observed = self.evaluator.evaluate(rule, readings)
        assert matched is False
        assert results[0].passed is True
        assert results[1].passed is False


class TestCompositeEvaluator:
    """Test CompositeEvaluator."""

    def setup_method(self):
        self.history = SensorHistory()
        self.previous_findings = {}

    def test_evaluate_all_referenced_triggered(self):
        from services.rule_models import RuleFinding

        self.previous_findings = {
            "RULE_1": RuleFinding(
                rule_id="RULE_1", rule_name="Rule 1", rule_type=RuleType.THRESHOLD,
                severity=RuleSeverity.HIGH, priority=2, confidence=0.9,
                summary="", explanation="", status=RuleStatus.TRIGGERED
            ),
            "RULE_2": RuleFinding(
                rule_id="RULE_2", rule_name="Rule 2", rule_type=RuleType.THRESHOLD,
                severity=RuleSeverity.MEDIUM, priority=4, confidence=0.8,
                summary="", explanation="", status=RuleStatus.TRIGGERED
            )
        }

        evaluator = CompositeEvaluator(self.history, self.previous_findings)
        evaluator.data_source = DataSource.SIMULATION

        rule = RuleDefinition(
            rule_id="COMPOSITE",
            name="Composite",
            description="Test",
            rule_type=RuleType.COMPOSITE,
            referenced_rule_ids=["RULE_1", "RULE_2"],
            composite_logic=LogicalOperator.AND,
            explanation_template="Test"
        )

        readings = {}
        matched, results, observed = evaluator.evaluate(rule, readings)
        assert matched is True

    def test_evaluate_one_referenced_not_triggered(self):
        from services.rule_models import RuleFinding

        self.previous_findings = {
            "RULE_1": RuleFinding(
                rule_id="RULE_1", rule_name="Rule 1", rule_type=RuleType.THRESHOLD,
                severity=RuleSeverity.HIGH, priority=2, confidence=0.9,
                summary="", explanation="", status=RuleStatus.TRIGGERED
            ),
            "RULE_2": RuleFinding(
                rule_id="RULE_2", rule_name="Rule 2", rule_type=RuleType.THRESHOLD,
                severity=RuleSeverity.MEDIUM, priority=4, confidence=0.8,
                summary="", explanation="", status=RuleStatus.NOT_TRIGGERED
            )
        }

        evaluator = CompositeEvaluator(self.history, self.previous_findings)
        evaluator.data_source = DataSource.SIMULATION

        rule = RuleDefinition(
            rule_id="COMPOSITE",
            name="Composite",
            description="Test",
            rule_type=RuleType.COMPOSITE,
            referenced_rule_ids=["RULE_1", "RULE_2"],
            composite_logic=LogicalOperator.AND,
            explanation_template="Test"
        )

        readings = {}
        matched, results, observed = evaluator.evaluate(rule, readings)
        assert matched is False

    def test_evaluate_or_logic(self):
        from services.rule_models import RuleFinding

        self.previous_findings = {
            "RULE_1": RuleFinding(
                rule_id="RULE_1", rule_name="Rule 1", rule_type=RuleType.THRESHOLD,
                severity=RuleSeverity.HIGH, priority=2, confidence=0.9,
                summary="", explanation="", status=RuleStatus.NOT_TRIGGERED
            ),
            "RULE_2": RuleFinding(
                rule_id="RULE_2", rule_name="Rule 2", rule_type=RuleType.THRESHOLD,
                severity=RuleSeverity.MEDIUM, priority=4, confidence=0.8,
                summary="", explanation="", status=RuleStatus.TRIGGERED
            )
        }

        evaluator = CompositeEvaluator(self.history, self.previous_findings)
        evaluator.data_source = DataSource.SIMULATION

        rule = RuleDefinition(
            rule_id="COMPOSITE",
            name="Composite",
            description="Test",
            rule_type=RuleType.COMPOSITE,
            referenced_rule_ids=["RULE_1", "RULE_2"],
            composite_logic=LogicalOperator.OR,
            explanation_template="Test"
        )

        readings = {}
        matched, results, observed = evaluator.evaluate(rule, readings)
        assert matched is True  # OR logic - one triggered


class TestRuleEvaluator:
    """Test main RuleEvaluator orchestrator."""

    def setup_method(self):
        self.evaluator = RuleEvaluator()
        self.evaluator.set_data_source(DataSource.SIMULATION)

    def test_evaluate_threshold_rules(self):
        rule = RuleDefinition(
            rule_id="THRESH_TEST",
            name="Threshold Test",
            description="Test",
            rule_type=RuleType.THRESHOLD,
            severity=RuleSeverity.HIGH,
            priority=2,
            confidence=0.9,
            conditions=[
                RuleCondition(
                    sensor_name="coolant_temp_c",
                    operator=ThresholdOperator.GREATER_THAN,
                    threshold=100.0
                )
            ],
            explanation_template="Coolant at {coolant_temp_c}°C"
        )

        readings = {
            "coolant_temp_c": make_reading("coolant_temp_c", 105.0, "°C")
        }

        result = self.evaluator.evaluate_rules([rule], readings)
        assert result.rules_evaluated == 1
        assert len(result.findings) == 1
        assert result.findings[0].rule_id == "THRESH_TEST"

    def test_evaluate_multiple_rules(self):
        rules = [
            RuleDefinition(
                rule_id=f"RULE_{i}",
                name=f"Rule {i}",
                description="Test",
                rule_type=RuleType.THRESHOLD,
                severity=RuleSeverity.MEDIUM,
                priority=5,
                confidence=0.8,
                conditions=[
                    RuleCondition(
                        sensor_name=f"sensor_{i}",
                        operator=ThresholdOperator.GREATER_THAN,
                        threshold=50.0
                    )
                ],
                explanation_template="Test"
            )
            for i in range(3)
        ]

        readings = {
            f"sensor_{i}": make_reading(f"sensor_{i}", 60.0)
            for i in range(3)
        }

        result = self.evaluator.evaluate_rules(rules, readings)
        assert result.rules_evaluated == 3
        assert len(result.findings) == 3

    def test_disabled_rule_skipped(self):
        rule = RuleDefinition(
            rule_id="DISABLED_RULE",
            name="Disabled Rule",
            description="Test",
            rule_type=RuleType.THRESHOLD,
            enabled=False,
            conditions=[
                RuleCondition(
                    sensor_name="sensor_a",
                    operator=ThresholdOperator.GREATER_THAN,
                    threshold=50.0
                )
            ],
            explanation_template="Test"
        )

        readings = {
            "sensor_a": make_reading("sensor_a", 60.0)
        }

        result = self.evaluator.evaluate_rules([rule], readings)
        assert result.rules_evaluated == 0
        assert result.rules_skipped == 1

    def test_priority_ordering(self):
        rule_low = RuleDefinition(
            rule_id="LOW_PRIORITY",
            name="Low Priority",
            description="Test",
            rule_type=RuleType.THRESHOLD,
            priority=10,
            conditions=[
                RuleCondition(sensor_name="sensor_a", operator=ThresholdOperator.GREATER_THAN, threshold=50.0)
            ],
            explanation_template="Test"
        )

        rule_high = RuleDefinition(
            rule_id="HIGH_PRIORITY",
            name="High Priority",
            description="Test",
            rule_type=RuleType.THRESHOLD,
            priority=1,
            conditions=[
                RuleCondition(sensor_name="sensor_a", operator=ThresholdOperator.GREATER_THAN, threshold=50.0)
            ],
            explanation_template="Test"
        )

        readings = {
            "sensor_a": make_reading("sensor_a", 60.0)
        }

        result = self.evaluator.evaluate_rules([rule_low, rule_high], readings)
        # High priority (1) should be evaluated first
        # Both should trigger
        assert len(result.findings) == 2

    def test_cooldown_prevents_duplicate(self):
        rule = RuleDefinition(
            rule_id="COOLDOWN_TEST",
            name="Cooldown Test",
            description="Test",
            rule_type=RuleType.THRESHOLD,
            cooldown_seconds=60,
            conditions=[
                RuleCondition(sensor_name="sensor_a", operator=ThresholdOperator.GREATER_THAN, threshold=50.0)
            ],
            explanation_template="Test"
        )

        readings = {
            "sensor_a": make_reading("sensor_a", 60.0)
        }

        # First evaluation
        result1 = self.evaluator.evaluate_rules([rule], readings)
        assert len(result1.findings) == 1

        # Second evaluation immediately (should be in cooldown)
        result2 = self.evaluator.evaluate_rules([rule], readings)
        assert len(result2.findings) == 0
        assert result2.rules_skipped == 1

    def test_data_source_propagation(self):
        rule = RuleDefinition(
            rule_id="SOURCE_TEST",
            name="Source Test",
            description="Test",
            rule_type=RuleType.THRESHOLD,
            conditions=[
                RuleCondition(sensor_name="sensor_a", operator=ThresholdOperator.GREATER_THAN, threshold=50.0)
            ],
            explanation_template="Test"
        )

        readings = {
            "sensor_a": make_reading("sensor_a", 60.0, is_simulated=False)
        }

        self.evaluator.set_data_source(DataSource.REAL)
        result = self.evaluator.evaluate_rules([rule], readings)

        assert result.data_source == DataSource.REAL
        assert result.findings[0].data_source == DataSource.REAL


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
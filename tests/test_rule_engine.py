"""
i20 AI Garage - Rule Engine Tests

Tests for the main RuleEngine orchestrator.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import yaml

from services.rule_engine import RuleEngine, get_rule_engine, create_default_rules_directory
from services.rule_models import (
    RuleDefinition, RuleCondition, RuleType, RuleSeverity,
    RuleStatus, DataSource, ThresholdOperator
)
from services.types import SensorReading, DTC
from services.diagnostic_models import VehicleProfile


class TestRuleEngine:
    """Test RuleEngine class."""

    def setup_method(self):
        """Create a temporary rules directory for each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.rules_dir = Path(self.temp_dir.name)

        # Create a simple test rule file
        rule_file = self.rules_dir / "test_rules.yaml"
        rule_data = {
            "rules": [{
                "rule_id": "TEST_COOLANT_OVERHEAT",
                "name": "Test Coolant Overheat",
                "description": "Test rule for coolant overheat",
                "category": "cooling",
                "rule_type": "threshold",
                "enabled": True,
                "severity": "high",
                "priority": 2,
                "confidence": 0.9,
                "conditions": [{
                    "sensor_name": "coolant_temp_c",
                    "sensor_unit": "°C",
                    "operator": "greater_than",
                    "threshold": 100.0
                }],
                "explanation_template": "Coolant at {coolant_temp_c}°C",
                "recommended_checks": ["Check coolant level"],
                "recommended_actions": ["Replace thermostat"],
                "safety_notes": ["Hot coolant burns"],
                "source": "generic_obd",
                "dtc_hints": ["P0217"],
                "cooldown_seconds": 60
            }]
        }
        with open(rule_file, 'w') as f:
            yaml.dump(rule_data, f)

    def teardown_method(self):
        self.temp_dir.cleanup()
        # Reset singleton properly
        RuleEngine.reset_instance()

    def test_engine_initialization(self):
        """Test RuleEngine initializes and loads rules."""
        engine = RuleEngine(rules_dir=self.rules_dir)

        rules = engine.get_all_rules()
        assert len(rules) == 1
        assert rules[0].rule_id == "TEST_COOLANT_OVERHEAT"

    def test_singleton_pattern(self):
        """Test that RuleEngine is a singleton."""
        engine1 = RuleEngine(rules_dir=self.rules_dir)
        engine2 = RuleEngine(rules_dir=self.rules_dir)

        assert engine1 is engine2

    def test_evaluate_triggered(self):
        """Test evaluation triggers a finding."""
        engine = RuleEngine(rules_dir=self.rules_dir)

        readings = {
            "coolant_temp_c": SensorReading(
                pid="coolant_temp_c", name="coolant_temp_c", value=105.0, unit="°C",
                timestamp=datetime.now(), is_simulated=True
            )
        }

        result = engine.evaluate(readings)

        assert result.rules_evaluated == 1
        assert len(result.findings) == 1
        assert result.findings[0].rule_id == "TEST_COOLANT_OVERHEAT"
        assert result.findings[0].severity == RuleSeverity.HIGH

    def test_evaluate_not_triggered(self):
        """Test evaluation doesn't trigger when below threshold."""
        engine = RuleEngine(rules_dir=self.rules_dir)

        readings = {
            "coolant_temp_c": SensorReading(
                pid="coolant_temp_c", name="coolant_temp_c", value=90.0, unit="°C",
                timestamp=datetime.now(), is_simulated=True
            )
        }

        result = engine.evaluate(readings)

        assert result.rules_evaluated == 1
        assert len(result.findings) == 0

    def test_evaluate_with_missing_sensor(self):
        """Test evaluation with missing sensor data."""
        engine = RuleEngine(rules_dir=self.rules_dir)

        readings = {}  # No coolant temp sensor

        result = engine.evaluate(readings)

        # Rule should be skipped due to missing data policy
        assert result.rules_skipped == 1
        assert len(result.findings) == 0

    def test_evaluate_cooldown(self):
        """Test cooldown prevents repeated findings."""
        engine = RuleEngine(rules_dir=self.rules_dir)

        readings = {
            "coolant_temp_c": SensorReading(
                pid="coolant_temp_c", name="coolant_temp_c", value=105.0, unit="°C",
                timestamp=datetime.now(), is_simulated=True
            )
        }

        # First evaluation
        result1 = engine.evaluate(readings)
        assert len(result1.findings) == 1

        # Second evaluation (should be in cooldown)
        result2 = engine.evaluate(readings)
        assert len(result2.findings) == 0
        assert result2.rules_skipped == 1

    def test_data_source_propagation(self):
        """Test data source is propagated to findings."""
        engine = RuleEngine(rules_dir=self.rules_dir)
        engine.set_data_source(DataSource.REAL)

        readings = {
            "coolant_temp_c": SensorReading(
                pid="coolant_temp_c", name="coolant_temp_c", value=105.0, unit="°C",
                timestamp=datetime.now(), is_simulated=False
            )
        }

        result = engine.evaluate(readings)

        assert result.data_source == DataSource.REAL
        assert result.findings[0].data_source == DataSource.REAL

    def test_get_ai_context(self):
        """Test AI context building."""
        engine = RuleEngine(rules_dir=self.rules_dir)

        readings = {
            "coolant_temp_c": SensorReading(
                pid="coolant_temp_c", name="coolant_temp_c", value=105.0, unit="°C",
                timestamp=datetime.now(), is_simulated=True
            )
        }

        result = engine.evaluate(readings)
        context = engine.get_ai_context()

        assert context is not None
        assert context.evaluation_id == result.evaluation_id
        assert context.total_findings == 1

    def test_get_ai_context_text(self):
        """Test AI context text formatting."""
        engine = RuleEngine(rules_dir=self.rules_dir)

        readings = {
            "coolant_temp_c": SensorReading(
                pid="coolant_temp_c", name="coolant_temp_c", value=105.0, unit="°C",
                timestamp=datetime.now(), is_simulated=True
            )
        }

        engine.evaluate(readings)
        ai_text = engine.get_ai_context_text()

        assert ai_text is not None
        assert "DETERMINISTIC RULE ENGINE FINDINGS" in ai_text
        assert "TEST_COOLANT_OVERHEAT" in ai_text

    def test_get_ai_context_summary(self):
        """Test AI context summary for UI."""
        engine = RuleEngine(rules_dir=self.rules_dir)

        readings = {
            "coolant_temp_c": SensorReading(
                pid="coolant_temp_c", name="coolant_temp_c", value=105.0, unit="°C",
                timestamp=datetime.now(), is_simulated=True
            )
        }

        engine.evaluate(readings)
        summary = engine.get_ai_context_summary()

        assert summary is not None
        assert "High" in summary

    def test_enable_disable_rule(self):
        """Test enabling/disabling rules."""
        engine = RuleEngine(rules_dir=self.rules_dir)

        # Disable rule
        assert engine.disable_rule("TEST_COOLANT_OVERHEAT") is True
        assert engine.get_rule("TEST_COOLANT_OVERHEAT").enabled is False

        readings = {
            "coolant_temp_c": SensorReading(
                pid="coolant_temp_c", name="coolant_temp_c", value=105.0, unit="°C",
                timestamp=datetime.now(), is_simulated=True
            )
        }

        result = engine.evaluate(readings)
        assert result.rules_skipped == 1

        # Re-enable
        assert engine.enable_rule("TEST_COOLANT_OVERHEAT") is True
        assert engine.get_rule("TEST_COOLANT_OVERHEAT").enabled is True

        result = engine.evaluate(readings)
        assert len(result.findings) == 1

    def test_get_rules_by_type(self):
        """Test filtering rules by type."""
        engine = RuleEngine(rules_dir=self.rules_dir)

        threshold_rules = engine.get_rules_by_type(RuleType.THRESHOLD)
        trend_rules = engine.get_rules_by_type(RuleType.TREND)

        assert len(threshold_rules) == 1
        assert len(trend_rules) == 0

    def test_get_rules_by_category(self):
        """Test filtering rules by category."""
        engine = RuleEngine(rules_dir=self.rules_dir)

        cooling_rules = engine.get_rules_by_category("cooling")
        fuel_rules = engine.get_rules_by_category("fuel")

        assert len(cooling_rules) == 1
        assert len(fuel_rules) == 0

    def test_get_statistics(self):
        """Test statistics retrieval."""
        engine = RuleEngine(rules_dir=self.rules_dir)

        stats = engine.get_statistics()

        assert stats["total_rules_loaded"] == 1
        assert stats["enabled_rules"] == 1
        assert stats["rules_by_type"]["threshold"] == 1
        assert stats["rules_by_category"]["cooling"] == 1
        assert stats["rules_by_severity"]["high"] == 1

    def test_add_sensor_readings(self):
        """Test adding sensor readings to history."""
        engine = RuleEngine(rules_dir=self.rules_dir)

        readings = [
            SensorReading(pid="coolant_temp_c", name="coolant_temp_c", value=90.0, unit="°C",
                         timestamp=datetime.now(), is_simulated=True),
            SensorReading(pid="engine_rpm", name="engine_rpm", value=800, unit="RPM",
                         timestamp=datetime.now(), is_simulated=True)
        ]

        engine.add_sensor_readings(readings)

        # Should have readings in history for trend analysis
        assert len(engine.evaluator.sensor_history.readings) == 2

    def test_clear_history(self):
        """Test clearing sensor history."""
        engine = RuleEngine(rules_dir=self.rules_dir)

        readings = [
            SensorReading(pid="coolant_temp_c", name="coolant_temp_c", value=90.0, unit="°C",
                         timestamp=datetime.now(), is_simulated=True)
        ]

        engine.add_sensor_readings(readings)
        assert len(engine.evaluator.sensor_history.readings) == 1

        engine.clear_history()
        assert len(engine.evaluator.sensor_history.readings) == 0

    def test_evaluate_with_diagnostic_session(self):
        """Test evaluation with diagnostic session ID."""
        engine = RuleEngine(rules_dir=self.rules_dir)

        readings = {
            "coolant_temp_c": SensorReading(
                pid="coolant_temp_c", name="coolant_temp_c", value=105.0, unit="°C",
                timestamp=datetime.now(), is_simulated=True
            )
        }

        result = engine.evaluate(
            readings,
            diagnostic_session_id="diag_session_123"
        )

        assert result.diagnostic_session_id == "diag_session_123"
        assert result.findings[0].diagnostic_session_id == "diag_session_123"


class TestGetRuleEngine:
    """Test get_rule_engine convenience function."""

    def test_get_rule_engine(self):
        """Test getting rule engine instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)
            rule_file = rules_dir / "test.yaml"
            rule_data = {
                "rules": [{
                    "rule_id": "TEST", "name": "Test", "description": "Test",
                    "category": "cooling", "rule_type": "threshold",
                    "conditions": [{"sensor_name": "s", "operator": "greater_than", "threshold": 1}],
                    "explanation_template": "Test"
                }]
            }
            with open(rule_file, 'w') as f:
                yaml.dump(rule_data, f)

            # Reset singleton properly
            RuleEngine.reset_instance()

            engine = get_rule_engine(rules_dir)
            assert isinstance(engine, RuleEngine)
            assert len(engine.get_all_rules()) == 1

            # Second call returns same instance
            engine2 = get_rule_engine(rules_dir)
            assert engine is engine2


class TestCreateDefaultRulesDirectory:
    """Test create_default_rules_directory function."""

    def test_create_default_rules_directory(self):
        """Test creating default rules directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir) / "custom_rules"

            created_dir = create_default_rules_directory(rules_dir)

            assert created_dir == rules_dir
            assert rules_dir.exists()
            assert (rules_dir / "example_rules.yaml").exists()

            # Check category files
            for cat in ["cooling", "fuel", "ignition", "emissions", "electrical", "transmission"]:
                assert (rules_dir / f"{cat}_rules.yaml").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
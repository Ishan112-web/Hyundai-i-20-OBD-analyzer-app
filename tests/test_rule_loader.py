"""
i20 AI Garage - Rule Loader Tests

Tests for the YAML rule loading functionality.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from services.rule_loader import RuleLoader, load_rules_from_directory
from services.rule_models import (
    RuleType, RuleCategory, RuleSeverity, RuleLoadResult,
    ThresholdOperator, TrendOperator, LogicalOperator, MissingDataPolicy
)


class TestRuleLoader:
    """Test RuleLoader class."""

    def test_load_valid_yaml_file(self):
        """Test loading a valid YAML rule file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)
            rule_file = rules_dir / "test_rules.yaml"

            rule_data = {
                "rules": [{
                    "rule_id": "TEST_RULE_1",
                    "name": "Test Rule 1",
                    "description": "A test threshold rule",
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
                    "explanation_template": "Temp is {coolant_temp_c}°C",
                    "recommended_checks": ["Check coolant"],
                    "recommended_actions": ["Replace thermostat"],
                    "safety_notes": ["Hot coolant burns"],
                    "source": "generic_obd",
                    "dtc_hints": ["P0217"]
                }]
            }

            with open(rule_file, 'w') as f:
                yaml.dump(rule_data, f)

            loader = RuleLoader(rules_dir)
            result = loader.load_all_rules()

            assert result.loaded_count == 1
            assert result.error_count == 0
            assert len(result.rules) == 1
            assert result.rules[0].rule_id == "TEST_RULE_1"

    def test_load_multiple_rules_in_file(self):
        """Test loading multiple rules from a single file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)
            rule_file = rules_dir / "test_rules.yaml"

            rule_data = {
                "rules": [
                    {
                        "rule_id": "RULE_1",
                        "name": "Rule 1",
                        "description": "First rule",
                        "category": "cooling",
                        "rule_type": "threshold",
                        "conditions": [{
                            "sensor_name": "sensor_a",
                            "operator": "greater_than",
                            "threshold": 10.0
                        }],
                        "explanation_template": "Test"
                    },
                    {
                        "rule_id": "RULE_2",
                        "name": "Rule 2",
                        "description": "Second rule",
                        "category": "fuel",
                        "rule_type": "threshold",
                        "conditions": [{
                            "sensor_name": "sensor_b",
                            "operator": "less_than",
                            "threshold": 5.0
                        }],
                        "explanation_template": "Test"
                    }
                ]
            }

            with open(rule_file, 'w') as f:
                yaml.dump(rule_data, f)

            loader = RuleLoader(rules_dir)
            result = loader.load_all_rules()

            assert result.loaded_count == 2
            assert len(result.rules) == 2

    def test_load_invalid_yaml(self):
        """Test handling of invalid YAML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)
            rule_file = rules_dir / "bad_rules.yaml"

            with open(rule_file, 'w') as f:
                f.write("invalid: yaml: content: [")

            loader = RuleLoader(rules_dir)
            result = loader.load_all_rules()

            assert result.error_count > 0
            assert len(result.errors) > 0

    def test_load_missing_required_fields(self):
        """Test handling of rules missing required fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)
            rule_file = rules_dir / "test_rules.yaml"

            rule_data = {
                "rules": [{
                    "name": "Test Rule",
                    "description": "Missing rule_id",
                    "category": "cooling",
                    "rule_type": "threshold",
                    "conditions": [{
                        "sensor_name": "sensor_a",
                        "operator": "greater_than",
                        "threshold": 10.0
                    }],
                    "explanation_template": "Test"
                }]
            }

            with open(rule_file, 'w') as f:
                yaml.dump(rule_data, f)

            loader = RuleLoader(rules_dir)
            result = loader.load_all_rules()

            assert result.error_count > 0

    def test_duplicate_rule_id_detection(self):
        """Test detection of duplicate rule IDs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)
            rule_file = rules_dir / "test_rules.yaml"

            rule_data = {
                "rules": [
                    {
                        "rule_id": "DUPLICATE_RULE",
                        "name": "Rule 1",
                        "description": "First",
                        "category": "cooling",
                        "rule_type": "threshold",
                        "conditions": [{
                            "sensor_name": "sensor_a",
                            "operator": "greater_than",
                            "threshold": 10.0
                        }],
                        "explanation_template": "Test"
                    },
                    {
                        "rule_id": "DUPLICATE_RULE",
                        "name": "Rule 2",
                        "description": "Second",
                        "category": "fuel",
                        "rule_type": "threshold",
                        "conditions": [{
                            "sensor_name": "sensor_b",
                            "operator": "less_than",
                            "threshold": 5.0
                        }],
                        "explanation_template": "Test"
                    }
                ]
            }

            with open(rule_file, 'w') as f:
                yaml.dump(rule_data, f)

            loader = RuleLoader(rules_dir)
            result = loader.load_all_rules()

            assert result.error_count > 0
            assert any("Duplicate rule ID" in e for e in result.errors)

    def test_get_rule_by_id(self):
        """Test retrieving a rule by ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)
            rule_file = rules_dir / "test_rules.yaml"

            rule_data = {
                "rules": [{
                    "rule_id": "GET_TEST_RULE",
                    "name": "Get Test Rule",
                    "description": "Test",
                    "category": "cooling",
                    "rule_type": "threshold",
                    "conditions": [{
                        "sensor_name": "sensor_a",
                        "operator": "greater_than",
                        "threshold": 10.0
                    }],
                    "explanation_template": "Test"
                }]
            }

            with open(rule_file, 'w') as f:
                yaml.dump(rule_data, f)

            loader = RuleLoader(rules_dir)
            loader.load_all_rules()

            rule = loader.get_rule("GET_TEST_RULE")
            assert rule is not None
            assert rule.rule_id == "GET_TEST_RULE"

            # Non-existent rule
            assert loader.get_rule("NON_EXISTENT") is None

    def test_get_rules_by_type(self):
        """Test filtering rules by type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)
            rule_file = rules_dir / "test_rules.yaml"

            rule_data = {
                "rules": [
                    {
                        "rule_id": "THRESH_RULE",
                        "name": "Threshold Rule",
                        "description": "Test",
                        "category": "cooling",
                        "rule_type": "threshold",
                        "conditions": [{
                            "sensor_name": "sensor_a",
                            "operator": "greater_than",
                            "threshold": 10.0
                        }],
                        "explanation_template": "Test"
                    },
                    {
                        "rule_id": "TREND_RULE",
                        "name": "Trend Rule",
                        "description": "Test",
                        "category": "cooling",
                        "rule_type": "trend",
                        "conditions": [{
                            "sensor_name": "sensor_b",
                            "trend_operator": "rate_above",
                            "rate_threshold": 1.0
                        }],
                        "explanation_template": "Test"
                    }
                ]
            }

            with open(rule_file, 'w') as f:
                yaml.dump(rule_data, f)

            loader = RuleLoader(rules_dir)
            loader.load_all_rules()

            threshold_rules = loader.get_rules_by_type(RuleType.THRESHOLD)
            trend_rules = loader.get_rules_by_type(RuleType.TREND)

            assert len(threshold_rules) == 1
            assert len(trend_rules) == 1
            assert threshold_rules[0].rule_id == "THRESH_RULE"
            assert trend_rules[0].rule_id == "TREND_RULE"

    def test_get_rules_by_category(self):
        """Test filtering rules by category."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)
            rule_file = rules_dir / "test_rules.yaml"

            rule_data = {
                "rules": [
                    {
                        "rule_id": "COOL_RULE",
                        "name": "Cooling Rule",
                        "description": "Test",
                        "category": "cooling",
                        "rule_type": "threshold",
                        "conditions": [{
                            "sensor_name": "sensor_a",
                            "operator": "greater_than",
                            "threshold": 10.0
                        }],
                        "explanation_template": "Test"
                    },
                    {
                        "rule_id": "FUEL_RULE",
                        "name": "Fuel Rule",
                        "description": "Test",
                        "category": "fuel",
                        "rule_type": "threshold",
                        "conditions": [{
                            "sensor_name": "sensor_b",
                            "operator": "less_than",
                            "threshold": 5.0
                        }],
                        "explanation_template": "Test"
                    }
                ]
            }

            with open(rule_file, 'w') as f:
                yaml.dump(rule_data, f)

            loader = RuleLoader(rules_dir)
            loader.load_all_rules()

            cooling_rules = loader.get_rules_by_category(RuleCategory.COOLING)
            fuel_rules = loader.get_rules_by_category(RuleCategory.FUEL)

            assert len(cooling_rules) == 1
            assert len(fuel_rules) == 1

    def test_get_enabled_rules(self):
        """Test filtering enabled rules."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)
            rule_file = rules_dir / "test_rules.yaml"

            rule_data = {
                "rules": [
                    {
                        "rule_id": "ENABLED_RULE",
                        "name": "Enabled Rule",
                        "description": "Test",
                        "category": "cooling",
                        "rule_type": "threshold",
                        "enabled": True,
                        "conditions": [{
                            "sensor_name": "sensor_a",
                            "operator": "greater_than",
                            "threshold": 10.0
                        }],
                        "explanation_template": "Test"
                    },
                    {
                        "rule_id": "DISABLED_RULE",
                        "name": "Disabled Rule",
                        "description": "Test",
                        "category": "cooling",
                        "rule_type": "threshold",
                        "enabled": False,
                        "conditions": [{
                            "sensor_name": "sensor_b",
                            "operator": "less_than",
                            "threshold": 5.0
                        }],
                        "explanation_template": "Test"
                    }
                ]
            }

            with open(rule_file, 'w') as f:
                yaml.dump(rule_data, f)

            loader = RuleLoader(rules_dir)
            loader.load_all_rules()

            enabled = loader.get_enabled_rules()
            assert len(enabled) == 1
            assert enabled[0].rule_id == "ENABLED_RULE"

    def test_validate_rules(self):
        """Test rule validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)
            rule_file = rules_dir / "test_rules.yaml"

            rule_data = {
                "rules": [{
                    "rule_id": "VALID_RULE",
                    "name": "Valid Rule",
                    "description": "Test",
                    "category": "cooling",
                    "rule_type": "threshold",
                    "confidence": 0.9,
                    "priority": 5,
                    "conditions": [{
                        "sensor_name": "sensor_a",
                        "operator": "greater_than",
                        "threshold": 10.0
                    }],
                    "explanation_template": "Test"
                }]
            }

            with open(rule_file, 'w') as f:
                yaml.dump(rule_data, f)

            loader = RuleLoader(rules_dir)
            loader.load_all_rules()

            result = loader.validate_rules()
            assert result.error_count == 0

    def test_validate_confidence_range(self):
        """Test confidence range validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)
            rule_file = rules_dir / "test_rules.yaml"

            rule_data = {
                "rules": [{
                    "rule_id": "BAD_CONFIDENCE",
                    "name": "Bad Confidence",
                    "description": "Test",
                    "category": "cooling",
                    "rule_type": "threshold",
                    "confidence": 1.5,  # Invalid - > 1.0
                    "priority": 5,
                    "conditions": [{
                        "sensor_name": "sensor_a",
                        "operator": "greater_than",
                        "threshold": 10.0
                    }],
                    "explanation_template": "Test"
                }]
            }

            with open(rule_file, 'w') as f:
                yaml.dump(rule_data, f)

            loader = RuleLoader(rules_dir)
            load_result = loader.load_all_rules()

            # The rule should fail to load due to Pydantic validation
            assert load_result.error_count > 0
            assert load_result.loaded_count == 0
            # The error should mention confidence validation
            assert any("confidence" in e.lower() and ("less_than_equal" in e or "out of range" in e or "should be" in e) for e in load_result.errors)

    def test_validate_priority_range(self):
        """Test priority range validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)
            rule_file = rules_dir / "test_rules.yaml"

            rule_data = {
                "rules": [{
                    "rule_id": "BAD_PRIORITY",
                    "name": "Bad Priority",
                    "description": "Test",
                    "category": "cooling",
                    "rule_type": "threshold",
                    "confidence": 0.9,
                    "priority": 15,  # Invalid - > 10
                    "conditions": [{
                        "sensor_name": "sensor_a",
                        "operator": "greater_than",
                        "threshold": 10.0
                    }],
                    "explanation_template": "Test"
                }]
            }

            with open(rule_file, 'w') as f:
                yaml.dump(rule_data, f)

            loader = RuleLoader(rules_dir)
            load_result = loader.load_all_rules()

            # The rule should fail to load due to Pydantic validation
            assert load_result.error_count > 0
            assert load_result.loaded_count == 0
            # The error should mention priority validation
            assert any("priority" in e.lower() and ("greater_than" in e or "out of range" in e or "should be" in e) for e in load_result.errors)

    def test_validate_composite_references(self):
        """Test composite rule reference validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)
            rule_file = rules_dir / "test_rules.yaml"

            rule_data = {
                "rules": [{
                    "rule_id": "COMPOSITE_RULE",
                    "name": "Composite Rule",
                    "description": "Test",
                    "category": "cooling",
                    "rule_type": "composite",
                    "referenced_rule_ids": ["NON_EXISTENT_RULE"],
                    "explanation_template": "Test"
                }]
            }

            with open(rule_file, 'w') as f:
                yaml.dump(rule_data, f)

            loader = RuleLoader(rules_dir)
            loader.load_all_rules()

            result = loader.validate_rules()
            assert result.error_count > 0
            assert any("references unknown rule" in e for e in result.errors)


class TestConvenienceFunction:
    """Test convenience functions."""

    def test_load_rules_from_directory(self):
        """Test the load_rules_from_directory convenience function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)
            rule_file = rules_dir / "test_rules.yaml"

            rule_data = {
                "rules": [{
                    "rule_id": "CONV_TEST",
                    "name": "Convenience Test",
                    "description": "Test",
                    "category": "cooling",
                    "rule_type": "threshold",
                    "conditions": [{
                        "sensor_name": "sensor_a",
                        "operator": "greater_than",
                        "threshold": 10.0
                    }],
                    "explanation_template": "Test"
                }]
            }

            with open(rule_file, 'w') as f:
                yaml.dump(rule_data, f)

            result = load_rules_from_directory(rules_dir)

            assert result.loaded_count == 1
            assert len(result.rules) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""
i20 AI Garage - Rule Loader

Loads and validates rule definitions from YAML files.
Supports multiple rule files with schema validation.
"""

import os
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from .rule_models import (
    RuleDefinition, RuleCondition, RuleLoadResult,
    RuleType, RuleCategory, RuleSeverity, RuleStatus,
    DataSource, LogicalOperator, ThresholdOperator, TrendOperator, MissingDataPolicy,
    calculate_confidence
)

logger = logging.getLogger(__name__)


class RuleLoader:
    """Loads and validates rule definitions from YAML files."""

    # Default rule directory
    DEFAULT_RULES_DIR = Path(__file__).parent / "rules"

    # Supported rule file extensions
    SUPPORTED_EXTENSIONS = {".yaml", ".yml"}

    def __init__(self, rules_dir: Optional[Path] = None):
        """
        Initialize rule loader.

        Args:
            rules_dir: Directory containing rule YAML files. Defaults to services/rules/
        """
        self.rules_dir = rules_dir or self.DEFAULT_RULES_DIR
        self._loaded_rules: Dict[str, RuleDefinition] = {}
        self._load_result: Optional[RuleLoadResult] = None

    def load_all_rules(self, recursive: bool = True) -> RuleLoadResult:
        """
        Load all rule files from the rules directory.

        Args:
            recursive: Whether to search subdirectories

        Returns:
            RuleLoadResult with loaded rules and any errors
        """
        result = RuleLoadResult()

        if not self.rules_dir.exists():
            result.errors.append(f"Rules directory not found: {self.rules_dir}")
            result.error_count = 1
            self._load_result = result
            return result

        # Find all YAML files
        if recursive:
            rule_files = list(self.rules_dir.rglob("*.yaml")) + list(self.rules_dir.rglob("*.yml"))
        else:
            rule_files = list(self.rules_dir.glob("*.yaml")) + list(self.rules_dir.glob("*.yml"))

        if not rule_files:
            result.errors.append(f"No YAML rule files found in: {self.rules_dir}")
            result.error_count = 1
            self._load_result = result
            return result

        for rule_file in rule_files:
            file_result = self.load_rule_file(rule_file)
            result.loaded_count += file_result.loaded_count
            result.skipped_count += file_result.skipped_count
            result.error_count += file_result.error_count
            result.errors.extend(file_result.errors)
            result.rules.extend(file_result.rules)

        # Check for duplicate rule IDs
        self._check_duplicates(result)

        # Store loaded rules
        for rule in result.rules:
            self._loaded_rules[rule.rule_id] = rule

        self._load_result = result
        logger.info(f"Loaded {result.loaded_count} rules from {len(rule_files)} files")
        return result

    def load_rule_file(self, file_path: Path) -> RuleLoadResult:
        """
        Load rules from a single YAML file.

        Args:
            file_path: Path to YAML rule file

        Returns:
            RuleLoadResult with rules from this file
        """
        result = RuleLoadResult()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            result.error_count = 1
            result.errors.append(f"YAML parse error in {file_path}: {e}")
            return result
        except Exception as e:
            result.error_count = 1
            result.errors.append(f"Error reading {file_path}: {e}")
            return result

        if not data:
            result.skipped_count = 1
            result.errors.append(f"Empty or invalid YAML in {file_path}")
            return result

        # Handle both single rule and list of rules
        if isinstance(data, dict) and 'rule_id' in data:
            rules_data = [data]
        elif isinstance(data, list):
            rules_data = data
        elif isinstance(data, dict) and 'rules' in data:
            rules_data = data['rules']
        else:
            result.error_count = 1
            result.errors.append(f"Invalid rule file structure in {file_path}")
            return result

        for rule_data in rules_data:
            try:
                rule = self._parse_rule(rule_data, file_path)
                if rule:
                    result.rules.append(rule)
                    result.loaded_count += 1
                else:
                    result.skipped_count += 1
            except Exception as e:
                result.error_count += 1
                result.errors.append(f"Error parsing rule in {file_path}: {e}")
                logger.exception(f"Rule parse error: {e}")

        return result

    def _parse_rule(self, rule_data: Dict[str, Any], source_file: Path) -> Optional[RuleDefinition]:
        """Parse a single rule definition from YAML data."""

        # Required fields
        required_fields = ['rule_id', 'name', 'description', 'rule_type']
        for field in required_fields:
            if field not in rule_data:
                raise ValueError(f"Missing required field: {field}")

        rule_id = rule_data['rule_id']

        # Parse enums
        try:
            rule_type = RuleType(rule_data['rule_type'])
            category = RuleCategory(rule_data.get('category', 'general'))
            severity = RuleSeverity(rule_data.get('severity', 'medium'))
        except ValueError as e:
            raise ValueError(f"Invalid enum value: {e}")

        # Parse conditions
        conditions = []
        for cond_data in rule_data.get('conditions', []):
            condition = self._parse_condition(cond_data)
            if condition:
                conditions.append(condition)

        # Parse composite rule references
        referenced_rule_ids = rule_data.get('referenced_rule_ids', [])
        composite_logic = LogicalOperator(rule_data.get('composite_logic', 'and'))

        # Build rule definition
        rule = RuleDefinition(
            rule_id=rule_id,
            name=rule_data['name'],
            description=rule_data['description'],
            category=category,
            rule_type=rule_type,
            enabled=rule_data.get('enabled', True),
            version=rule_data.get('version', '1.0'),
            severity=severity,
            priority=rule_data.get('priority', 5),
            confidence=rule_data.get('confidence', 0.8),
            conditions=conditions,
            evaluation_window_seconds=rule_data.get('evaluation_window_seconds'),
            required_sensors=rule_data.get('required_sensors', []),
            missing_data_policy=MissingDataPolicy(rule_data.get('missing_data_policy', 'skip_rule')),
            cooldown_seconds=rule_data.get('cooldown_seconds', 300),
            referenced_rule_ids=referenced_rule_ids,
            composite_logic=composite_logic,
            explanation_template=rule_data.get('explanation_template', ''),
            recommended_checks=rule_data.get('recommended_checks', []),
            recommended_actions=rule_data.get('recommended_actions', []),
            safety_notes=rule_data.get('safety_notes', []),
            source=rule_data.get('source', 'generic_obd'),
            dtc_hints=rule_data.get('dtc_hints', []),
        )

        return rule

    def _parse_condition(self, cond_data: Dict[str, Any]) -> Optional[RuleCondition]:
        """Parse a single condition from YAML data."""

        if 'sensor_name' not in cond_data:
            raise ValueError("Condition missing required field: sensor_name")

        # Parse operators
        operator = None
        if 'operator' in cond_data:
            operator = ThresholdOperator(cond_data['operator'])

        trend_operator = None
        if 'trend_operator' in cond_data:
            trend_operator = TrendOperator(cond_data['trend_operator'])

        logical_operator = LogicalOperator(cond_data.get('logical_operator', 'and'))
        missing_data_policy = MissingDataPolicy(cond_data.get('missing_data_policy', 'skip_rule'))

        condition = RuleCondition(
            sensor_name=cond_data['sensor_name'],
            sensor_unit=cond_data.get('sensor_unit'),
            operator=operator,
            threshold=cond_data.get('threshold'),
            threshold_min=cond_data.get('threshold_min'),
            threshold_max=cond_data.get('threshold_max'),
            comparison_value=cond_data.get('comparison_value'),
            trend_operator=trend_operator,
            trend_window_seconds=cond_data.get('trend_window_seconds', 60),
            min_samples=cond_data.get('min_samples', 5),
            max_gap_seconds=cond_data.get('max_gap_seconds', 30),
            rate_threshold=cond_data.get('rate_threshold'),
            condition_group=cond_data.get('condition_group'),
            logical_operator=logical_operator,
            optional=cond_data.get('optional', False),
            missing_data_policy=missing_data_policy,
            default_value=cond_data.get('default_value'),
        )

        return condition

    def _check_duplicates(self, result: RuleLoadResult) -> None:
        """Check for duplicate rule IDs."""
        seen = {}
        for rule in result.rules:
            if rule.rule_id in seen:
                result.errors.append(
                    f"Duplicate rule ID '{rule.rule_id}' in rules: "
                    f"{seen[rule.rule_id]}, {rule.name}"
                )
                result.error_count += 1
            else:
                seen[rule.rule_id] = rule.name

    def get_rule(self, rule_id: str) -> Optional[RuleDefinition]:
        """Get a loaded rule by ID."""
        return self._loaded_rules.get(rule_id)

    def get_all_rules(self) -> List[RuleDefinition]:
        """Get all loaded rules."""
        return list(self._loaded_rules.values())

    def get_rules_by_type(self, rule_type: RuleType) -> List[RuleDefinition]:
        """Get rules filtered by type."""
        return [r for r in self._loaded_rules.values() if r.rule_type == rule_type]

    def get_rules_by_category(self, category: RuleCategory) -> List[RuleDefinition]:
        """Get rules filtered by category."""
        return [r for r in self._loaded_rules.values() if r.category == category]

    def get_enabled_rules(self) -> List[RuleDefinition]:
        """Get only enabled rules."""
        return [r for r in self._loaded_rules.values() if r.enabled]

    def validate_rules(self, rules: Optional[List[RuleDefinition]] = None) -> RuleLoadResult:
        """
        Validate rules for consistency and completeness.

        Args:
            rules: Rules to validate. If None, uses all loaded rules.

        Returns:
            RuleLoadResult with validation errors
        """
        result = RuleLoadResult()
        rules_to_check = rules or list(self._loaded_rules.values())

        rule_ids = set()
        for rule in rules_to_check:
            # Check duplicate IDs
            if rule.rule_id in rule_ids:
                result.errors.append(f"Duplicate rule ID: {rule.rule_id}")
                result.error_count += 1
            rule_ids.add(rule.rule_id)

            # Check composite rule references exist
            if rule.rule_type == RuleType.COMPOSITE:
                for ref_id in rule.referenced_rule_ids:
                    if ref_id not in self._loaded_rules:
                        result.errors.append(
                            f"Rule {rule.rule_id} references unknown rule: {ref_id}"
                        )
                        result.error_count += 1

            # Check confidence range
            if not 0.0 <= rule.confidence <= 1.0:
                result.errors.append(
                    f"Rule {rule.rule_id} confidence out of range: {rule.confidence}"
                )
                result.error_count += 1

            # Check priority range
            if not 1 <= rule.priority <= 10:
                result.errors.append(
                    f"Rule {rule.rule_id} priority out of range: {rule.priority}"
                )
                result.error_count += 1

        return result

    def reload(self) -> RuleLoadResult:
        """Reload all rules from disk."""
        self._loaded_rules.clear()
        return self.load_all_rules()


# =============================================================================
# YAML EXAMPLE TEMPLATE
# =============================================================================

RULE_YAML_TEMPLATE = """
# Example rule YAML file
# Save as: services/rules/cooling_rules.yaml

rules:
  # Threshold Rule - Coolant Overheat
  - rule_id: "RULE_COOLANT_OVERHEAT"
    name: "Coolant Temperature Overheat"
    description: "Detects when coolant temperature exceeds safe operating limits"
    category: "cooling"
    rule_type: "threshold"
    enabled: true
    version: "1.0"
    severity: "high"
    priority: 2
    confidence: 0.9
    conditions:
      - sensor_name: "coolant_temp_c"
        sensor_unit: "°C"
        operator: "greater_than"
        threshold: 105.0
    explanation_template: "Coolant temperature reached {observed_value}°C, exceeding the safe limit of {threshold}°C"
    recommended_checks:
      - "Check coolant level in reservoir"
      - "Inspect radiator for blockages"
      - "Verify radiator fan operation"
      - "Check for coolant leaks"
    recommended_actions:
      - "Allow engine to cool before opening radiator cap"
      - "Top up coolant if low"
      - "Replace thermostat if stuck closed"
      - "Flush cooling system if contaminated"
    safety_notes:
      - "Never open radiator cap when engine is hot"
      - "Hot coolant can cause severe burns"
    source: "hyundai_specific"
    dtc_hints: ["P0217", "P0128"]

  # Trend Rule - Coolant Temp Rising Rapidly
  - rule_id: "RULE_COOLANT_RAPID_RISE"
    name: "Coolant Temperature Rising Rapidly"
    description: "Detects abnormal rate of coolant temperature increase"
    category: "cooling"
    rule_type: "trend"
    enabled: true
    version: "1.0"
    severity: "medium"
    priority: 3
    confidence: 0.75
    conditions:
      - sensor_name: "coolant_temp_c"
        sensor_unit: "°C"
        trend_operator: "rate_above"
        trend_window_seconds: 60
        min_samples: 5
        max_gap_seconds: 15
        rate_threshold: 1.0  # °C per second
    explanation_template: "Coolant temperature rising at {rate}°C/s, exceeding threshold of {rate_threshold}°C/s"
    recommended_checks:
      - "Check water pump operation"
      - "Verify thermostat opening"
      - "Check for air pockets in cooling system"
    recommended_actions:
      - "Inspect water pump for leaks"
      - "Replace thermostat"
      - "Bleed cooling system"
    safety_notes:
      - "Rapid temperature rise indicates imminent overheating"
    source: "generic_obd"
    dtc_hints: ["P0217"]

  # Correlation Rule - Lean Condition with High Load
  - rule_id: "RULE_LEAN_UNDER_LOAD"
    name: "Lean Fuel Condition Under Load"
    description: "Detects lean air-fuel ratio during high engine load"
    category: "fuel"
    rule_type: "correlation"
    enabled: true
    version: "1.0"
    severity: "high"
    priority: 2
    confidence: 0.85
    conditions:
      - sensor_name: "engine_load_pct"
        sensor_unit: "%"
        operator: "greater_than"
        threshold: 70.0
        condition_group: "high_load"
      - sensor_name: "short_term_fuel_trim_b1"
        sensor_unit: "%"
        operator: "greater_than"
        threshold: 15.0
        condition_group: "lean_condition"
      - sensor_name: "long_term_fuel_trim_b1"
        sensor_unit: "%"
        operator: "greater_than"
        threshold: 10.0
        condition_group: "lean_condition"
    explanation_template: "Engine running lean (STFT: {stft}%, LTFT: {ltft}%) under high load ({load}%)"
    recommended_checks:
      - "Check for vacuum leaks"
      - "Inspect MAF sensor for contamination"
      - "Check fuel pressure and delivery"
      - "Verify injector operation"
    recommended_actions:
      - "Clean or replace MAF sensor"
      - "Replace fuel filter"
      - "Check fuel pump pressure"
      - "Repair vacuum leaks"
    safety_notes:
      - "Lean condition can cause engine damage"
      - "May cause misfire and catalytic converter damage"
    source: "generic_obd"
    dtc_hints: ["P0171", "P0174"]

  # Composite Rule - Cooling System Failure
  - rule_id: "RULE_COOLING_SYSTEM_FAILURE"
    name: "Cooling System Failure"
    description: "Composite rule detecting cooling system failure from multiple indicators"
    category: "cooling"
    rule_type: "composite"
    enabled: true
    version: "1.0"
    severity: "critical"
    priority: 1
    confidence: 0.95
    referenced_rule_ids:
      - "RULE_COOLANT_OVERHEAT"
      - "RULE_COOLANT_RAPID_RISE"
    composite_logic: "or"
    explanation_template: "Multiple cooling system indicators triggered: {triggered_rules}"
    recommended_checks:
      - "Complete cooling system inspection"
      - "Pressure test cooling system"
      - "Check all cooling system components"
    recommended_actions:
      - "Repair all identified cooling system issues"
      - "Flush and refill cooling system"
      - "Replace thermostat and water pump if needed"
    safety_notes:
      - "Continued operation will cause severe engine damage"
      - "Stop driving immediately"
    source: "hyundai_specific"
    dtc_hints: ["P0217", "P0128", "P0480"]
"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_example_rules_file(output_path: Optional[Path] = None) -> Path:
    """Create an example rules YAML file for reference."""
    if output_path is None:
        output_path = Path(__file__).parent / "rules" / "example_rules.yaml"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(RULE_YAML_TEMPLATE)

    logger.info(f"Created example rules file at: {output_path}")
    return output_path


def load_rules_from_directory(rules_dir: Optional[Path] = None) -> RuleLoadResult:
    """Convenience function to load rules from a directory."""
    loader = RuleLoader(rules_dir)
    return loader.load_all_rules()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "RuleLoader",
    "load_rules_from_directory",
    "create_example_rules_file",
    "RULE_YAML_TEMPLATE",
]
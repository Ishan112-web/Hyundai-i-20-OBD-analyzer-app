"""
i20 AI Garage - Rule Evaluator

Implements the 4 rule evaluation types:
- Threshold: Simple value comparisons
- Trend: Rate of change analysis
- Correlation: Multi-sensor correlation
- Composite: Logical combination of other rules
"""

import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from dataclasses import dataclass, field
import logging

from .rule_models import (
    RuleDefinition, RuleCondition, RuleConditionResult, RuleFinding,
    RuleEvaluationResult, RuleType, RuleSeverity, RuleStatus,
    DataSource, LogicalOperator, ThresholdOperator, TrendOperator,
    MissingDataPolicy, calculate_confidence, escalate_severity
)
from .types import SensorReading
from .diagnostic_models import VehicleProfile

logger = logging.getLogger(__name__)


@dataclass
class SensorHistory:
    """Historical sensor readings for trend analysis."""
    readings: List[SensorReading] = field(default_factory=list)
    max_age_seconds: int = 300  # 5 minutes default

    def add_reading(self, reading: SensorReading) -> None:
        """Add a reading and prune old ones."""
        self.readings.append(reading)
        self._prune_old()

    def _prune_old(self) -> None:
        """Remove readings older than max_age_seconds."""
        cutoff = datetime.now() - timedelta(seconds=self.max_age_seconds)
        self.readings = [r for r in self.readings if r.timestamp >= cutoff]

    def get_values(self, sensor_name: str, window_seconds: Optional[int] = None) -> List[float]:
        """Get values for a sensor within time window."""
        if window_seconds:
            cutoff = datetime.now() - timedelta(seconds=window_seconds)
            return [r.value for r in self.readings
                   if r.name == sensor_name and r.timestamp >= cutoff]
        return [r.value for r in self.readings if r.name == sensor_name]

    def get_readings(self, sensor_name: str, window_seconds: Optional[int] = None) -> List[SensorReading]:
        """Get full readings for a sensor within time window."""
        if window_seconds:
            cutoff = datetime.now() - timedelta(seconds=window_seconds)
            return [r for r in self.readings
                   if r.name == sensor_name and r.timestamp >= cutoff]
        return [r for r in self.readings if r.name == sensor_name]

    def has_sufficient_data(self, sensor_name: str, min_samples: int,
                           window_seconds: Optional[int] = None,
                           max_gap_seconds: Optional[int] = None) -> bool:
        """Check if we have enough data points with acceptable gaps."""
        readings = self.get_readings(sensor_name, window_seconds)
        if len(readings) < min_samples:
            return False

        if max_gap_seconds and len(readings) >= 2:
            # Check for gaps
            for i in range(1, len(readings)):
                gap = (readings[i].timestamp - readings[i-1].timestamp).total_seconds()
                if gap > max_gap_seconds:
                    return False

        return True

    def calculate_trend_rate(self, sensor_name: str, window_seconds: int) -> Optional[float]:
        """
        Calculate rate of change (slope) using linear regression.
        Returns rate per second.
        """
        readings = self.get_readings(sensor_name, window_seconds)
        if len(readings) < 2:
            return None

        # Use timestamps relative to first reading
        t0 = readings[0].timestamp
        x = [(r.timestamp - t0).total_seconds() for r in readings]
        y = [r.value for r in readings]

        # Simple linear regression
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))

        if n * sum_x2 - sum_x ** 2 == 0:
            return 0.0

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        return slope

    def calculate_moving_average(self, sensor_name: str, window_seconds: int) -> Optional[float]:
        """Calculate moving average over time window."""
        values = self.get_values(sensor_name, window_seconds)
        if not values:
            return None
        return statistics.mean(values)


class BaseEvaluator:
    """Base class for rule evaluators."""

    def __init__(self, sensor_history: SensorHistory):
        self.sensor_history = sensor_history
        self.data_source = DataSource.SIMULATION

    def evaluate(self, rule: RuleDefinition,
                 current_readings: Dict[str, SensorReading],
                 vehicle_profile: Optional[VehicleProfile] = None) -> Tuple[Optional[bool], List[RuleConditionResult], Dict[str, float]]:
        """
        Evaluate a rule.

        Returns:
            (matched, condition_results, observed_values)
            matched is None if rule was skipped due to missing data with SKIP_RULE policy
        """
        raise NotImplementedError

    def _get_sensor_reading(self, sensor_name: str,
                           current_readings: Dict[str, SensorReading]) -> Optional[SensorReading]:
        """Get sensor reading, handling missing data."""
        if sensor_name in current_readings:
            return current_readings[sensor_name]

        # Check history
        recent = self.sensor_history.get_readings(sensor_name, 60)
        if recent:
            return recent[-1]

        return None

    def _handle_missing_data(self, condition: RuleCondition, sensor_name: str) -> Tuple[bool, Optional[float]]:
        """
        Handle missing sensor data according to policy.

        Returns:
            (should_evaluate, value_to_use)
        """
        if condition.missing_data_policy == MissingDataPolicy.SKIP_RULE:
            return False, None
        elif condition.missing_data_policy == MissingDataPolicy.TREAT_AS_NORMAL:
            return True, condition.default_value if condition.default_value is not None else 0.0
        elif condition.missing_data_policy == MissingDataPolicy.TREAT_AS_ABNORMAL:
            return True, condition.threshold if condition.threshold is not None else float('inf')
        elif condition.missing_data_policy == MissingDataPolicy.USE_DEFAULT:
            return True, condition.default_value if condition.default_value is not None else 0.0
        return False, None


class ThresholdEvaluator(BaseEvaluator):
    """Evaluates threshold-based rules (value > threshold, etc.)."""

    def evaluate(self, rule: RuleDefinition,
                 current_readings: Dict[str, SensorReading],
                 vehicle_profile: Optional[VehicleProfile] = None) -> Tuple[Optional[bool], List[RuleConditionResult], Dict[str, float]]:

        condition_results = []
        observed_values = {}
        all_passed = True

        for condition in rule.conditions:
            reading = self._get_sensor_reading(condition.sensor_name, current_readings)

            if reading is None:
                # Handle missing data
                should_eval, default_val = self._handle_missing_data(condition, condition.sensor_name)
                if not should_eval:
                    # SKIP_RULE policy - skip the entire rule
                    condition_results.append(RuleConditionResult(
                        condition_id=condition.condition_id,
                        sensor_name=condition.sensor_name,
                        passed=False,
                        operator=condition.operator.value if condition.operator else None,
                        threshold=condition.threshold,
                        missing_data=True,
                        error="Sensor data not available - rule skipped"
                    ))
                    if not condition.optional:
                        # Required condition missing with SKIP_RULE - skip rule entirely
                        return None, condition_results, observed_values
                    continue

                reading = SensorReading(
                    pid=condition.sensor_name,
                    name=condition.sensor_name,
                    value=default_val,
                    unit=condition.sensor_unit or "",
                    timestamp=datetime.now(),
                    is_simulated=True
                )

            observed_value = float(reading.value)
            observed_values[condition.sensor_name] = observed_value

            # Evaluate threshold
            passed = self._evaluate_threshold(condition, observed_value)

            if not passed and not condition.optional:
                all_passed = False

            condition_results.append(RuleConditionResult(
                condition_id=condition.condition_id,
                sensor_name=condition.sensor_name,
                passed=passed,
                operator=condition.operator.value if condition.operator else None,
                threshold=condition.threshold,
                threshold_min=condition.threshold_min,
                threshold_max=condition.threshold_max,
                observed_value=observed_value,
                unit=condition.sensor_unit,
                missing_data=condition.sensor_name not in current_readings
            ))

        # Apply logical grouping if conditions have groups
        if rule.conditions and any(c.condition_group for c in rule.conditions):
            all_passed = self._evaluate_groups(rule.conditions, condition_results)

        return all_passed, condition_results, observed_values

    def _evaluate_threshold(self, condition: RuleCondition, value: float) -> bool:
        """Evaluate a single threshold condition."""
        op = condition.operator
        threshold = condition.threshold

        if op == ThresholdOperator.GREATER_THAN:
            return value > threshold
        elif op == ThresholdOperator.GREATER_THAN_OR_EQUAL:
            return value >= threshold
        elif op == ThresholdOperator.LESS_THAN:
            return value < threshold
        elif op == ThresholdOperator.LESS_THAN_OR_EQUAL:
            return value <= threshold
        elif op == ThresholdOperator.EQUAL:
            return abs(value - threshold) < 0.001
        elif op == ThresholdOperator.NOT_EQUAL:
            return abs(value - threshold) >= 0.001
        elif op == ThresholdOperator.BETWEEN:
            return condition.threshold_min <= value <= condition.threshold_max
        elif op == ThresholdOperator.OUTSIDE:
            return value < condition.threshold_min or value > condition.threshold_max
        elif op == ThresholdOperator.EXISTS:
            return True  # We have a value
        elif op == ThresholdOperator.MISSING:
            return False  # We have a value, so not missing

        return False

    def _evaluate_groups(self, conditions: List[RuleCondition],
                        results: List[RuleConditionResult]) -> bool:
        """Evaluate conditions with logical grouping (AND/OR)."""
        # Group conditions by condition_group
        groups = defaultdict(list)
        ungrouped = []

        for cond, result in zip(conditions, results):
            if cond.condition_group:
                groups[cond.condition_group].append((cond, result))
            else:
                ungrouped.append((cond, result))

        # Ungrouped conditions must all pass (AND)
        for cond, result in ungrouped:
            if not cond.optional and not result.passed:
                return False

        # Each group is evaluated with its logical_operator
        for group_name, group_items in groups.items():
            if not group_items:
                continue

            # Use first condition's logical_operator for the group
            op = group_items[0][0].logical_operator

            if op == LogicalOperator.AND:
                group_passed = all(r.passed for _, r in group_items)
            else:  # OR
                group_passed = any(r.passed for _, r in group_items)

            # Check if any required condition in group failed
            for cond, result in group_items:
                if not cond.optional and not result.passed and op == LogicalOperator.AND:
                    return False

            if not group_passed:
                # For OR groups, if none passed, group fails
                # For AND groups, if any failed, already handled above
                if op == LogicalOperator.OR:
                    return False

        return True


class TrendEvaluator(BaseEvaluator):
    """Evaluates trend-based rules (rate of change, moving averages)."""

    def evaluate(self, rule: RuleDefinition,
                 current_readings: Dict[str, SensorReading],
                 vehicle_profile: Optional[VehicleProfile] = None) -> Tuple[Optional[bool], List[RuleConditionResult], Dict[str, float]]:

        condition_results = []
        observed_values = {}
        all_passed = True

        for condition in rule.conditions:
            sensor_name = condition.sensor_name
            window = condition.trend_window_seconds or 60
            min_samples = condition.min_samples or 5
            max_gap = condition.max_gap_seconds or 30

            # Check if we have sufficient data
            if not self.sensor_history.has_sufficient_data(
                sensor_name, min_samples, window, max_gap
            ):
                # Handle missing data
                should_eval, default_val = self._handle_missing_data(condition, sensor_name)
                if not should_eval:
                    condition_results.append(RuleConditionResult(
                        condition_id=condition.condition_id,
                        sensor_name=sensor_name,
                        passed=False,
                        operator=condition.trend_operator.value if condition.trend_operator else None,
                        threshold=condition.rate_threshold,
                        evaluation_window_seconds=window,
                        missing_data=True,
                        error=f"Insufficient data: need {min_samples} samples over {window}s"
                    ))
                    if not condition.optional:
                        all_passed = False
                    continue

            # Get current value
            reading = self._get_sensor_reading(sensor_name, current_readings)
            current_value = float(reading.value) if reading else None

            if current_value is not None:
                observed_values[sensor_name] = current_value

            # Evaluate trend
            passed, trend_rate, samples_used = self._evaluate_trend(condition, window)

            if not passed and not condition.optional:
                all_passed = False

            condition_results.append(RuleConditionResult(
                condition_id=condition.condition_id,
                sensor_name=sensor_name,
                passed=passed,
                operator=condition.trend_operator.value if condition.trend_operator else None,
                threshold=condition.rate_threshold,
                observed_value=current_value,
                unit=condition.sensor_unit,
                samples_used=samples_used,
                trend_rate=trend_rate,
                evaluation_window_seconds=window
            ))

        return all_passed, condition_results, observed_values

    def _evaluate_trend(self, condition: RuleCondition, window_seconds: int) -> Tuple[bool, Optional[float], int]:
        """Evaluate a trend condition."""
        sensor_name = condition.sensor_name
        op = condition.trend_operator
        rate_threshold = condition.rate_threshold

        readings = self.sensor_history.get_readings(sensor_name, window_seconds)
        samples_used = len(readings)

        if samples_used < 2:
            return False, None, samples_used

        if op == TrendOperator.INCREASING:
            rate = self.sensor_history.calculate_trend_rate(sensor_name, window_seconds)
            if rate is None:
                return False, None, samples_used
            return rate > 0, rate, samples_used

        elif op == TrendOperator.DECREASING:
            rate = self.sensor_history.calculate_trend_rate(sensor_name, window_seconds)
            if rate is None:
                return False, None, samples_used
            return rate < 0, rate, samples_used

        elif op == TrendOperator.RATE_ABOVE:
            rate = self.sensor_history.calculate_trend_rate(sensor_name, window_seconds)
            if rate is None:
                return False, None, samples_used
            return rate > rate_threshold, rate, samples_used

        elif op == TrendOperator.RATE_BELOW:
            rate = self.sensor_history.calculate_trend_rate(sensor_name, window_seconds)
            if rate is None:
                return False, None, samples_used
            return rate < rate_threshold, rate, samples_used

        elif op == TrendOperator.SUSTAINED_ABOVE:
            values = [r.value for r in readings]
            return all(v > rate_threshold for v in values), None, samples_used

        elif op == TrendOperator.SUSTAINED_BELOW:
            values = [r.value for r in readings]
            return all(v < rate_threshold for v in values), None, samples_used

        elif op == TrendOperator.MOVING_AVERAGE_ABOVE:
            avg = self.sensor_history.calculate_moving_average(sensor_name, window_seconds)
            if avg is None:
                return False, None, samples_used
            return avg > rate_threshold, avg, samples_used

        elif op == TrendOperator.MOVING_AVERAGE_BELOW:
            avg = self.sensor_history.calculate_moving_average(sensor_name, window_seconds)
            if avg is None:
                return False, None, samples_used
            return avg < rate_threshold, avg, samples_used

        return False, None, samples_used


class CorrelationEvaluator(BaseEvaluator):
    """Evaluates multi-sensor correlation rules."""

    def evaluate(self, rule: RuleDefinition,
                 current_readings: Dict[str, SensorReading],
                 vehicle_profile: Optional[VehicleProfile] = None) -> Tuple[Optional[bool], List[RuleConditionResult], Dict[str, float]]:

        condition_results = []
        observed_values = {}
        condition_passed = []

        for condition in rule.conditions:
            reading = self._get_sensor_reading(condition.sensor_name, current_readings)

            if reading is None:
                should_eval, default_val = self._handle_missing_data(condition, condition.sensor_name)
                if not should_eval:
                    condition_results.append(RuleConditionResult(
                        condition_id=condition.condition_id,
                        sensor_name=condition.sensor_name,
                        passed=False,
                        operator=condition.operator.value if condition.operator else None,
                        threshold=condition.threshold,
                        missing_data=True,
                        error="Sensor data not available"
                    ))
                    condition_passed.append(False)
                    if not condition.optional:
                        continue
                    # For optional, continue with default

                reading = SensorReading(
                    pid=condition.sensor_name,
                    name=condition.sensor_name,
                    value=default_val,
                    unit=condition.sensor_unit or "",
                    timestamp=datetime.now(),
                    is_simulated=True
                )

            observed_value = float(reading.value)
            observed_values[condition.sensor_name] = observed_value

            # Evaluate threshold for this condition
            passed = self._evaluate_threshold(condition, observed_value)
            condition_passed.append(passed)

            condition_results.append(RuleConditionResult(
                condition_id=condition.condition_id,
                sensor_name=condition.sensor_name,
                passed=passed,
                operator=condition.operator.value if condition.operator else None,
                threshold=condition.threshold,
                threshold_min=condition.threshold_min,
                threshold_max=condition.threshold_max,
                observed_value=observed_value,
                unit=condition.sensor_unit,
                missing_data=condition.sensor_name not in current_readings
            ))

        # Correlation requires ALL conditions to pass (AND logic)
        # But we can also support grouped logic
        all_passed = self._evaluate_correlation(rule.conditions, condition_passed, condition_results)

        return all_passed, condition_results, observed_values

    def _evaluate_threshold(self, condition: RuleCondition, value: float) -> bool:
        """Evaluate a single threshold condition (same as ThresholdEvaluator)."""
        op = condition.operator
        threshold = condition.threshold

        if op == ThresholdOperator.GREATER_THAN:
            return value > threshold
        elif op == ThresholdOperator.GREATER_THAN_OR_EQUAL:
            return value >= threshold
        elif op == ThresholdOperator.LESS_THAN:
            return value < threshold
        elif op == ThresholdOperator.LESS_THAN_OR_EQUAL:
            return value <= threshold
        elif op == ThresholdOperator.EQUAL:
            return abs(value - threshold) < 0.001
        elif op == ThresholdOperator.NOT_EQUAL:
            return abs(value - threshold) >= 0.001
        elif op == ThresholdOperator.BETWEEN:
            return condition.threshold_min <= value <= condition.threshold_max
        elif op == ThresholdOperator.OUTSIDE:
            return value < condition.threshold_min or value > condition.threshold_max
        elif op == ThresholdOperator.EXISTS:
            return True
        elif op == ThresholdOperator.MISSING:
            return False

        return False

    def _evaluate_correlation(self, conditions: List[RuleCondition],
                             condition_passed: List[bool],
                             condition_results: List[RuleConditionResult]) -> bool:
        """Evaluate correlation logic with grouping support."""
        # Group by condition_group
        groups = defaultdict(list)

        for i, (cond, passed) in enumerate(zip(conditions, condition_passed)):
            group_name = cond.condition_group or f"_ungrouped_{i}"
            groups[group_name].append((cond, passed, condition_results[i]))

        # Each group is AND internally
        group_results = []
        for group_name, group_items in groups.items():
            op = group_items[0][0].logical_operator

            if op == LogicalOperator.AND:
                group_passed = all(passed for _, passed, _ in group_items)
            else:  # OR
                group_passed = any(passed for _, passed, _ in group_items)

            # Check required conditions
            for cond, passed, _ in group_items:
                if not cond.optional and not passed and op == LogicalOperator.AND:
                    return False

            group_results.append(group_passed)

        # All groups must pass (AND between groups)
        return all(group_results)


class CompositeEvaluator(BaseEvaluator):
    """Evaluates composite rules that combine other rule results."""

    def __init__(self, sensor_history: SensorHistory,
                 previous_findings: Optional[Dict[str, RuleFinding]] = None):
        super().__init__(sensor_history)
        self.previous_findings = previous_findings or {}

    def evaluate(self, rule: RuleDefinition,
                 current_readings: Dict[str, SensorReading],
                 vehicle_profile: Optional[VehicleProfile] = None) -> Tuple[Optional[bool], List[RuleConditionResult], Dict[str, float]]:

        condition_results = []
        observed_values = {}
        referenced_passed = []

        for ref_rule_id in rule.referenced_rule_ids:
            if ref_rule_id in self.previous_findings:
                finding = self.previous_findings[ref_rule_id]
                passed = finding.status == RuleStatus.TRIGGERED
                referenced_passed.append(passed)

                # Add referenced rule's observed values
                observed_values.update(finding.observed_values)

                condition_results.append(RuleConditionResult(
                    condition_id=f"ref_{ref_rule_id}",
                    sensor_name=ref_rule_id,
                    passed=passed,
                    observed_value=1.0 if passed else 0.0,
                    expected_value=1.0,
                    unit="triggered",
                    error=None if passed else "Referenced rule not triggered"
                ))
            else:
                # Referenced rule not evaluated or no finding
                referenced_passed.append(False)
                condition_results.append(RuleConditionResult(
                    condition_id=f"ref_{ref_rule_id}",
                    sensor_name=ref_rule_id,
                    passed=False,
                    observed_value=0.0,
                    expected_value=1.0,
                    unit="triggered",
                    error=f"Referenced rule {ref_rule_id} not found or not evaluated"
                ))

        # Evaluate composite logic
        if rule.composite_logic == LogicalOperator.AND:
            all_passed = all(referenced_passed)
        else:  # OR
            all_passed = any(referenced_passed)

        return all_passed, condition_results, observed_values


# =============================================================================
# MAIN RULE EVALUATOR ORCHESTRATOR
# =============================================================================

class RuleEvaluator:
    """
    Main rule evaluator that orchestrates all evaluator types.
    """

    def __init__(self, sensor_history: Optional[SensorHistory] = None):
        self.sensor_history = sensor_history or SensorHistory()
        self.evaluators = {
            RuleType.THRESHOLD: ThresholdEvaluator(self.sensor_history),
            RuleType.TREND: TrendEvaluator(self.sensor_history),
            RuleType.CORRELATION: CorrelationEvaluator(self.sensor_history),
            RuleType.COMPOSITE: CompositeEvaluator(self.sensor_history),
        }
        self.data_source = DataSource.SIMULATION
        # Track last finding time per rule for cooldown
        self._last_finding_time: Dict[str, datetime] = {}

    def set_data_source(self, source: DataSource) -> None:
        """Set data source for all evaluators."""
        self.data_source = source
        for evaluator in self.evaluators.values():
            evaluator.data_source = source

    def add_reading(self, reading: SensorReading) -> None:
        """Add a sensor reading to history."""
        self.sensor_history.add_reading(reading)

    def add_readings(self, readings: List[SensorReading]) -> None:
        """Add multiple sensor readings to history."""
        for reading in readings:
            self.add_reading(reading)

    def evaluate_rules(self, rules: List[RuleDefinition],
                      current_readings: Dict[str, SensorReading],
                      vehicle_profile: Optional[VehicleProfile] = None,
                      diagnostic_session_id: Optional[str] = None) -> RuleEvaluationResult:
        """
        Evaluate a list of rules.

        Args:
            rules: List of rules to evaluate
            current_readings: Current sensor readings
            vehicle_profile: Optional vehicle profile for context
            diagnostic_session_id: Optional session ID for tracking

        Returns:
            RuleEvaluationResult with all findings
        """
        start_time = time.perf_counter()

        result = RuleEvaluationResult(
            data_source=self.data_source,
            diagnostic_session_id=diagnostic_session_id
        )

        # Sort rules by priority (1 = highest)
        sorted_rules = sorted(rules, key=lambda r: (r.priority, -r.confidence))

        # Track findings for composite rules
        findings_by_rule: Dict[str, RuleFinding] = {}

        for rule in sorted_rules:
            if not rule.enabled:
                result.rules_skipped += 1
                continue

            try:
                # Check cooldown
                if self._is_in_cooldown(rule):
                    result.rules_skipped += 1
                    continue

                # Get evaluator for rule type
                evaluator = self.evaluators.get(rule.rule_type)
                if not evaluator:
                    result.rules_failed += 1
                    result.evaluation_errors.append(f"No evaluator for rule type: {rule.rule_type}")
                    continue

                # For composite rules, pass previous findings
                if rule.rule_type == RuleType.COMPOSITE:
                    self.evaluators[RuleType.COMPOSITE] = CompositeEvaluator(
                        self.sensor_history, findings_by_rule
                    )
                    evaluator = self.evaluators[RuleType.COMPOSITE]

                # Evaluate rule
                rule_start = time.perf_counter()
                matched, condition_results, observed_values = evaluator.evaluate(
                    rule, current_readings, vehicle_profile
                )
                rule_duration = (time.perf_counter() - rule_start) * 1000

                # Check if rule was skipped due to missing data with SKIP_RULE policy
                if matched is None:
                    result.rules_skipped += 1
                    continue

                result.rules_evaluated += 1

                if matched:
                    # Create finding
                    finding = self._create_finding(
                        rule, condition_results, observed_values,
                        rule_duration, diagnostic_session_id
                    )

                    # Escalate severity based on other findings
                    finding.severity = escalate_severity(
                        finding.severity, list(findings_by_rule.values())
                    )

                    result.findings.append(finding)
                    findings_by_rule[rule.rule_id] = finding
                    # Update last finding time for cooldown tracking
                    self._last_finding_time[rule.rule_id] = finding.timestamp

            except Exception as e:
                result.rules_failed += 1
                result.evaluation_errors.append(f"Error evaluating {rule.rule_id}: {e}")
                logger.exception(f"Rule evaluation error: {e}")

        result.execution_duration_ms = (time.perf_counter() - start_time) * 1000
        return result

    def _is_in_cooldown(self, rule: RuleDefinition) -> bool:
        """Check if rule is in cooldown period."""
        if rule.rule_id in self._last_finding_time:
            elapsed = (datetime.now() - self._last_finding_time[rule.rule_id]).total_seconds()
            if elapsed < rule.cooldown_seconds:
                return True
        return False

    def _create_finding(self, rule: RuleDefinition,
                       condition_results: List[RuleConditionResult],
                       observed_values: Dict[str, float],
                       duration_ms: float,
                       diagnostic_session_id: Optional[str]) -> RuleFinding:
        """Create a RuleFinding from evaluation results."""

        # Build explanation from template
        explanation = rule.explanation_template
        for cond_result in condition_results:
            if cond_result.observed_value is not None:
                explanation = explanation.replace(
                    f"{{{cond_result.sensor_name}}}",
                    f"{cond_result.observed_value:.1f}"
                )
                if cond_result.threshold is not None:
                    explanation = explanation.replace(
                        f"{{threshold}}", f"{cond_result.threshold:.1f}"
                    )
                if cond_result.trend_rate is not None:
                    explanation = explanation.replace(
                        f"{{rate}}", f"{cond_result.trend_rate:.2f}"
                    )
                    if cond_result.threshold is not None:
                        explanation = explanation.replace(
                            f"{{rate_threshold}}", f"{cond_result.threshold:.2f}"
                        )

        # Build evidence list
        evidence = []
        for cond_result in condition_results:
            if cond_result.passed:
                if cond_result.operator:
                    evidence.append(
                        f"{cond_result.sensor_name}: {cond_result.observed_value:.1f} "
                        f"{cond_result.operator} {cond_result.threshold}"
                    )
                elif cond_result.trend_rate is not None:
                    evidence.append(
                        f"{cond_result.sensor_name}: trend rate {cond_result.trend_rate:.2f}/s"
                    )

        # Missing data
        missing_data = [cr.sensor_name for cr in condition_results if cr.missing_data]

        # Expected values (thresholds)
        expected_values = {}
        for cr in condition_results:
            if cr.threshold is not None:
                expected_values[cr.sensor_name] = cr.threshold

        # Calculate confidence
        confidence = calculate_confidence(
            sensor_valid=len(missing_data) == 0,
            data_fresh=True,  # We'd need timestamp checking for this
            sample_count=max((cr.samples_used or 0) for cr in condition_results),
            min_samples=5,
            condition_complete=len(missing_data) == 0,
            rule_reliability=rule.confidence,
            evidence_quality=0.9 if evidence else 0.5
        )

        finding = RuleFinding(
            rule_id=rule.rule_id,
            rule_name=rule.name,
            rule_type=rule.rule_type,
            severity=rule.severity,
            priority=rule.priority,
            confidence=confidence,
            status=RuleStatus.TRIGGERED,
            summary=f"{rule.name}: {explanation[:100]}",
            explanation=explanation,
            observed_values=observed_values,
            expected_values=expected_values,
            evidence=evidence,
            missing_data=missing_data,
            condition_results=condition_results,
            recommended_checks=rule.recommended_checks,
            recommended_actions=rule.recommended_actions,
            safety_notes=rule.safety_notes,
            data_source=self.data_source,
            diagnostic_session_id=diagnostic_session_id,
            rule_source=rule.source,
            dtc_hints=rule.dtc_hints,
            evaluation_duration_ms=duration_ms
        )

        return finding


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "SensorHistory",
    "BaseEvaluator",
    "ThresholdEvaluator",
    "TrendEvaluator",
    "CorrelationEvaluator",
    "CompositeEvaluator",
    "RuleEvaluator",
]
"""
i20 AI Garage - Rule Engine

Main orchestrator for deterministic rule-based diagnostics.
Integrates rule loading, evaluation, history persistence, and AI context building.
"""

import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

from .rule_models import (
    RuleDefinition, RuleEvaluationResult, RuleFinding, RuleLoadResult,
    RuleType, RuleSeverity, DataSource, calculate_confidence
)
from .rule_loader import RuleLoader, load_rules_from_directory
from .rule_evaluator import RuleEvaluator, SensorHistory
from .rule_context import RuleContext, RuleContextBuilder
from .rule_history import RuleHistoryStore
from .types import SensorReading, DTC
from .diagnostic_models import VehicleProfile
from .database import DatabaseService, get_database

logger = logging.getLogger(__name__)


class RuleEngine:
    """
    Main rule engine for deterministic automotive diagnostics.

    Features:
    - YAML-based rule configuration
    - 4 rule types: threshold, trend, correlation, composite
    - Historical sensor data for trend analysis
    - Evaluation history persistence
    - AI diagnostic context integration
    - Thread-safe operation
    """

    # Singleton instance
    _instance: Optional['RuleEngine'] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self,
                 rules_dir: Optional[Path] = None,
                 db_service: Optional[DatabaseService] = None,
                 max_history_age_seconds: int = 300,
                 force_reload: bool = False):
        """
        Initialize the rule engine.

        Args:
            rules_dir: Directory containing rule YAML files
            db_service: Database service for history persistence
            max_history_age_seconds: Max age for sensor history (trend analysis)
            force_reload: Force re-initialization even if already initialized (for testing)
        """
        # Prevent re-initialization unless forced
        if hasattr(self, '_initialized') and not force_reload:
            # If rules_dir changed, reload rules
            if rules_dir is not None and rules_dir != self.rules_dir:
                self.rules_dir = rules_dir
                self.loader = RuleLoader(rules_dir)
                self.reload_rules()
            return

        self.rules_dir = rules_dir
        self.max_history_age_seconds = max_history_age_seconds

        # Initialize components
        self.loader = RuleLoader(rules_dir)
        self.sensor_history = SensorHistory(max_age_seconds=max_history_age_seconds)
        self.evaluator = RuleEvaluator(self.sensor_history)
        self.context_builder = RuleContextBuilder()

        # Database for history
        self.db_service = db_service or get_database()
        self.history_store = RuleHistoryStore(self.db_service)

        # State
        self._loaded_rules: Dict[str, RuleDefinition] = {}
        self._last_evaluation: Optional[RuleEvaluationResult] = None
        self._last_context: Optional[RuleContext] = None
        self.data_source = DataSource.SIMULATION

        # Load rules on init
        self.reload_rules()

        self._initialized = True
        logger.info("RuleEngine initialized")

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (for testing)."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance._initialized = False
                cls._instance = None

    def reload_rules(self) -> RuleLoadResult:
        """Reload all rules from disk."""
        result = self.loader.load_all_rules()
        self._loaded_rules = {r.rule_id: r for r in result.rules}
        self.evaluator.set_data_source(self.data_source)
        logger.info(f"Reloaded {result.loaded_count} rules")
        return result

    def set_data_source(self, source: DataSource) -> None:
        """Set data source for all evaluations."""
        self.data_source = source
        self.evaluator.set_data_source(source)

    def add_sensor_reading(self, reading: SensorReading) -> None:
        """Add a sensor reading to history."""
        self.sensor_history.add_reading(reading)

    def add_sensor_readings(self, readings: List[SensorReading]) -> None:
        """Add multiple sensor readings to history."""
        for reading in readings:
            self.sensor_history.add_reading(reading)

    def evaluate(self,
                current_readings: Dict[str, SensorReading],
                vehicle_profile: Optional[VehicleProfile] = None,
                active_dtcs: Optional[List[DTC]] = None,
                diagnostic_session_id: Optional[str] = None) -> RuleEvaluationResult:
        """
        Evaluate all enabled rules against current sensor data.

        Args:
            current_readings: Current sensor readings from OBD
            vehicle_profile: Optional vehicle profile for context
            active_dtcs: Currently active DTCs
            diagnostic_session_id: Optional session ID for tracking

        Returns:
            RuleEvaluationResult with all findings
        """
        start_time = time.perf_counter()

        # Get all rules (evaluator will handle disabled ones)
        rules = list(self._loaded_rules.values())

        if not rules:
            logger.warning("No rules loaded to evaluate")
            return RuleEvaluationResult(
                rules_evaluated=0,
                data_source=self.data_source,
                diagnostic_session_id=diagnostic_session_id
            )

        # Update evaluator data source
        self.evaluator.set_data_source(self.data_source)

        # Evaluate rules
        result = self.evaluator.evaluate_rules(
            rules=rules,
            current_readings=current_readings,
            vehicle_profile=vehicle_profile,
            diagnostic_session_id=diagnostic_session_id
        )

        # Update data quality based on available sensors
        result.data_quality = self._assess_data_quality(current_readings, rules)

        # Persist to history
        self._persist_history(result, diagnostic_session_id)

        # Build context for AI
        self._last_context = self.context_builder.build_context(
            evaluation_result=result,
            current_readings=current_readings,
            vehicle_profile=vehicle_profile,
            active_dtcs=active_dtcs
        )

        self._last_evaluation = result

        logger.info(f"Rule evaluation complete: {result.rules_evaluated} rules, "
                   f"{len(result.findings)} findings in {result.execution_duration_ms:.1f}ms")

        return result

    def _assess_data_quality(self,
                            current_readings: Dict[str, SensorReading],
                            rules: List[RuleDefinition]) -> str:
        """Assess data quality based on sensor availability."""
        required_sensors = set()
        for rule in rules:
            required_sensors.update(rule.required_sensors)
            for cond in rule.conditions:
                required_sensors.add(cond.sensor_name)

        if not required_sensors:
            return "unknown"

        available = sum(1 for s in required_sensors if s in current_readings)
        ratio = available / len(required_sensors)

        if ratio >= 0.9:
            return "excellent"
        elif ratio >= 0.7:
            return "good"
        elif ratio >= 0.5:
            return "fair"
        else:
            return "poor"

    def _persist_history(self,
                        result: RuleEvaluationResult,
                        diagnostic_session_id: Optional[str]) -> None:
        """Persist evaluation results to history store."""
        try:
            self.history_store.save_evaluation(result, diagnostic_session_id)
        except Exception as e:
            logger.error(f"Failed to persist rule evaluation history: {e}")

    def get_ai_context(self) -> Optional[RuleContext]:
        """Get the last built AI context."""
        return self._last_context

    def get_ai_context_text(self) -> Optional[str]:
        """Get formatted AI context text for prompt inclusion."""
        if self._last_context:
            return self.context_builder.format_for_ai(self._last_context)
        return None

    def get_ai_context_summary(self) -> Optional[str]:
        """Get brief summary for UI display."""
        if self._last_context:
            return self.context_builder.format_summary(self._last_context)
        return None

    def get_last_evaluation(self) -> Optional[RuleEvaluationResult]:
        """Get the last evaluation result."""
        return self._last_evaluation

    def get_rule(self, rule_id: str) -> Optional[RuleDefinition]:
        """Get a rule by ID."""
        return self._loaded_rules.get(rule_id)

    def get_all_rules(self) -> List[RuleDefinition]:
        """Get all loaded rules."""
        return list(self._loaded_rules.values())

    def get_enabled_rules(self) -> List[RuleDefinition]:
        """Get all enabled rules."""
        return [r for r in self._loaded_rules.values() if r.enabled]

    def get_rules_by_type(self, rule_type: RuleType) -> List[RuleDefinition]:
        """Get rules filtered by type."""
        return [r for r in self._loaded_rules.values() if r.rule_type == rule_type]

    def get_rules_by_category(self, category: str) -> List[RuleDefinition]:
        """Get rules filtered by category."""
        try:
            from .rule_models import RuleCategory
            cat = RuleCategory(category)
            return [r for r in self._loaded_rules.values() if r.category == cat]
        except ValueError:
            return []

    def enable_rule(self, rule_id: str) -> bool:
        """Enable a rule."""
        if rule_id in self._loaded_rules:
            self._loaded_rules[rule_id].enabled = True
            return True
        return False

    def disable_rule(self, rule_id: str) -> bool:
        """Disable a rule."""
        if rule_id in self._loaded_rules:
            self._loaded_rules[rule_id].enabled = False
            return True
        return False

    def get_evaluation_history(self,
                              limit: int = 100,
                              rule_id: Optional[str] = None,
                              severity: Optional[RuleSeverity] = None,
                              start_time: Optional[datetime] = None,
                              end_time: Optional[datetime] = None) -> List[Dict]:
        """Get rule evaluation history from database."""
        return self.history_store.get_history(
            limit=limit,
            rule_id=rule_id,
            severity=severity,
            start_time=start_time,
            end_time=end_time
        )

    def get_finding_history(self,
                           rule_id: str,
                           limit: int = 50) -> List[Dict]:
        """Get finding history for a specific rule."""
        return self.history_store.get_findings_for_rule(rule_id, limit)

    def get_statistics(self) -> Dict[str, Any]:
        """Get rule engine statistics."""
        enabled = self.get_enabled_rules()

        stats = {
            "total_rules_loaded": len(self._loaded_rules),
            "enabled_rules": len(enabled),
            "rules_by_type": {},
            "rules_by_category": {},
            "rules_by_severity": {},
            "data_source": self.data_source.value,
            "history_size": len(self.sensor_history.readings),
            "last_evaluation": None
        }

        for rule in self._loaded_rules.values():
            # By type
            t = rule.rule_type.value
            stats["rules_by_type"][t] = stats["rules_by_type"].get(t, 0) + 1

            # By category
            c = rule.category.value
            stats["rules_by_category"][c] = stats["rules_by_category"].get(c, 0) + 1

            # By severity
            s = rule.severity.value
            stats["rules_by_severity"][s] = stats["rules_by_severity"].get(s, 0) + 1

        if self._last_evaluation:
            stats["last_evaluation"] = {
                "evaluation_id": self._last_evaluation.evaluation_id,
                "timestamp": self._last_evaluation.timestamp.isoformat(),
                "rules_evaluated": self._last_evaluation.rules_evaluated,
                "findings_count": len(self._last_evaluation.findings),
                "execution_duration_ms": self._last_evaluation.execution_duration_ms
            }

        return stats

    def clear_history(self) -> None:
        """Clear sensor history."""
        self.sensor_history.readings.clear()
        logger.info("Sensor history cleared")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_rule_engine(rules_dir: Optional[Path] = None,
                   db_service: Optional[DatabaseService] = None) -> RuleEngine:
    """Get or create the singleton RuleEngine instance."""
    return RuleEngine(rules_dir, db_service)


def create_default_rules_directory(rules_dir: Optional[Path] = None) -> Path:
    """Create default rules directory structure with example files."""
    from .rule_loader import create_example_rules_file

    if rules_dir is None:
        rules_dir = Path(__file__).parent / "rules"

    rules_dir.mkdir(parents=True, exist_ok=True)

    # Create example file
    example_path = rules_dir / "example_rules.yaml"
    create_example_rules_file(example_path)

    # Create category files
    categories = ["cooling", "fuel", "ignition", "emissions", "electrical", "transmission"]
    for cat in categories:
        cat_file = rules_dir / f"{cat}_rules.yaml"
        if not cat_file.exists():
            cat_file.write_text(f"# {cat.capitalize()} Rules\n# Add your {cat} rules here\n\nrules: []\n")

    logger.info(f"Created default rules directory at: {rules_dir}")
    return rules_dir


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "RuleEngine",
    "get_rule_engine",
    "create_default_rules_directory",
]
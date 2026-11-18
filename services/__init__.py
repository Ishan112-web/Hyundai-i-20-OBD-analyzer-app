"""
i20 AI Garage - Services Package
"""

from services.database import get_database, DatabaseService
from services.ai_service import get_ai_service, AIService, AIServiceError
from services.obd_service import get_obd_service, OBDService
from services.real_obd_adapter import RealOBDAdapter, ConnectionProfile, AdapterType, PIDInfo, FreezeFrameData
from services.connection_manager import ConnectionManager, PortInfo, ConnectionAttempt
from services.pid_registry import PIDRegistry, PIDDefinition, PIDValue, PIDPriority
from services.types import OBDMode, ConnectionState, SensorReading, DTC
from services.diagnostic_engine import get_diagnostic_engine, DiagnosticEngine
from services.diagnostic_models import (
    DiagnosticResult, DiagnosticContext, ProbableCause, PrimaryDiagnosis,
    SecondaryDiagnosis, DiagnosticRecommendation,
    DataSource, DiagnosticSeverity, DiagnosticStatus, DataQuality, SafetyLevel
)
# Rule Engine (Phase 3)
from services.rule_engine import get_rule_engine, RuleEngine, create_default_rules_directory
from services.rule_models import (
    RuleDefinition, RuleCondition, RuleFinding, RuleEvaluationResult,
    RuleType, RuleCategory, RuleSeverity, RuleStatus, DataSource as RuleDataSource,
    LogicalOperator, ThresholdOperator, TrendOperator, MissingDataPolicy,
    RuleLoadResult, RuleHistoryEntry, calculate_confidence, escalate_severity
)
from services.rule_loader import RuleLoader, load_rules_from_directory
from services.rule_evaluator import RuleEvaluator, SensorHistory
from services.rule_context import RuleContext, RuleContextBuilder
from services.rule_history import RuleHistoryStore

__all__ = [
    "get_database",
    "DatabaseService",
    "get_ai_service",
    "AIService",
    "AIServiceError",
    "get_obd_service",
    "OBDService",
    "OBDMode",
    "ConnectionState",
    "SensorReading",
    "DTC",
    "RealOBDAdapter",
    "ConnectionProfile",
    "AdapterType",
    "PIDInfo",
    "FreezeFrameData",
    "ConnectionManager",
    "PortInfo",
    "ConnectionAttempt",
    "PIDRegistry",
    "PIDDefinition",
    "PIDValue",
    "PIDPriority",
    "get_diagnostic_engine",
    "DiagnosticEngine",
    "DiagnosticResult",
    "DiagnosticContext",
    "ProbableCause",
    "PrimaryDiagnosis",
    "SecondaryDiagnosis",
    "DiagnosticRecommendation",
    "DataSource",
    "DiagnosticSeverity",
    "DiagnosticStatus",
    "DataQuality",
    "SafetyLevel",
    # Rule Engine (Phase 3)
    "get_rule_engine",
    "RuleEngine",
    "create_default_rules_directory",
    "RuleDefinition",
    "RuleCondition",
    "RuleFinding",
    "RuleEvaluationResult",
    "RuleType",
    "RuleCategory",
    "RuleSeverity",
    "RuleStatus",
    "RuleDataSource",
    "LogicalOperator",
    "ThresholdOperator",
    "TrendOperator",
    "MissingDataPolicy",
    "RuleLoadResult",
    "RuleHistoryEntry",
    "calculate_confidence",
    "escalate_severity",
    "RuleLoader",
    "load_rules_from_directory",
    "RuleEvaluator",
    "SensorHistory",
    "RuleContext",
    "RuleContextBuilder",
    "RuleHistoryStore",
]
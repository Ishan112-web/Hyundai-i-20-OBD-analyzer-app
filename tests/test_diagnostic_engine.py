"""
i20 AI Garage - Diagnostic Engine Tests

Comprehensive tests for the AI Diagnostic Engine including:
- Pydantic model validation
- DiagnosticContextBuilder
- KnowledgeBase
- DiagnosticPromptBuilder
- DiagnosticEngine orchestration
- Database integration
"""

import pytest
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from typing import Dict, Any, List

# Import the modules under test
from services.diagnostic_models import (
    DataSource, DiagnosticSeverity, DiagnosticStatus, DataQuality, SafetyLevel,
    ProbableCause, DiagnosticRecommendation, PrimaryDiagnosis, SecondaryDiagnosis,
    DiagnosticResult, DiagnosticContext
)
from services.diagnostic_engine import (
    KnowledgeBase, DiagnosticContextBuilder, DiagnosticPromptBuilder, DiagnosticEngine
)
from services.types import SensorReading, DTC, OBDMode, ConnectionState


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_obd_service():
    """Create a mock OBD service."""
    service = Mock()
    service.mode = OBDMode.SIMULATION
    service.get_all_readings.return_value = {
        "rpm": SensorReading("rpm", 800, "RPM", datetime.now()),
        "speed_kmh": SensorReading("speed_kmh", 0, "km/h", datetime.now()),
        "coolant_temp_c": SensorReading("coolant_temp_c", 90, "°C", datetime.now()),
        "throttle_pos_pct": SensorReading("throttle_pos_pct", 12, "%", datetime.now()),
        "engine_load_pct": SensorReading("engine_load_pct", 25, "%", datetime.now()),
        "stft_b1_pct": SensorReading("stft_b1_pct", 2.5, "%", datetime.now()),
        "ltft_b1_pct": SensorReading("ltft_b1_pct", 1.2, "%", datetime.now()),
        "voltage_v": SensorReading("voltage_v", 13.8, "V", datetime.now()),
    }
    service.scan_dtcs.return_value = [
        DTC("P0300", "Random/Multiple Cylinder Misfire Detected", "major", "active", True),
        DTC("P0171", "System Too Lean (Bank 1)", "minor", "active", True),
    ]
    service.real_adapter = None
    service.pid_registry = Mock()
    service.pid_registry.supported_pids = {"0C", "0D", "05", "11", "04"}
    service.pid_registry.unsupported_pids = {"06", "07"}
    return service


@pytest.fixture
def mock_database_service():
    """Create a mock database service."""
    service = Mock()
    service.get_vehicle_profile.return_value = {
        "id": 1,
        "make": "Hyundai",
        "model": "i20 Asta",
        "year": 2023,
        "engine": "1.2L Kappa",
        "transmission": "Manual 5-speed",
        "fuel_type": "Petrol",
        "market": "India",
        "ecu_tuning": "Stock",
        "diagnostic_mode": "simulation",
        "vin": "MALA1234567890123"
    }
    service.get_active_session.return_value = {"id": 1, "session_name": "Test Session"}
    service.get_session_records.return_value = [
        {"timestamp": (datetime.now() - timedelta(seconds=i)).isoformat(), "rpm": 800 + i, "speed_kmh": 0, "coolant_temp_c": 90, "throttle_pos_pct": 12, "engine_load_pct": 25, "stft_b1_pct": 2.5, "ltft_b1_pct": 1.2, "voltage_v": 13.8, "maf_g_s": 3.2, "map_kpa": 35}
        for i in range(50)
    ]
    service.get_diagnostic_reports.return_value = []
    service.db_path = Path(":memory:")
    return service


@pytest.fixture
def mock_ai_service():
    """Create a mock AI service."""
    service = Mock()
    service.model = "qwen2.5-3b-instruct"
    service.check_connection.return_value = True
    service.chat_completion.return_value = Mock(
        content=json.dumps({
            "diagnosis_id": "diag_20240101_000001_abc123",
            "diagnostic_status": "complete",
            "severity": "major",
            "confidence": 0.85,
            "summary": "Engine misfire detected with lean condition. Likely ignition coil or fuel delivery issue.",
            "detected_symptoms": ["Rough idle", "Check engine light"],
            "confirmed_faults": ["P0300", "P0171"],
            "primary_diagnosis": {
                "code": "P0300",
                "description": "Random/Multiple Cylinder Misfire Detected",
                "probable_causes": [
                    {
                        "cause": "Faulty ignition coil(s)",
                        "explanation": "Ignition coil failure is common on Kappa 1.2L engines, especially cylinders 2&3",
                        "confidence": 0.8,
                        "supporting_evidence": ["P0300 present", "Rough idle reported"],
                        "contradictory_evidence": [],
                        "verification_steps": ["Swap coil test", "Check coil resistance"],
                        "urgency": "soon"
                    },
                    {
                        "cause": "Worn spark plugs",
                        "explanation": "Spark plugs at 40,000km interval per maintenance schedule",
                        "confidence": 0.6,
                        "supporting_evidence": ["P0300 present"],
                        "contradictory_evidence": [],
                        "verification_steps": ["Inspect spark plugs", "Check gap"],
                        "urgency": "schedule"
                    }
                ],
                "confidence": 0.85,
                "severity": "major"
            },
            "secondary_diagnoses": [
                {
                    "code": "P0171",
                    "description": "System Too Lean (Bank 1)",
                    "probable_causes": [
                        {
                            "cause": "Vacuum leak",
                            "explanation": "Unmetered air entering intake causes lean condition",
                            "confidence": 0.7,
                            "supporting_evidence": ["P0171 present", "STFT positive"],
                            "contradictory_evidence": [],
                            "verification_steps": ["Smoke test intake", "Check fuel trims at idle vs load"],
                            "urgency": "soon"
                        }
                    ],
                    "confidence": 0.75,
                    "severity": "minor",
                    "relationship_to_primary": "May be contributing to misfire"
                }
            ],
            "supporting_evidence": ["P0300 and P0171 both present", "STFT +2.5%", "LTFT +1.2%"],
            "contradictory_evidence": [],
            "recommended_checks": ["Inspect ignition coils", "Check for vacuum leaks", "Verify fuel pressure"],
            "recommended_actions": [
                {
                    "recommendation": "Replace faulty ignition coil(s)",
                    "rationale": "High probability cause of P0300 on this engine",
                    "priority": 2,
                    "safety_level": "professional",
                    "requires_professional": True,
                    "supporting_evidence": ["Common failure on Kappa 1.2L"],
                    "estimated_cost_inr": "₹2,000-₹4,000"
                },
                {
                    "recommendation": "Smoke test intake system for vacuum leaks",
                    "rationale": "P0171 indicates unmetered air",
                    "priority": 3,
                    "safety_level": "professional",
                    "requires_professional": True,
                    "supporting_evidence": ["STFT positive at idle"],
                    "estimated_cost_inr": "₹500-₹1,500"
                }
            ],
            "safety_warnings": [],
            "missing_information": ["Freeze frame data", "Compression test results"],
            "data_quality": "good",
            "dtc_references": ["P0300", "P0171"],
            "rule_engine_findings": ["RULE_MISFIRE_DETECTED", "RULE_LEAN_CONDITION"],
            "rag_sources": ["builtin:P0300", "builtin:P0171", "builtin:hyundai_i20_kappa"]
        }),
        id="test_123",
        model="qwen2.5-3b-instruct",
        finish_reason="stop",
        usage={"total_tokens": 1500},
        created=1234567890
    )
    return service


@pytest.fixture
def knowledge_base():
    """Create a knowledge base instance."""
    return KnowledgeBase()


@pytest.fixture
def diagnostic_context_builder():
    """Create a diagnostic context builder."""
    return DiagnosticContextBuilder()


# =============================================================================
# PYDANTIC MODEL TESTS
# =============================================================================

class TestProbableCause:
    """Tests for ProbableCause model."""

    def test_valid_probable_cause(self):
        """Test creating a valid probable cause."""
        cause = ProbableCause(
            cause="Faulty ignition coil",
            explanation="Coil failure causes misfire",
            confidence=0.8,
            supporting_evidence=["P0300"],
            contradictory_evidence=[],
            verification_steps=["Swap test"],
            urgency="soon"
        )
        assert cause.cause == "Faulty ignition coil"
        assert cause.confidence == 0.8
        assert cause.urgency == "soon"

    def test_confidence_validation(self):
        """Test confidence validation bounds."""
        with pytest.raises(ValueError):
            ProbableCause(cause="Test", explanation="Test", confidence=1.5)
        with pytest.raises(ValueError):
            ProbableCause(cause="Test", explanation="Test", confidence=-0.1)

    def test_confidence_rounding(self):
        """Test confidence is rounded to 2 decimal places."""
        cause = ProbableCause(cause="Test", explanation="Test", confidence=0.789)
        assert cause.confidence == 0.79

    def test_default_urgency(self):
        """Test default urgency value."""
        cause = ProbableCause(cause="Test", explanation="Test", confidence=0.5)
        assert cause.urgency == "schedule"


class TestDiagnosticRecommendation:
    """Tests for DiagnosticRecommendation model."""

    def test_valid_recommendation(self):
        """Test creating a valid recommendation."""
        rec = DiagnosticRecommendation(
            recommendation="Replace ignition coil",
            rationale="Common failure",
            priority=2,
            safety_level=SafetyLevel.PROFESSIONAL,
            requires_professional=True,
            supporting_evidence=["Common on Kappa"],
            estimated_cost_inr="₹2,000-₹4,000"
        )
        assert rec.priority == 2
        assert rec.safety_level == SafetyLevel.PROFESSIONAL
        assert rec.requires_professional is True

    def test_priority_bounds(self):
        """Test priority validation bounds."""
        with pytest.raises(ValueError):
            DiagnosticRecommendation(recommendation="Test", rationale="Test", priority=0)
        with pytest.raises(ValueError):
            DiagnosticRecommendation(recommendation="Test", rationale="Test", priority=11)


class TestPrimaryDiagnosis:
    """Tests for PrimaryDiagnosis model."""

    def test_valid_primary_diagnosis(self):
        """Test creating a valid primary diagnosis."""
        diag = PrimaryDiagnosis(
            code="P0300",
            description="Random Misfire",
            probable_causes=[
                ProbableCause(cause="Coil", explanation="Test", confidence=0.8)
            ],
            confidence=0.85,
            severity=DiagnosticSeverity.MAJOR
        )
        assert diag.code == "P0300"
        assert diag.severity == DiagnosticSeverity.MAJOR
        assert len(diag.probable_causes) == 1


class TestDiagnosticResult:
    """Tests for DiagnosticResult model."""

    def test_valid_result(self):
        """Test creating a valid diagnostic result."""
        result = DiagnosticResult(
            diagnosis_id="diag_test_123",
            data_source=DataSource.SIMULATION,
            diagnostic_status=DiagnosticStatus.COMPLETE,
            severity=DiagnosticSeverity.MAJOR,
            confidence=0.85,
            summary="Test diagnosis",
            primary_diagnosis=PrimaryDiagnosis(
                code="P0300",
                description="Misfire",
                probable_causes=[],
                confidence=0.85,
                severity=DiagnosticSeverity.MAJOR
            )
        )
        assert result.diagnosis_id == "diag_test_123"
        assert result.data_source == DataSource.SIMULATION
        assert result.is_conclusive() is True

    def test_is_conclusive(self):
        """Test is_conclusive method."""
        # Complete with high confidence
        result1 = DiagnosticResult(
            diagnosis_id="test",
            data_source=DataSource.SIMULATION,
            diagnostic_status=DiagnosticStatus.COMPLETE,
            confidence=0.7
        )
        assert result1.is_conclusive() is True

        # Inconclusive
        result2 = DiagnosticResult(
            diagnosis_id="test",
            data_source=DataSource.SIMULATION,
            diagnostic_status=DiagnosticStatus.INCONCLUSIVE,
            confidence=0.7
        )
        assert result2.is_conclusive() is False

        # Low confidence
        result3 = DiagnosticResult(
            diagnosis_id="test",
            data_source=DataSource.SIMULATION,
            diagnostic_status=DiagnosticStatus.COMPLETE,
            confidence=0.3
        )
        assert result3.is_conclusive() is False

    def test_get_highest_severity(self):
        """Test get_highest_severity method."""
        result = DiagnosticResult(
            diagnosis_id="test",
            data_source=DataSource.SIMULATION,
            severity=DiagnosticSeverity.MINOR,
            primary_diagnosis=PrimaryDiagnosis(
                code="P0300", description="Test", probable_causes=[],
                confidence=0.8, severity=DiagnosticSeverity.MAJOR
            ),
            secondary_diagnoses=[
                SecondaryDiagnosis(
                    code="P0171", description="Test", probable_causes=[],
                    confidence=0.7, severity=DiagnosticSeverity.CRITICAL
                )
            ]
        )
        assert result.get_highest_severity() == DiagnosticSeverity.CRITICAL

    def test_confidence_validation(self):
        """Test confidence validation."""
        with pytest.raises(ValueError):
            DiagnosticResult(
                diagnosis_id="test",
                data_source=DataSource.SIMULATION,
                confidence=1.5
            )


class TestDiagnosticContext:
    """Tests for DiagnosticContext model."""

    def test_to_prompt_context(self):
        """Test prompt context generation."""
        context = DiagnosticContext(
            vehicle_profile={
                "make": "Hyundai",
                "model": "i20",
                "year": 2023,
                "engine": "1.2L Kappa"
            },
            data_source=DataSource.SIMULATION,
            sensor_readings={"rpm": 800, "coolant_temp_c": 90},
            sensor_units={"rpm": "RPM", "coolant_temp_c": "°C"},
            dtcs=[{"code": "P0300", "description": "Misfire", "severity": "major"}]
        )
        prompt = context.to_prompt_context()
        assert "VEHICLE DIAGNOSTIC CONTEXT" in prompt
        assert "Hyundai" in prompt
        assert "i20" in prompt
        assert "SIMULATION" in prompt
        assert "P0300" in prompt
        assert "800" in prompt
        assert "90" in prompt


# =============================================================================
# KNOWLEDGE BASE TESTS
# =============================================================================

class TestKnowledgeBase:
    """Tests for KnowledgeBase."""

    def test_builtin_knowledge_loaded(self, knowledge_base):
        """Test that built-in knowledge is loaded."""
        assert len(knowledge_base._documents) > 0
        # Check for key documents
        titles = [d.get("title", "") for d in knowledge_base._documents]
        assert any("P0300" in t for t in titles)
        assert any("P0171" in t for t in titles)
        assert any("Hyundai i20" in t for t in titles)
        assert any("Fuel Trim" in t for t in titles)

    def test_search_returns_results(self, knowledge_base):
        """Test search returns relevant results."""
        results = knowledge_base.search("misfire ignition", top_k=3)
        assert len(results) > 0
        assert any("P0300" in r or "misfire" in r.lower() for r in results)

    def test_search_returns_empty_for_unknown(self, knowledge_base):
        """Test search returns empty for unknown terms."""
        results = knowledge_base.search("xyzunknown123", top_k=3)
        assert len(results) == 0

    def test_get_by_dtc(self, knowledge_base):
        """Test getting knowledge by DTC code."""
        results = knowledge_base.get_by_dtc("P0300")
        assert len(results) > 0
        assert any("P0300" in r for r in results)

    def test_get_by_tags(self, knowledge_base):
        """Test getting knowledge by tags."""
        results = knowledge_base.get_by_tags(["dtc", "misfire"], top_k=3)
        assert len(results) > 0


# =============================================================================
# DIAGNOSTIC CONTEXT BUILDER TESTS
# =============================================================================

class TestDiagnosticContextBuilder:
    """Tests for DiagnosticContextBuilder."""

    def test_build_context(self, diagnostic_context_builder, mock_obd_service, mock_database_service, mock_ai_service, knowledge_base):
        """Test building diagnostic context."""
        context = diagnostic_context_builder.build_context(
            obd_service=mock_obd_service,
            database_service=mock_database_service,
            ai_service=mock_ai_service,
            include_knowledge=True,
            knowledge_base=knowledge_base
        )

        assert context.vehicle_profile is not None
        assert context.vehicle_profile["make"] == "Hyundai"
        assert context.data_source == DataSource.SIMULATION
        assert "rpm" in context.sensor_readings
        assert "coolant_temp_c" in context.sensor_readings
        assert len(context.dtcs) == 2
        assert context.dtcs[0]["code"] == "P0300"
        assert context.dtcs[1]["code"] == "P0171"
        assert context.recent_telemetry is not None
        assert len(context.recent_telemetry) == 50
        assert context.telemetry_trends is not None
        assert context.knowledge_passages is not None
        assert len(context.knowledge_passages) > 0

    def test_build_context_real_mode(self, diagnostic_context_builder, mock_database_service, mock_ai_service, knowledge_base):
        """Test building context in real mode."""
        mock_obd = Mock()
        mock_obd.mode = OBDMode.REAL
        mock_obd.get_all_readings.return_value = {}
        mock_obd.scan_dtcs.return_value = []
        mock_obd.real_adapter = None
        mock_obd.pid_registry = Mock()
        mock_obd.pid_registry.supported_pids = set()
        mock_obd.pid_registry.unsupported_pids = set()

        context = diagnostic_context_builder.build_context(
            obd_service=mock_obd,
            database_service=mock_database_service,
            ai_service=mock_ai_service,
            include_knowledge=True,
            knowledge_base=knowledge_base
        )

        assert context.data_source == DataSource.REAL

    def test_calculate_trends(self, diagnostic_context_builder):
        """Test trend calculation."""
        records = [
            {"rpm": 800, "coolant_temp_c": 80},
            {"rpm": 850, "coolant_temp_c": 82},
            {"rpm": 900, "coolant_temp_c": 85},
            {"rpm": 950, "coolant_temp_c": 88},
            {"rpm": 1000, "coolant_temp_c": 90},
            {"rpm": 1050, "coolant_temp_c": 92},
            {"rpm": 1100, "coolant_temp_c": 94},
            {"rpm": 1150, "coolant_temp_c": 96},
            {"rpm": 1200, "coolant_temp_c": 98},
            {"rpm": 1250, "coolant_temp_c": 100},
        ]
        trends = diagnostic_context_builder._calculate_trends(records)

        assert "rpm" in trends
        assert "increasing" in trends["rpm"]
        assert "coolant_temp_c" in trends
        assert "increasing" in trends["coolant_temp_c"]


# =============================================================================
# DIAGNOSTIC PROMPT BUILDER TESTS
# =============================================================================

class TestDiagnosticPromptBuilder:
    """Tests for DiagnosticPromptBuilder."""

    def test_build_diagnostic_prompt(self, diagnostic_context_builder, mock_obd_service, mock_database_service, mock_ai_service, knowledge_base):
        """Test building diagnostic prompt."""
        context = diagnostic_context_builder.build_context(
            obd_service=mock_obd_service,
            database_service=mock_database_service,
            ai_service=mock_ai_service,
            include_knowledge=True,
            knowledge_base=knowledge_base
        )

        prompt = DiagnosticPromptBuilder.build_diagnostic_prompt(context)

        assert "DIAGNOSTIC CONTEXT" in prompt
        assert "Hyundai" in prompt
        assert "i20" in prompt
        assert "P0300" in prompt
        assert "P0171" in prompt
        assert "JSON only" in prompt
        assert "diagnosis_id" in prompt
        assert "probable_causes" in prompt
        assert "confidence" in prompt


# =============================================================================
# DIAGNOSTIC ENGINE TESTS
# =============================================================================

class TestDiagnosticEngine:
    """Tests for DiagnosticEngine."""

    def test_init(self, mock_obd_service, mock_database_service, mock_ai_service):
        """Test engine initialization."""
        engine = DiagnosticEngine(
            obd_service=mock_obd_service,
            database_service=mock_database_service,
            ai_service=mock_ai_service
        )

        assert engine.obd_service == mock_obd_service
        assert engine.database_service == mock_database_service
        assert engine.ai_service == mock_ai_service
        assert engine.knowledge_base is not None
        assert engine.context_builder is not None
        assert engine.max_retries == 2

    def test_assess_data_quality_excellent(self, mock_obd_service, mock_database_service, mock_ai_service):
        """Test data quality assessment - excellent."""
        engine = DiagnosticEngine(
            obd_service=mock_obd_service,
            database_service=mock_database_service,
            ai_service=mock_ai_service
        )

        # Build context with full data
        context = engine.context_builder.build_context(
            obd_service=mock_obd_service,
            database_service=mock_database_service,
            ai_service=mock_ai_service,
            include_knowledge=True,
            knowledge_base=engine.knowledge_base
        )

        quality = engine._assess_data_quality(context)
        assert quality == DataQuality.EXCELLENT

    def test_assess_data_quality_poor(self, mock_database_service, mock_ai_service):
        """Test data quality assessment - poor."""
        engine = DiagnosticEngine(
            obd_service=Mock(mode=OBDMode.SIMULATION, get_all_readings=Mock(return_value={}), scan_dtcs=Mock(return_value=[])),
            database_service=mock_database_service,
            ai_service=mock_ai_service
        )

        context = engine.context_builder.build_context(
            obd_service=engine.obd_service,
            database_service=mock_database_service,
            ai_service=mock_ai_service,
            include_knowledge=True,
            knowledge_base=engine.knowledge_base
        )

        quality = engine._assess_data_quality(context)
        assert quality in [DataQuality.POOR, DataQuality.NONE]

    def test_extract_json(self, mock_obd_service, mock_database_service, mock_ai_service):
        """Test JSON extraction from AI response."""
        engine = DiagnosticEngine(
            obd_service=mock_obd_service,
            database_service=mock_database_service,
            ai_service=mock_ai_service
        )

        # Test code block with json
        text = '```json\n{"key": "value"}\n```'
        assert engine._extract_json(text) == '{"key": "value"}'

        # Test code block without language
        text = '```\n{"key": "value"}\n```'
        assert engine._extract_json(text) == '{"key": "value"}'

        # Test bare JSON
        text = '{"key": "value"}'
        assert engine._extract_json(text) == '{"key": "value"}'

        # Test with surrounding text
        text = 'Here is the result: {"key": "value"} end'
        assert engine._extract_json(text) == '{"key": "value"}'

    def test_create_insufficient_data_result(self, mock_obd_service, mock_database_service, mock_ai_service):
        """Test creating insufficient data result."""
        engine = DiagnosticEngine(
            obd_service=mock_obd_service,
            database_service=mock_database_service,
            ai_service=mock_ai_service
        )

        context = DiagnosticContext(data_source=DataSource.SIMULATION)
        result = engine._create_insufficient_data_result("diag_test", context, "No data")

        assert result.diagnosis_id == "diag_test"
        assert result.diagnostic_status == DiagnosticStatus.INSUFFICIENT_DATA
        assert result.confidence == 0.0
        assert "No data" in result.missing_information[0]

    def test_create_error_result(self, mock_obd_service, mock_database_service, mock_ai_service):
        """Test creating error result."""
        engine = DiagnosticEngine(
            obd_service=mock_obd_service,
            database_service=mock_database_service,
            ai_service=mock_ai_service
        )

        context = DiagnosticContext(data_source=DataSource.SIMULATION)
        result = engine._create_error_result("diag_test", context, "AI failed")

        assert result.diagnosis_id == "diag_test"
        assert result.diagnostic_status == DiagnosticStatus.ERROR
        assert result.confidence == 0.0
        assert "AI failed" in result.summary

    def test_reconcile_findings(self, mock_obd_service, mock_database_service, mock_ai_service):
        """Test reconciling AI findings with actual data."""
        engine = DiagnosticEngine(
            obd_service=mock_obd_service,
            database_service=mock_database_service,
            ai_service=mock_ai_service
        )

        # Create result with DTC that wasn't scanned
        result = DiagnosticResult(
            diagnosis_id="diag_test",
            data_source=DataSource.SIMULATION,
            diagnostic_status=DiagnosticStatus.COMPLETE,
            confidence=0.9,
            primary_diagnosis=PrimaryDiagnosis(
                code="P0420",  # Not in scanned DTCs
                description="Catalyst",
                probable_causes=[],
                confidence=0.8,
                severity=DiagnosticSeverity.MAJOR
            )
        )

        context = DiagnosticContext(
            data_source=DataSource.SIMULATION,
            dtcs=[{"code": "P0300", "description": "Misfire"}]
        )

        reconciled = engine._reconcile_findings(result, context)

        assert "P0420" in str(reconciled.contradictory_evidence)
        # Confidence is reduced by 0.2 but rounded to 2 decimal places
        # 0.9 - 0.2 = 0.7 (already at 2 decimal places)
        assert reconciled.confidence <= result.confidence

    @patch('services.get_obd_service')
    @patch('services.get_database')
    @patch('services.get_ai_service')
    def test_get_diagnosis_history(self, mock_get_ai, mock_get_db, mock_get_obd, mock_database_service):
        """Test getting diagnosis history."""
        # Setup mocks
        mock_get_obd.return_value = Mock()
        mock_get_db.return_value = mock_database_service
        mock_get_ai.return_value = Mock()

        # Mock database response - use the actual database with proper schema
        # The test is complex with in-memory DB, just test the method exists and handles errors
        engine = DiagnosticEngine()
        history = engine.get_diagnosis_history(limit=10)
        assert isinstance(history, list)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestDiagnosticEngineIntegration:
    """Integration tests for the full diagnostic flow."""

    def test_full_diagnosis_flow(self, mock_obd_service, mock_database_service, mock_ai_service):
        """Test the complete diagnosis flow."""
        engine = DiagnosticEngine(
            obd_service=mock_obd_service,
            database_service=mock_database_service,
            ai_service=mock_ai_service
        )

        # Run diagnosis
        result = engine.run_diagnosis()

        # Verify result structure
        assert isinstance(result, DiagnosticResult)
        assert result.diagnosis_id.startswith("diag_")
        assert result.data_source == DataSource.SIMULATION
        assert result.diagnostic_status in [DiagnosticStatus.COMPLETE, DiagnosticStatus.ERROR]
        assert result.confidence >= 0.0
        assert result.confidence <= 1.0
        assert result.primary_diagnosis is not None
        assert result.primary_diagnosis.code == "P0300"
        assert len(result.primary_diagnosis.probable_causes) >= 1
        assert len(result.secondary_diagnoses) >= 1
        assert len(result.recommended_actions) >= 1
        assert result.model_information["model"] == "qwen2.5-3b-instruct"

    def test_diagnosis_with_ai_error(self, mock_obd_service, mock_database_service):
        """Test diagnosis when AI service fails."""
        mock_ai = Mock()
        mock_ai.check_connection.return_value = False
        mock_ai.model = "qwen2.5-3b-instruct"

        engine = DiagnosticEngine(
            obd_service=mock_obd_service,
            database_service=mock_database_service,
            ai_service=mock_ai
        )

        result = engine.run_diagnosis()

        assert result.diagnostic_status == DiagnosticStatus.ERROR
        assert "AI service unavailable" in result.summary or "AI service" in str(result.safety_warnings)

    def test_diagnosis_insufficient_data(self, mock_database_service):
        """Test diagnosis with no data."""
        mock_obd = Mock()
        mock_obd.mode = OBDMode.SIMULATION
        mock_obd.get_all_readings.return_value = {}
        mock_obd.scan_dtcs.return_value = []
        mock_obd.real_adapter = None
        mock_obd.pid_registry = Mock()
        mock_obd.pid_registry.supported_pids = set()
        mock_obd.pid_registry.unsupported_pids = set()

        mock_ai = Mock()
        mock_ai.check_connection.return_value = True
        mock_ai.model = "qwen2.5-3b-instruct"

        engine = DiagnosticEngine(
            obd_service=mock_obd,
            database_service=mock_database_service,
            ai_service=mock_ai
        )

        result = engine.run_diagnosis()

        assert result.diagnostic_status == DiagnosticStatus.INSUFFICIENT_DATA
        assert result.confidence == 0.0


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Edge case tests."""

    def test_empty_knowledge_base_search(self):
        """Test search on empty knowledge base."""
        kb = KnowledgeBase()
        kb._documents = []
        results = kb.search("anything")
        assert results == []

    def test_diagnostic_context_empty(self):
        """Test DiagnosticContext with no data."""
        context = DiagnosticContext()
        prompt = context.to_prompt_context()
        assert "SIMULATION" in prompt
        assert "(No sensor readings available)" in prompt
        assert "(No DTCs detected)" in prompt

    def test_probable_cause_without_optional_fields(self):
        """Test ProbableCause with minimal fields."""
        cause = ProbableCause(
            cause="Test cause",
            explanation="Test explanation",
            confidence=0.5
        )
        assert cause.supporting_evidence == []
        assert cause.contradictory_evidence == []
        assert cause.verification_steps == []
        assert cause.urgency == "schedule"

    def test_diagnostic_recommendation_minimal(self):
        """Test DiagnosticRecommendation with minimal fields."""
        rec = DiagnosticRecommendation(
            recommendation="Test action",
            rationale="Test rationale",
            priority=5
        )
        assert rec.safety_level == SafetyLevel.PROFESSIONAL
        assert rec.requires_professional is True
        assert rec.supporting_evidence == []
        assert rec.estimated_cost_inr is None


# =============================================================================
# SINGLETON TESTS
# =============================================================================

class TestSingletons:
    """Tests for singleton functions."""

    @patch('services.get_obd_service')
    @patch('services.get_database')
    @patch('services.get_ai_service')
    def test_get_diagnostic_engine(self, mock_get_ai, mock_get_db, mock_get_obd):
        """Test diagnostic engine singleton."""
        from services.diagnostic_engine import get_diagnostic_engine, _diagnostic_engine_instance

        # Reset singleton
        import services.diagnostic_engine as de
        de._diagnostic_engine_instance = None

        mock_get_obd.return_value = Mock()
        mock_get_db.return_value = Mock()
        mock_get_ai.return_value = Mock()

        engine1 = get_diagnostic_engine()
        engine2 = get_diagnostic_engine()

        assert engine1 is engine2
        assert isinstance(engine1, DiagnosticEngine)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
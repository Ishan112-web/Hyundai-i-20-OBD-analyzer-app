"""
i20 AI Garage - Diagnostic Engine

Orchestrates AI-powered diagnostics using LM Studio.
Integrates with existing OBD service, simulation engine, database, and knowledge base.
Includes Deterministic Rule Engine integration (Phase 3).
"""

import json
import logging
import uuid
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

from services.types import SensorReading, DTC, OBDMode, ConnectionState
from services.diagnostic_models import (
    DiagnosticResult, DiagnosticContext, ProbableCause, PrimaryDiagnosis,
    SecondaryDiagnosis, DiagnosticRecommendation, DiagnosticSeverity,
    DiagnosticStatus, DataSource, DataQuality, SafetyLevel, VehicleProfile
)

# Rule Engine imports (Phase 3)
try:
    from services.rule_engine import RuleEngine, get_rule_engine
    from services.rule_models import RuleEvaluationResult, RuleFinding, RuleSeverity, DataSource as RuleDataSource
    RULE_ENGINE_AVAILABLE = True
except ImportError:
    RULE_ENGINE_AVAILABLE = False
    RuleEngine = None
    RuleEvaluationResult = None
    RuleFinding = None
    RuleSeverity = None
    RuleDataSource = None
    get_rule_engine = None

logger = logging.getLogger(__name__)


# =============================================================================
# KNOWLEDGE BASE
# =============================================================================

class KnowledgeBase:
    """Lightweight local knowledge base for automotive diagnostics."""

    def __init__(self, knowledge_dir: Optional[Path] = None):
        self.knowledge_dir = knowledge_dir or Path("services/knowledge")
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        self._documents: List[Dict[str, Any]] = []
        self._load_builtin_knowledge()

    def _load_builtin_knowledge(self):
        """Load built-in automotive knowledge."""
        # DTC explanations
        self._documents.extend([
            {
                "source": "builtin",
                "title": "P0300 - Random/Multiple Cylinder Misfire",
                "content": (
                    "P0300 indicates random or multiple cylinder misfire detected. "
                    "Common causes: faulty spark plugs, ignition coils, fuel injectors, "
                    "vacuum leaks, low fuel pressure, compression issues, or ECM problems. "
                    "Verification: check spark plug condition, test ignition coil resistance, "
                    "verify fuel pressure, smoke test for vacuum leaks, compression test."
                ),
                "tags": ["dtc", "p0300", "misfire", "ignition", "fuel"],
                "metadata": {"dtc_code": "P0300", "system": "powertrain"}
            },
            {
                "source": "builtin",
                "title": "P0171 - System Too Lean (Bank 1)",
                "content": (
                    "P0171 indicates the ECM has detected a lean condition on Bank 1 "
                    "(too much air, not enough fuel). Common causes: vacuum leaks downstream "
                    "of MAF sensor, faulty MAF sensor, clogged fuel filter, weak fuel pump, "
                    "exhaust leak before O2 sensor, faulty fuel injectors. "
                    "Verification: inspect intake system for leaks, clean/test MAF sensor, "
                    "check fuel pressure and flow, inspect exhaust for leaks, monitor fuel trims."
                ),
                "tags": ["dtc", "p0171", "lean", "fuel", "air"],
                "metadata": {"dtc_code": "P0171", "system": "fuel"}
            },
            {
                "source": "builtin",
                "title": "P0420 - Catalyst System Efficiency Below Threshold (Bank 1)",
                "content": (
                    "P0420 indicates the catalytic converter is not operating efficiently. "
                    "Common causes: aged catalytic converter, exhaust leak, faulty downstream "
                    "O2 sensor, engine running rich/lean, PCM software issue. "
                    "Verification: check for exhaust leaks, monitor O2 sensor switching, "
                    "verify fuel trim values, check for related TSBs."
                ),
                "tags": ["dtc", "p0420", "catalyst", "exhaust", "emissions"],
                "metadata": {"dtc_code": "P0420", "system": "emissions"}
            },
            {
                "source": "builtin",
                "title": "P0128 - Coolant Thermostat (Temperature Below Regulating Temperature)",
                "content": (
                    "P0128 indicates the engine coolant temperature is not reaching "
                    "the expected temperature within the specified time. "
                    "Common causes: thermostat stuck open, faulty ECT sensor, low coolant level, "
                    "cooling fan stuck on, PCM calibration issue. "
                    "Verification: verify coolant level/condition, test thermostat operation, "
                    "check ECT sensor resistance, monitor warm-up cycle, inspect cooling fan."
                ),
                "tags": ["dtc", "p0128", "coolant", "thermostat", "cooling"],
                "metadata": {"dtc_code": "P0128", "system": "cooling"}
            },
            {
                "source": "builtin",
                "title": "Hyundai i20 1.2L Kappa Engine - Common Issues",
                "content": (
                    "Hyundai i20 Asta 2023 with 1.2L Kappa naturally aspirated engine: "
                    "Known issues include: 1) Ignition coil failures (especially cylinders 2&3), "
                    "2) Throttle body carbon buildup causing idle issues, "
                    "3) Purge valve solenoid failures causing EVAP codes (P0441, P0455), "
                    "4) O2 sensor heater circuit issues, "
                    "5) Fuel pump controller module failures. "
                    "Maintenance: Spark plugs at 40,000km, throttle body cleaning at 30,000km, "
                    "fuel system cleaning at 20,000km intervals."
                ),
                "tags": ["hyundai", "i20", "kappa", "1.2l", "common_issues"],
                "metadata": {"vehicle": "i20_asta_2023", "engine": "kappa_1.2l"}
            },
            {
                "source": "builtin",
                "title": "Diagnostic Principles - Fuel Trim Analysis",
                "content": (
                    "Fuel trim interpretation: STFT (Short Term Fuel Trim) reacts immediately "
                    "to O2 sensor feedback. LTFT (Long Term Fuel Trim) learns over time. "
                    "Positive trims = ECU adding fuel (lean condition). Negative trims = ECU "
                    "reducing fuel (rich condition). Normal range: ±5%. "
                    "STFT + LTFT > +10% = significant lean condition (vacuum leak, MAF, fuel). "
                    "STFT + LTFT < -10% = significant rich condition (leaking injector, FPR). "
                    "Both trims high at idle but normal at load = vacuum leak. "
                    "Both trims high at all loads = fuel delivery or MAF issue."
                ),
                "tags": ["diagnostic", "fuel_trim", "stft", "ltft", "lean", "rich"],
                "metadata": {"category": "diagnostic_principle"}
            },
            {
                "source": "builtin",
                "title": "Diagnostic Principles - Cooling System",
                "content": (
                    "Normal coolant temperature: 85-100°C (185-212°F) at operating temp. "
                    "Overheating > 105°C: Check thermostat, water pump, radiator, coolant level, "
                    "cooling fan, head gasket. Thermostat stuck open = slow warm-up, P0128. "
                    "Thermostat stuck closed = rapid overheating. "
                    "Cooling fan should activate at ~95-100°C. "
                    "Pressure test cooling system for head gasket leaks (bubbles in reservoir)."
                ),
                "tags": ["diagnostic", "cooling", "thermostat", "overheating", "coolant"],
                "metadata": {"category": "diagnostic_principle"}
            },
            {
                "source": "builtin",
                "title": "Diagnostic Principles - Ignition System",
                "content": (
                    "Misfire diagnosis: P0300 random, P0301-P0304 cylinder specific. "
                    "Swap test: swap coil/plug/injector to adjacent cylinder, if code follows "
                    "component is faulty. Compression test: should be >130 psi, <10% variance. "
                    "Common: worn spark plugs (40k km interval), failed ignition coils, "
                    "carbon tracking on plugs/boots, fuel injector issues. "
                    "Check ignition coil primary resistance (~0.5-1.5 ohm) and secondary (~8-15k ohm)."
                ),
                "tags": ["diagnostic", "ignition", "misfire", "coil", "spark_plug"],
                "metadata": {"category": "diagnostic_principle"}
            },
        ])

        # Try to load additional knowledge files
        self._load_knowledge_files()

    def _load_knowledge_files(self):
        """Load knowledge from JSON files in knowledge directory."""
        for file_path in self.knowledge_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self._documents.extend(data)
                    elif isinstance(data, dict):
                        self._documents.append(data)
            except Exception as e:
                logger.warning(f"Failed to load knowledge file {file_path}: {e}")

    def search(self, query: str, top_k: int = 5) -> List[str]:
        """Simple keyword-based search for relevant knowledge passages."""
        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored_docs = []
        for doc in self._documents:
            content = f"{doc.get('title', '')} {doc.get('content', '')} {' '.join(doc.get('tags', []))}".lower()
            content_words = set(content.split())

            # Score based on word overlap
            overlap = len(query_words & content_words)
            if overlap > 0:
                scored_docs.append((overlap, doc))

        # Sort by score descending
        scored_docs.sort(key=lambda x: x[0], reverse=True)

        # Return top passages
        results = []
        for score, doc in scored_docs[:top_k]:
            passage = f"[{doc.get('source', 'knowledge').upper()}] {doc.get('title', 'Untitled')}: {doc.get('content', '')}"
            results.append(passage)

        return results

    def get_by_dtc(self, dtc_code: str) -> List[str]:
        """Get knowledge passages specific to a DTC code."""
        dtc_lower = dtc_code.lower()
        results = []
        for doc in self._documents:
            meta = doc.get('metadata', {})
            if meta.get('dtc_code', '').lower() == dtc_lower:
                results.append(f"[{doc.get('source', 'knowledge').upper()}] {doc.get('title', 'Untitled')}: {doc.get('content', '')}")
        return results

    def get_by_tags(self, tags: List[str], top_k: int = 3) -> List[str]:
        """Get knowledge passages by tags."""
        tag_set = set(t.lower() for t in tags)
        results = []
        for doc in self._documents:
            doc_tags = set(t.lower() for t in doc.get('tags', []))
            if tag_set & doc_tags:
                results.append(f"[{doc.get('source', 'knowledge').upper()}] {doc.get('title', 'Untitled')}: {doc.get('content', '')}")
        return results[:top_k]


# =============================================================================
# DIAGNOSTIC CONTEXT BUILDER
# =============================================================================

class DiagnosticContextBuilder:
    """Builds diagnostic context from existing vehicle services."""

    def __init__(self):
        pass

    def build_context(
        self,
        obd_service,
        database_service,
        ai_service,
        include_knowledge: bool = True,
        knowledge_base: Optional[KnowledgeBase] = None
    ) -> DiagnosticContext:
        """Build complete diagnostic context from available services."""
        context = DiagnosticContext()

        # Vehicle profile
        vehicle_profile = database_service.get_vehicle_profile()
        if vehicle_profile:
            context.vehicle_profile = vehicle_profile

        # Data source
        context.data_source = DataSource.REAL if obd_service.mode == OBDMode.REAL else DataSource.SIMULATION

        # Current sensor readings
        readings = obd_service.get_all_readings()
        if readings:
            context.sensor_readings = {k: v.value for k, v in readings.items()}
            context.sensor_units = {k: v.unit for k, v in readings.items()}
            context.sensor_timestamps = {k: v.timestamp.isoformat() for k, v in readings.items()}

            # Data freshness
            if readings:
                latest = max(v.timestamp for v in readings.values())
                context.data_freshness_seconds = (datetime.now() - latest).total_seconds()

        # DTCs
        dtcs = obd_service.scan_dtcs()
        if dtcs:
            context.dtcs = [
                {
                    "code": d.code,
                    "description": d.description,
                    "severity": d.severity,
                    "status": d.status,
                    "is_demo": d.is_demo
                }
                for d in dtcs
            ]

        # Freeze frame (if available)
        if obd_service.mode == OBDMode.REAL and obd_service.real_adapter:
            for dtc in dtcs:
                ff = obd_service.real_adapter.get_freeze_frame(dtc.code)
                if ff:
                    context.freeze_frame = {
                        "rpm": ff.rpm,
                        "speed_kmh": ff.speed_kmh,
                        "coolant_temp_c": ff.coolant_temp_c,
                        "throttle_pos_pct": ff.throttle_pos_pct,
                        "engine_load_pct": ff.engine_load_pct,
                        "map_kpa": ff.map_kpa,
                        "maf_g_s": ff.maf_g_s,
                    }
                    break

        # Recent telemetry trends (from active session)
        active_session = database_service.get_active_session()
        if active_session:
            records = database_service.get_session_records(active_session["id"])
            if len(records) >= 10:
                context.recent_telemetry = records[-50:]  # Last 50 records
                context.telemetry_trends = self._calculate_trends(records[-50:])

        # Diagnostic history
        diag_reports = database_service.get_diagnostic_reports(limit=5)
        context.diagnostic_history = diag_reports

        # Unsupported PIDs
        if obd_service.mode == OBDMode.REAL and obd_service.pid_registry:
            context.unsupported_pids = list(obd_service.pid_registry.unsupported_pids)
            # Missing measurements (standard PIDs not supported)
            standard_pids = ["0C", "0D", "05", "11", "04", "0B", "06", "07", "42", "10", "0F"]
            supported = set(obd_service.pid_registry.supported_pids)
            context.missing_measurements = [pid for pid in standard_pids if pid not in supported]

        # Knowledge retrieval
        if include_knowledge and knowledge_base:
            query_terms = []
            for dtc in context.dtcs:
                query_terms.append(dtc.get("code", ""))
            if context.sensor_readings:
                # Add terms for abnormal readings - convert to float for comparison
                def get_float(key, default=0.0):
                    try:
                        return float(context.sensor_readings.get(key, default))
                    except (ValueError, TypeError):
                        return default

                if get_float("coolant_temp_c") > 105:
                    query_terms.extend(["overheating", "cooling"])
                if get_float("stft_b1_pct") > 15:
                    query_terms.extend(["lean", "fuel_trim"])
                if get_float("rpm") > 5000:
                    query_terms.extend(["high_rpm"])

            if query_terms:
                context.knowledge_passages = knowledge_base.search(" ".join(query_terms), top_k=5)

            # Add DTC-specific knowledge
            for dtc in context.dtcs:
                dtc_knowledge = knowledge_base.get_by_dtc(dtc.get("code", ""))
                context.knowledge_passages.extend(dtc_knowledge)

        return context

    def _calculate_trends(self, records: List[Dict]) -> Dict[str, str]:
        """Calculate simple trends from recent telemetry records."""
        if len(records) < 5:
            return {}

        trends = {}
        params = ["rpm", "speed_kmh", "coolant_temp_c", "throttle_pos_pct",
                  "engine_load_pct", "stft_b1_pct", "ltft_b1_pct", "voltage_v"]

        for param in params:
            values = [r.get(param) for r in records if r.get(param) is not None]
            if len(values) >= 5:
                # Simple linear trend: compare first half vs second half
                mid = len(values) // 2
                first_half_avg = sum(values[:mid]) / mid
                second_half_avg = sum(values[mid:]) / (len(values) - mid)

                diff = second_half_avg - first_half_avg
                pct_change = (diff / first_half_avg * 100) if first_half_avg != 0 else 0

                if abs(pct_change) < 2:
                    trends[param] = "stable"
                elif pct_change > 0:
                    trends[param] = f"increasing ({pct_change:+.1f}%)"
                else:
                    trends[param] = f"decreasing ({pct_change:+.1f}%)"

        return trends


# =============================================================================
# AI DIAGNOSTIC PROMPT BUILDER
# =============================================================================

class DiagnosticPromptBuilder:
    """Builds structured prompts for AI diagnostic requests."""

    DIAGNOSTIC_SYSTEM_PROMPT = """You are an expert automotive diagnostician specializing in Hyundai vehicles.
Given DTC codes, live telemetry, and vehicle context, provide structured diagnosis in JSON format.

VEHICLE: 2023 Hyundai i20 Asta, 1.2L Kappa naturally aspirated petrol, Manual 5-speed, India market (BS6)

OUTPUT FORMAT: JSON only, matching this schema:
{
  "diagnosis_id": "diag_YYYYMMDD_NNN",
  "diagnostic_status": "complete|inconclusive|error|insufficient_data",
  "severity": "critical|major|minor|info|unknown",
  "confidence": 0.0-1.0,
  "summary": "Human-readable summary",
  "detected_symptoms": ["symptom1", "symptom2"],
  "confirmed_faults": ["DTC codes from scan"],
  "primary_diagnosis": {
    "code": "PXXXX",
    "description": "DTC description",
    "probable_causes": [
      {"cause": "Cause description", "explanation": "Why this causes symptoms", "confidence": 0.0-1.0, "supporting_evidence": [], "contradictory_evidence": [], "verification_steps": [], "urgency": "immediate|soon|schedule|monitor"}
    ],
    "confidence": 0.0-1.0,
    "severity": "critical|major|minor|info"
  },
  "secondary_diagnoses": [...],
  "supporting_evidence": ["evidence1", "evidence2"],
  "contradictory_evidence": ["evidence1"],
  "recommended_checks": ["check1", "check2"],
  "recommended_actions": [
    {"recommendation": "Action", "rationale": "Why", "priority": 1-10, "safety_level": "safe|caution|professional", "requires_professional": true, "supporting_evidence": [], "estimated_cost_inr": "₹X-₹Y"}
  ],
  "safety_warnings": ["warning1"],
  "missing_information": ["missing1"],
  "data_quality": "excellent|good|fair|poor|none",
  "dtc_references": ["PXXXX"],
  "rule_engine_findings": ["RULE_XXX"],
  "rag_sources": ["source1", "source2"]
}

RULES:
1. Always include confidence scores (0.0-1.0) - be honest about uncertainty
2. Rank probable causes by probability (highest first)
3. Reference Hyundai/Kia service bulletins where applicable
4. Consider i20 Asta 2023 specific known issues (Kappa 1.2L engine)
5. Flag safety-critical issues with severity="critical"
6. Include estimated repair costs in INR for Indian market
7. If data is insufficient, set diagnostic_status to "insufficient_data" and explain what's missing
8. Distinguish simulation data from real data clearly
9. Never invent readings or confirm faults without evidence
10. Provide specific, actionable verification steps for each probable cause
11. Include contradictory evidence when observations don't support a cause
12. For simulation data, add disclaimer: "SIMULATION DATA — NOT ACTUAL VEHICLE DATA"
"""

    @classmethod
    def build_diagnostic_prompt(cls, context: DiagnosticContext) -> str:
        """Build the complete diagnostic prompt."""
        context_str = context.to_prompt_context()

        prompt = f"""{cls.DIAGNOSTIC_SYSTEM_PROMPT}

{context_str}

Provide your diagnosis as JSON only. No additional text or explanation."""

        return prompt


# =============================================================================
# DIAGNOSTIC ENGINE (MAIN ORCHESTRATOR)
# =============================================================================

class DiagnosticEngine:
    """Main orchestrator for AI-powered diagnostics with Rule Engine integration (Phase 3)."""

    def __init__(
        self,
        obd_service=None,
        database_service=None,
        ai_service=None,
        knowledge_base: Optional[KnowledgeBase] = None,
        rule_engine: Optional["RuleEngine"] = None
    ):
        self.obd_service = obd_service
        self.database_service = database_service
        self.ai_service = ai_service
        self.knowledge_base = knowledge_base or KnowledgeBase()
        self.context_builder = DiagnosticContextBuilder()

        # Rule Engine (Phase 3)
        self.rule_engine = rule_engine
        self._rule_engine_available = RULE_ENGINE_AVAILABLE

        # Retry configuration
        self.max_retries = 2
        self.retry_delay = 1.0

    def run_diagnosis(
        self,
        session_id: Optional[str] = None,
        force_refresh: bool = False
    ) -> DiagnosticResult:
        """
        Run a complete AI diagnosis.

        Args:
            session_id: Optional telemetry session ID
            force_refresh: Force refresh of context

        Returns:
            DiagnosticResult with structured diagnosis
        """
        diagnosis_id = f"diag_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

        try:
            # 1. Build context
            logger.info("Building diagnostic context...")
            context = self.context_builder.build_context(
                obd_service=self.obd_service,
                database_service=self.database_service,
                ai_service=self.ai_service,
                include_knowledge=True,
                knowledge_base=self.knowledge_base
            )

            # 2. Run Rule Engine evaluation (Phase 3)
            rule_evaluation_result = None
            if self._rule_engine_available and self.rule_engine:
                logger.info("Running deterministic rule evaluation...")
                rule_evaluation_result = self._run_rule_evaluation(context, session_id)
                self._merge_rule_findings_into_context(context, rule_evaluation_result)

            # 3. Validate data quality
            data_quality = self._assess_data_quality(context)
            logger.info(f"Data quality assessed: {data_quality.value}")

            # 4. If insufficient data, return early
            if data_quality == DataQuality.NONE:
                return self._create_insufficient_data_result(diagnosis_id, context, "No telemetry or DTC data available")

            # 5. Build prompt
            prompt = DiagnosticPromptBuilder.build_diagnostic_prompt(context)

            # 6. Call AI service
            ai_result = self._call_ai_with_retry(prompt, context)

            if not ai_result:
                return self._create_error_result(diagnosis_id, context, "AI service unavailable or failed")

            # 7. Parse and validate AI response
            diagnostic_result = self._parse_ai_response(
                ai_result, diagnosis_id, context, data_quality
            )

            # 8. Add rule engine findings to result
            if rule_evaluation_result:
                diagnostic_result.rule_engine_findings = self._extract_rule_findings(rule_evaluation_result)

            # 9. Reconcile with actual observations
            diagnostic_result = self._reconcile_findings(diagnostic_result, context)

            # 10. Save to database
            self._save_diagnosis(diagnostic_result, session_id)

            logger.info(f"Diagnosis complete: {diagnosis_id} - Status: {diagnostic_result.diagnostic_status.value}")
            return diagnostic_result

        except Exception as e:
            logger.error(f"Diagnosis failed: {e}", exc_info=True)
            return self._create_error_result(diagnosis_id, DiagnosticContext(), str(e))

    def _run_rule_evaluation(self, context: DiagnosticContext, session_id: Optional[str]) -> Optional["RuleEvaluationResult"]:
        """Run deterministic rule engine evaluation."""
        try:
            if not self.rule_engine:
                # Try to get singleton instance
                if get_rule_engine:
                    self.rule_engine = get_rule_engine()
                else:
                    return None

            # Convert context sensor readings to SensorReading objects
            current_readings = {}
            for key, value in context.sensor_readings.items():
                unit = context.sensor_units.get(key, "")
                timestamp_str = context.sensor_timestamps.get(key)
                timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.now()
                is_simulated = (context.data_source == DataSource.SIMULATION)
                current_readings[key] = SensorReading(
                    pid=key,
                    name=key,
                    value=value,
                    unit=unit,
                    timestamp=timestamp,
                    is_simulated=is_simulated
                )

            # Build vehicle profile
            vehicle_profile = None
            if context.vehicle_profile:
                vehicle_profile = VehicleProfile(**context.vehicle_profile)

            # Build active DTCs
            active_dtcs = []
            for dtc_data in context.dtcs:
                active_dtcs.append(DTC(
                    code=dtc_data.get("code", ""),
                    description=dtc_data.get("description", ""),
                    severity=dtc_data.get("severity", "unknown"),
                    status=dtc_data.get("status", "active"),
                    is_demo=dtc_data.get("is_demo", True)
                ))

            # Set data source on rule engine
            rule_data_source = RuleDataSource.SIMULATION if context.data_source == DataSource.SIMULATION else RuleDataSource.REAL
            self.rule_engine.set_data_source(rule_data_source)

            # Run evaluation
            result = self.rule_engine.evaluate(
                current_readings=current_readings,
                vehicle_profile=vehicle_profile,
                active_dtcs=active_dtcs,
                diagnostic_session_id=session_id
            )

            logger.info(f"Rule evaluation complete: {result.rules_evaluated} rules, {len(result.findings)} findings")
            return result

        except Exception as e:
            logger.warning(f"Rule engine evaluation failed (continuing without): {e}")
            return None

    def _merge_rule_findings_into_context(self, context: DiagnosticContext, rule_result: "RuleEvaluationResult"):
        """Merge rule engine findings into diagnostic context for AI prompt."""
        if not rule_result or not rule_result.findings:
            return

        # Convert findings to format for context
        rule_findings = []
        for finding in rule_result.findings:
            finding_text = (
                f"[{finding.rule_id}] {finding.rule_name}: {finding.summary} "
                f"(Severity: {finding.severity.value}, Confidence: {finding.confidence:.0%})"
            )
            if finding.explanation:
                finding_text += f" - {finding.explanation}"
            rule_findings.append(finding_text)

        # Add to context
        context.rule_findings = rule_findings

    def _extract_rule_findings(self, rule_result: "RuleEvaluationResult") -> List[str]:
        """Extract rule finding IDs for the diagnostic result."""
        if not rule_result or not rule_result.findings:
            return []
        return [finding.rule_id for finding in rule_result.findings]

    def _assess_data_quality(self, context: DiagnosticContext) -> DataQuality:
        """Assess the quality of diagnostic data."""
        score = 0

        # Has sensor readings
        if context.sensor_readings:
            score += 30
            # Has key sensors
            key_sensors = ["rpm", "coolant_temp_c", "engine_load_pct"]
            if all(s in context.sensor_readings for s in key_sensors):
                score += 20

        # Has DTCs
        if context.dtcs:
            score += 30

        # Has recent telemetry
        if context.recent_telemetry:
            score += 10

        # Data freshness
        if context.data_freshness_seconds is not None:
            if context.data_freshness_seconds < 10:
                score += 10
            elif context.data_freshness_seconds < 60:
                score += 5

        if score >= 80:
            return DataQuality.EXCELLENT
        elif score >= 60:
            return DataQuality.GOOD
        elif score >= 40:
            return DataQuality.FAIR
        elif score >= 20:
            return DataQuality.POOR
        else:
            return DataQuality.NONE

    def _call_ai_with_retry(
        self,
        prompt: str,
        context: DiagnosticContext
    ) -> Optional[str]:
        """Call AI service with retry logic."""
        if not self.ai_service:
            logger.error("AI service not available")
            return None

        # Check connection
        if not self.ai_service.check_connection():
            logger.warning("LM Studio not connected")
            return None

        messages = [
            type('ChatMessage', (object,), {"role": "system", "content": DiagnosticPromptBuilder.DIAGNOSTIC_SYSTEM_PROMPT})(),
            type('ChatMessage', (object,), {"role": "user", "content": prompt})()
        ]

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                # Use higher token limit for structured output
                response = self.ai_service.chat_completion(
                    messages=messages,
                    temperature=0.1,  # Low temperature for consistent structured output
                    max_tokens=4096
                )

                if response and response.content:
                    return response.content

            except Exception as e:
                last_error = e
                logger.warning(f"AI call attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries:
                    import time
                    time.sleep(self.retry_delay)

        logger.error(f"AI call failed after {self.max_retries + 1} attempts: {last_error}")
        return None

    def _parse_ai_response(
        self,
        ai_response: str,
        diagnosis_id: str,
        context: DiagnosticContext,
        data_quality: DataQuality
    ) -> DiagnosticResult:
        """Parse and validate AI response into DiagnosticResult."""
        # Extract JSON from response
        json_str = self._extract_json(ai_response)

        if not json_str:
            logger.error("No valid JSON found in AI response")
            return self._create_error_result(
                diagnosis_id, context, "Invalid AI response format"
            )

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return self._create_error_result(
                diagnosis_id, context, f"Invalid JSON: {e}"
            )

        # Validate and construct DiagnosticResult
        try:
            result = self._construct_diagnostic_result(data, diagnosis_id, context, data_quality, ai_response)
            return result
        except Exception as e:
            logger.error(f"Failed to construct diagnostic result: {e}")
            return self._create_error_result(diagnosis_id, context, f"Response validation failed: {e}")

    def _extract_json(self, text: str) -> Optional[str]:
        """Extract JSON from AI response text."""
        # Try to find JSON block
        text = text.strip()

        # Look for code block
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()

        # Look for ``` without language
        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()

        # Try to find first { and last }
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace > first_brace:
            return text[first_brace:last_brace + 1]

        return None

    def _construct_diagnostic_result(
        self,
        data: Dict,
        diagnosis_id: str,
        context: DiagnosticContext,
        data_quality: DataQuality,
        raw_response: str
    ) -> DiagnosticResult:
        """Construct DiagnosticResult from parsed JSON."""

        # Parse primary diagnosis
        primary = None
        if data.get("primary_diagnosis"):
            pd = data["primary_diagnosis"]
            probable_causes = []
            for pc in pd.get("probable_causes", []):
                probable_causes.append(ProbableCause(
                    cause=pc.get("cause", ""),
                    explanation=pc.get("explanation", ""),
                    confidence=pc.get("confidence", 0.0),
                    supporting_evidence=pc.get("supporting_evidence", []),
                    contradictory_evidence=pc.get("contradictory_evidence", []),
                    verification_steps=pc.get("verification_steps", []),
                    urgency=pc.get("urgency", "schedule")
                ))

            primary = PrimaryDiagnosis(
                code=pd.get("code", ""),
                description=pd.get("description", ""),
                probable_causes=probable_causes,
                confidence=pd.get("confidence", 0.0),
                severity=DiagnosticSeverity(pd.get("severity", "unknown"))
            )

        # Parse secondary diagnoses
        secondary = []
        for sd in data.get("secondary_diagnoses", []):
            probable_causes = []
            for pc in sd.get("probable_causes", []):
                probable_causes.append(ProbableCause(
                    cause=pc.get("cause", ""),
                    explanation=pc.get("explanation", ""),
                    confidence=pc.get("confidence", 0.0),
                    supporting_evidence=pc.get("supporting_evidence", []),
                    contradictory_evidence=pc.get("contradictory_evidence", []),
                    verification_steps=pc.get("verification_steps", []),
                    urgency=pc.get("urgency", "schedule")
                ))

            secondary.append(SecondaryDiagnosis(
                code=sd.get("code", ""),
                description=sd.get("description", ""),
                probable_causes=probable_causes,
                confidence=sd.get("confidence", 0.0),
                severity=DiagnosticSeverity(sd.get("severity", "unknown")),
                relationship_to_primary=sd.get("relationship_to_primary")
            ))

        # Parse recommendations
        recommendations = []
        for rec in data.get("recommended_actions", []):
            recommendations.append(DiagnosticRecommendation(
                recommendation=rec.get("recommendation", ""),
                rationale=rec.get("rationale", ""),
                priority=rec.get("priority", 5),
                safety_level=SafetyLevel(rec.get("safety_level", "professional")),
                requires_professional=rec.get("requires_professional", True),
                supporting_evidence=rec.get("supporting_evidence", []),
                estimated_cost_inr=rec.get("estimated_cost_inr")
            ))

        # Determine overall severity
        overall_severity = DiagnosticSeverity.UNKNOWN
        if primary:
            overall_severity = primary.severity
        for s in secondary:
            severity_order = {
                DiagnosticSeverity.CRITICAL: 4,
                DiagnosticSeverity.MAJOR: 3,
                DiagnosticSeverity.MINOR: 2,
                DiagnosticSeverity.INFO: 1,
                DiagnosticSeverity.UNKNOWN: 0
            }
            if severity_order.get(s.severity, 0) > severity_order.get(overall_severity, 0):
                overall_severity = s.severity

        # Build result
        result = DiagnosticResult(
            diagnosis_id=diagnosis_id,
            vehicle_id=context.vehicle_profile.get("vin"),
            session_id=None,  # Will be set by caller
            data_source=context.data_source,
            diagnostic_status=DiagnosticStatus(data.get("diagnostic_status", "complete")),
            severity=overall_severity,
            confidence=data.get("confidence", 0.0),
            summary=data.get("summary", ""),
            detected_symptoms=data.get("detected_symptoms", []),
            confirmed_faults=data.get("confirmed_faults", []),
            primary_diagnosis=primary,
            secondary_diagnoses=secondary,
            supporting_evidence=data.get("supporting_evidence", []),
            contradictory_evidence=data.get("contradictory_evidence", []),
            recommended_checks=data.get("recommended_checks", []),
            recommended_actions=recommendations,
            safety_warnings=data.get("safety_warnings", []),
            missing_information=data.get("missing_information", []),
            data_quality=data_quality,
            dtc_references=data.get("dtc_references", []),
            rule_engine_findings=data.get("rule_engine_findings", []),
            rag_sources=data.get("rag_sources", []),
            model_information={
                "model": self.ai_service.model if self.ai_service else "unknown",
                "temperature": 0.1,
                "max_tokens": 4096
            },
            raw_ai_response=raw_response
        )

        # Add simulation disclaimer if needed
        if context.data_source == DataSource.SIMULATION:
            if result.summary and "SIMULATION" not in result.summary:
                result.summary = "[SIMULATION DATA — NOT ACTUAL VEHICLE DATA] " + result.summary
            result.safety_warnings.insert(0, "SIMULATION DATA — NOT ACTUAL VEHICLE DATA")

        return result

    def _reconcile_findings(self, result: DiagnosticResult, context: DiagnosticContext) -> DiagnosticResult:
        """Reconcile AI findings with actual observations."""
        # Check if AI claimed DTCs that weren't actually scanned
        ai_dtc_codes = set()
        if result.primary_diagnosis:
            ai_dtc_codes.add(result.primary_diagnosis.code)
        for s in result.secondary_diagnoses:
            ai_dtc_codes.add(s.code)

        scanned_codes = set(d.get("code", "") for d in context.dtcs)

        # If AI mentions DTCs not in scan, flag as unverified
        unverified = ai_dtc_codes - scanned_codes
        if unverified:
            result.contradictory_evidence.append(
                f"AI referenced DTCs not found in scan: {', '.join(unverified)}"
            )
            # Reduce confidence
            result.confidence = max(0.0, result.confidence - 0.2)

        # Check sensor readings against AI claims
        # (This could be expanded with specific logic)

        return result

    def _save_diagnosis(self, result: DiagnosticResult, session_id: Optional[str] = None):
        """Save diagnosis to database."""
        if not self.database_service:
            return

        try:
            # Serialize result to JSON
            diagnosis_json = result.model_dump_json()

            # Get active session if not provided
            if session_id is None:
                active = self.database_service.get_active_session()
                if active:
                    session_id = str(active["id"])

            # Use raw SQL to insert into ai_diagnostic_sessions table
            # (We'll add the table creation in database service)
            import sqlite3
            with sqlite3.connect(self.database_service.db_path) as conn:
                cursor = conn.cursor()
                # Ensure table exists
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ai_diagnostic_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT UNIQUE,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        vehicle_context TEXT,
                        dtcs TEXT,
                        ai_diagnosis TEXT,
                        rule_matches TEXT,
                        user_feedback TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                vehicle_context_json = json.dumps({
                    k: v for k, v in context.vehicle_profile.items()
                })

                dtcs_json = json.dumps(context.dtcs)
                rule_matches_json = json.dumps(result.rule_engine_findings)

                cursor.execute("""
                    INSERT INTO ai_diagnostic_sessions
                    (session_id, vehicle_context, dtcs, ai_diagnosis, rule_matches)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    result.diagnosis_id,
                    vehicle_context_json,
                    dtcs_json,
                    diagnosis_json,
                    rule_matches_json
                ))
                conn.commit()
                logger.info(f"Diagnosis saved to database: {result.diagnosis_id}")

        except Exception as e:
            logger.error(f"Failed to save diagnosis: {e}")

    def _create_insufficient_data_result(
        self,
        diagnosis_id: str,
        context: DiagnosticContext,
        message: str
    ) -> DiagnosticResult:
        """Create result for insufficient data."""
        return DiagnosticResult(
            diagnosis_id=diagnosis_id,
            data_source=context.data_source,
            diagnostic_status=DiagnosticStatus.INSUFFICIENT_DATA,
            severity=DiagnosticSeverity.INFO,
            confidence=0.0,
            summary=f"Insufficient data for diagnosis: {message}",
            missing_information=[message],
            data_quality=DataQuality.NONE,
            model_information={"model": self.ai_service.model if self.ai_service else "unknown"}
        )

    def _create_error_result(
        self,
        diagnosis_id: str,
        context: DiagnosticContext,
        message: str
    ) -> DiagnosticResult:
        """Create result for AI error."""
        return DiagnosticResult(
            diagnosis_id=diagnosis_id,
            data_source=context.data_source if hasattr(context, 'data_source') else DataSource.SIMULATION,
            diagnostic_status=DiagnosticStatus.ERROR,
            severity=DiagnosticSeverity.INFO,
            confidence=0.0,
            summary=f"Diagnostic error: {message}",
            safety_warnings=[f"Diagnostic engine error: {message}"],
            data_quality=DataQuality.NONE,
            model_information={"model": self.ai_service.model if self.ai_service else "unknown"}
        )

    def get_diagnosis_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve diagnostic history from database."""
        if not self.database_service:
            return []

        try:
            import sqlite3
            with sqlite3.connect(self.database_service.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM ai_diagnostic_sessions
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
                results = []
                for row in cursor.fetchall():
                    item = dict(row)
                    # Parse JSON fields
                    if item.get("vehicle_context"):
                        item["vehicle_context"] = json.loads(item["vehicle_context"])
                    if item.get("dtcs"):
                        item["dtcs"] = json.loads(item["dtcs"])
                    if item.get("ai_diagnosis"):
                        item["ai_diagnosis"] = json.loads(item["ai_diagnosis"])
                    if item.get("rule_matches"):
                        item["rule_matches"] = json.loads(item["rule_matches"])
                    results.append(item)
                return results
        except Exception as e:
            logger.error(f"Failed to get diagnosis history: {e}")
            return []


# =============================================================================
# SINGLETON ACCESS
# =============================================================================

_diagnostic_engine_instance: Optional[DiagnosticEngine] = None


def get_diagnostic_engine() -> DiagnosticEngine:
    """Get the diagnostic engine singleton."""
    global _diagnostic_engine_instance
    if _diagnostic_engine_instance is None:
        from services import get_obd_service, get_database, get_ai_service
        _diagnostic_engine_instance = DiagnosticEngine(
            obd_service=get_obd_service(),
            database_service=get_database(),
            ai_service=get_ai_service(),
            knowledge_base=KnowledgeBase(),
            rule_engine=get_rule_engine() if RULE_ENGINE_AVAILABLE else None
        )
    return _diagnostic_engine_instance
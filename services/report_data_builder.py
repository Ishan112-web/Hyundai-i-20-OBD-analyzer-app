"""
i20 AI Garage - Report Data Builder

Assembles report data from existing application services and database.
Reuses existing database accessors and service methods.
Handles missing data gracefully and tracks data provenance.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from services.database import DatabaseService, get_database
from services.diagnostic_engine import get_diagnostic_engine, DiagnosticEngine
from services.rule_engine import get_rule_engine, RuleEngine
from services.obd_service import get_obd_service, OBDService
from services.types import SensorReading, DTC
from services.diagnostic_models import DiagnosticResult, DataSource as DiagDataSource
from services.rule_models import RuleFinding, RuleSeverity, DataSource as RuleDataSource
from services.report_models import (
    ReportType,
    ReportFormat,
    DataSource,
    DiagnosticSeverity,
    RuleSeverity as ReportRuleSeverity,
    MaintenanceStatus,
    ReportMetadata,
    ReportVehicleInfo,
    DataProvenance,
    DTCReportItem,
    AIDiagnosisReportItem,
    RuleFindingReportItem,
    TelemetrySummary,
    DiagnosticReportData,
    VehicleHealthReportData,
    ComponentStatus,
    PerformanceSessionSummary,
    SensorStatistics,
    PerformanceReportData,
    MaintenanceRecordReportItem,
    MaintenanceSummary,
    MaintenanceReportData,
)


class ReportDataBuilder:
    """
    Builds report data by assembling information from existing services.

    Does NOT trigger new diagnoses, scans, or evaluations.
    Only uses already-persisted data and current application state.
    """

    def __init__(
        self,
        database: Optional[Union[DatabaseService, str]] = None,
        db_path: Optional[str] = None,
        diagnostic_engine: Optional[DiagnosticEngine] = None,
        rule_engine: Optional[RuleEngine] = None,
        obd_service: Optional[OBDService] = None,
    ):
        # Accept DatabaseService object, or string path as 'database' or 'db_path'
        # Store the path string before converting to DatabaseService
        path_str = None
        if isinstance(database, str):
            # String path passed as 'database' parameter
            path_str = database
            from services.database import DatabaseService
            database = DatabaseService(database)
        elif database is None and db_path is not None:
            # String path passed as 'db_path' parameter
            path_str = db_path
            from services.database import DatabaseService
            database = DatabaseService(db_path)

        self.db = database or get_database()
        self._db_path = path_str or (self.db.db_path if hasattr(self.db, 'db_path') else None)
        self.diagnostic_engine = diagnostic_engine or get_diagnostic_engine()
        self.rule_engine = rule_engine or get_rule_engine()
        self.obd_service = obd_service or get_obd_service()

    @property
    def db_path(self) -> Optional[str]:
        """Get database path."""
        return self._db_path

    def _determine_data_source(self, is_simulated: bool = True) -> DataSource:
        """Determine data source from simulation status."""
        if is_simulated:
            return DataSource.SIMULATION
        return DataSource.REAL

    def _get_vehicle_info(self) -> ReportVehicleInfo:
        """Get vehicle info from database."""
        profile = self.db.get_vehicle_profile()
        if profile:
            return ReportVehicleInfo.from_vehicle_profile(profile)
        return ReportVehicleInfo()

    def _get_current_data_source(self) -> DataSource:
        """Get current data source from OBD service."""
        status = self.obd_service.get_status()
        mode = status.get("mode", "simulation")
        return DataSource.REAL if mode == "real" else DataSource.SIMULATION

    # =========================================================================
    # DIAGNOSTIC REPORT
    # =========================================================================

    def build_diagnostic_report_data(
        self,
        diagnosis_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> DiagnosticReportData:
        """
        Build comprehensive diagnostic report data.

        Args:
            diagnosis_id: Specific AI diagnosis ID (uses latest if None)
            session_id: Specific telemetry session ID (uses active if None)
        """
        metadata = ReportMetadata(
            report_type=ReportType.DIAGNOSTIC,
            data_source=self._get_current_data_source(),
        )
        vehicle_info = self._get_vehicle_info()

        # Get diagnostic session info
        diagnostic_session = self._build_diagnostic_session_info(diagnosis_id, session_id)

        # Get DTCs
        dtcs = self._build_dtc_items()

        # Get AI diagnosis
        ai_diagnosis = self._build_ai_diagnosis(diagnosis_id)

        # Get rule findings
        rule_findings = self._build_rule_findings()

        # Get telemetry summary
        telemetry_summary = self._build_telemetry_summary(session_id)

        # Build recommendations
        recommendations = self._build_recommendations(dtcs, ai_diagnosis, rule_findings)

        # Build limitations
        limitations = self._build_limitations(dtcs, ai_diagnosis, rule_findings, telemetry_summary)

        # Build provenance
        provenance = self._build_provenance(
            diagnosis_id=diagnosis_id,
            session_id=session_id,
            has_dtcs=bool(dtcs),
            has_ai=ai_diagnosis is not None,
            has_rules=bool(rule_findings),
            has_telemetry=telemetry_summary is not None,
        )

        return DiagnosticReportData(
            metadata=metadata,
            vehicle_info=vehicle_info,
            diagnostic_session=diagnostic_session,
            dtcs=dtcs,
            ai_diagnosis=ai_diagnosis,
            rule_findings=rule_findings,
            telemetry_summary=telemetry_summary,
            recommendations=recommendations,
            limitations=limitations,
            data_provenance=provenance,
        )

    def _build_diagnostic_session_info(
        self,
        diagnosis_id: Optional[str],
        session_id: Optional[str],
    ) -> Dict[str, Any]:
        """Build diagnostic session information."""
        info = {
            "session_id": session_id,
            "diagnosis_id": diagnosis_id,
            "data_source": self._get_current_data_source().value,
            "operating_mode": self.obd_service.get_status().get("mode", "simulation"),
            "available_sensor_count": 0,
            "available_dtc_count": 0,
        }

        # Get current sensor count
        readings = self.obd_service.get_all_readings()
        info["available_sensor_count"] = len(readings) if readings else 0

        # Get DTC count
        dtcs = self.obd_service.scan_dtcs()
        info["available_dtc_count"] = len(dtcs) if dtcs else 0

        # If specific diagnosis requested, get its details
        if diagnosis_id:
            diag_session = self.db.get_ai_diagnostic_session(diagnosis_id)
            if diag_session:
                info["diagnosis_timestamp"] = diag_session.get("timestamp")
                info["diagnosis_data_source"] = diag_session.get("vehicle_context", {}).get("diagnostic_mode", "unknown")

        # If specific session requested, get its details
        if session_id:
            try:
                session = self.db.get_session_records(int(session_id))
                if session:
                    info["telemetry_record_count"] = len(session)
            except (ValueError, TypeError):
                pass

        return info

    def _build_dtc_items(self) -> List[DTCReportItem]:
        """Build DTC report items from current scan."""
        dtcs = self.obd_service.scan_dtcs()
        if not dtcs:
            return []

        items = []
        for dtc in dtcs:
            severity_map = {
                "critical": DiagnosticSeverity.CRITICAL,
                "major": DiagnosticSeverity.MAJOR,
                "minor": DiagnosticSeverity.MINOR,
                "info": DiagnosticSeverity.INFO,
            }

            items.append(DTCReportItem(
                code=dtc.code,
                description=dtc.description,
                severity=severity_map.get(dtc.severity, DiagnosticSeverity.UNKNOWN),
                status=dtc.status,
                possible_causes=dtc.possible_causes if hasattr(dtc, 'possible_causes') else [],
                recommended_verification=dtc.recommended_verification if hasattr(dtc, 'recommended_verification') else [],
                is_demo=getattr(dtc, 'is_demo', True),
                data_source=self._determine_data_source(getattr(dtc, 'is_demo', True)),
            ))
        return items

    def _build_ai_diagnosis(self, diagnosis_id: Optional[str] = None) -> Optional[AIDiagnosisReportItem]:
        """Build AI diagnosis report item from stored diagnosis."""
        # If specific ID requested, get that one
        if diagnosis_id:
            session = self.db.get_ai_diagnostic_session(diagnosis_id)
            if session and session.get("ai_diagnosis"):
                return self._parse_ai_diagnosis(session["ai_diagnosis"], session.get("diagnosis_id"))
            return None

        # Otherwise get latest
        sessions = self.db.get_ai_diagnostic_sessions(limit=1)
        if not sessions or not sessions[0].get("ai_diagnosis"):
            return None

        return self._parse_ai_diagnosis(sessions[0]["ai_diagnosis"], sessions[0].get("diagnosis_id"))

    def _parse_ai_diagnosis(self, ai_diag: Dict[str, Any], diagnosis_id: str) -> AIDiagnosisReportItem:
        """Parse stored AI diagnosis into report item."""
        # Determine data source from vehicle context
        vehicle_context = ai_diag.get("vehicle_profile", {})
        is_sim = vehicle_context.get("diagnostic_mode", "").lower() == "simulation"
        data_source = DataSource.SIMULATION if is_sim else DataSource.REAL

        # Extract estimated cost
        estimated_cost = None
        for action in ai_diag.get("recommended_actions", []):
            if action.get("estimated_cost_inr"):
                estimated_cost = action["estimated_cost_inr"]
                break

        return AIDiagnosisReportItem(
            diagnosis_id=diagnosis_id,
            timestamp=datetime.fromisoformat(ai_diag.get("timestamp", datetime.now().isoformat())),
            primary_diagnosis=ai_diag.get("primary_diagnosis"),
            secondary_diagnoses=ai_diag.get("secondary_diagnoses", []),
            confidence=ai_diag.get("confidence", 0.0),
            severity=DiagnosticSeverity(ai_diag.get("severity", "unknown")),
            summary=ai_diag.get("summary", ""),
            supporting_evidence=ai_diag.get("supporting_evidence", []),
            contradictory_evidence=ai_diag.get("contradictory_evidence", []),
            recommended_checks=ai_diag.get("recommended_checks", []),
            recommended_actions=ai_diag.get("recommended_actions", []),
            safety_warnings=ai_diag.get("safety_warnings", []),
            missing_information=ai_diag.get("missing_information", []),
            data_quality=ai_diag.get("data_quality", "unknown"),
            estimated_cost_inr=estimated_cost,
            data_source=data_source,
        )

    def _build_rule_findings(self) -> List[RuleFindingReportItem]:
        """Build rule findings from latest rule evaluation."""
        # Get latest evaluation from rule engine
        last_eval = self.rule_engine.get_last_evaluation()
        if not last_eval or not last_eval.findings:
            return []

        items = []
        for finding in last_eval.findings:
            # Map rule severity to report severity
            severity_map = {
                RuleSeverity.INFORMATIONAL: ReportRuleSeverity.INFORMATIONAL,
                RuleSeverity.LOW: ReportRuleSeverity.LOW,
                RuleSeverity.MEDIUM: ReportRuleSeverity.MEDIUM,
                RuleSeverity.HIGH: ReportRuleSeverity.HIGH,
                RuleSeverity.CRITICAL: ReportRuleSeverity.CRITICAL,
            }

            items.append(RuleFindingReportItem(
                finding_id=finding.finding_id,
                rule_id=finding.rule_id,
                rule_name=finding.rule_name,
                category=finding.rule_type.value,
                rule_type=finding.rule_type.value,
                severity=severity_map.get(finding.severity, ReportRuleSeverity.MEDIUM),
                confidence=finding.confidence,
                explanation=finding.explanation,
                observed_values=finding.observed_values,
                expected_values=finding.expected_values,
                evidence=finding.evidence,
                recommended_checks=finding.recommended_checks,
                recommended_actions=finding.recommended_actions,
                safety_notes=finding.safety_notes,
                data_source=finding.data_source.value,
                dtc_hints=finding.dtc_hints,
            ))
        return items

    def _build_telemetry_summary(self, session_id: Optional[str] = None) -> Optional[TelemetrySummary]:
        """Build telemetry summary from active session or specified session."""
        # Determine which session to use
        target_session_id = None
        if session_id:
            try:
                target_session_id = int(session_id)
            except (ValueError, TypeError):
                pass

        if target_session_id is None:
            active = self.db.get_active_session()
            if active:
                target_session_id = active["id"]

        if target_session_id is None:
            return None

        records = self.db.get_session_records(target_session_id)
        if not records:
            return None

        # Get latest record
        latest = records[-1] if records else {}

        # Determine data source
        is_sim = latest.get("is_simulated", True)
        data_source = DataSource.SIMULATION if is_sim else DataSource.REAL

        return TelemetrySummary(
            rpm=latest.get("rpm"),
            speed_kmh=latest.get("speed_kmh"),
            coolant_temp_c=latest.get("coolant_temp_c"),
            throttle_pos_pct=latest.get("throttle_pos_pct"),
            engine_load_pct=latest.get("engine_load_pct"),
            stft_b1_pct=latest.get("stft_b1_pct"),
            ltft_b1_pct=latest.get("ltft_b1_pct"),
            voltage_v=latest.get("voltage_v"),
            maf_g_s=latest.get("maf_g_s"),
            map_kpa=latest.get("map_kpa"),
            data_source=data_source,
            record_count=len(records),
            timestamp=datetime.fromisoformat(latest["timestamp"]) if latest.get("timestamp") else None,
        )

    def _build_recommendations(
        self,
        dtcs: List[DTCReportItem],
        ai_diagnosis: Optional[AIDiagnosisReportItem],
        rule_findings: List[RuleFindingReportItem],
    ) -> Dict[str, List[str]]:
        """Build categorized recommendations."""
        immediate = []
        verification = []
        routine = []
        monitoring = []

        # From DTCs
        for dtc in dtcs:
            if dtc.severity in [DiagnosticSeverity.CRITICAL, DiagnosticSeverity.MAJOR]:
                immediate.append(f"Address {dtc.code}: {dtc.description}")
            for v in dtc.recommended_verification:
                verification.append(f"[{dtc.code}] {v}")

        # From AI diagnosis
        if ai_diagnosis:
            for check in ai_diagnosis.recommended_checks:
                verification.append(f"[AI] {check}")
            for action in ai_diagnosis.recommended_actions:
                priority = action.get("priority", 5)
                if priority <= 3:
                    immediate.append(f"[AI] {action.get('recommendation', '')}")
                elif priority <= 6:
                    routine.append(f"[AI] {action.get('recommendation', '')}")
                else:
                    monitoring.append(f"[AI] {action.get('recommendation', '')}")
            for warning in ai_diagnosis.safety_warnings:
                immediate.append(f"[SAFETY] {warning}")

        # From rule findings
        for finding in rule_findings:
            if finding.severity in [ReportRuleSeverity.CRITICAL, ReportRuleSeverity.HIGH]:
                immediate.append(f"[{finding.rule_id}] {finding.explanation}")
            for check in finding.recommended_checks:
                verification.append(f"[{finding.rule_id}] {check}")
            for action in finding.recommended_actions:
                routine.append(f"[{finding.rule_id}] {action}")

        return {
            "immediate_attention": immediate,
            "further_verification": verification,
            "routine_maintenance": routine,
            "monitoring": monitoring,
        }

    def _build_limitations(
        self,
        dtcs: List[DTCReportItem],
        ai_diagnosis: Optional[AIDiagnosisReportItem],
        rule_findings: List[RuleFindingReportItem],
        telemetry_summary: Optional[TelemetrySummary],
    ) -> List[str]:
        """Build report limitations list."""
        limitations = []

        if not dtcs:
            limitations.append("No DTC records available for this report.")
        if not ai_diagnosis:
            limitations.append("AI diagnosis not available.")
        if not rule_findings:
            limitations.append("No deterministic rule findings recorded.")
        if not telemetry_summary:
            limitations.append("No saved telemetry session selected or available.")

        # Data source limitations
        data_sources = set()
        for dtc in dtcs:
            data_sources.add(dtc.data_source.value)
        if ai_diagnosis:
            data_sources.add(ai_diagnosis.data_source.value)
        for finding in rule_findings:
            data_sources.add(finding.data_source)
        if telemetry_summary:
            data_sources.add(telemetry_summary.data_source.value)

        if "simulation" in data_sources:
            limitations.append("This report contains SIMULATION DATA — NOT ACTUAL VEHICLE DATA.")
        if "mixed" in data_sources:
            limitations.append("This report combines real and simulated data sources.")

        limitations.append("AI outputs are advisory and require professional verification.")
        limitations.append("Rule thresholds require appropriate vehicle-specific validation.")

        return limitations

    def _build_provenance(
        self,
        diagnosis_id: Optional[str],
        session_id: Optional[str],
        has_dtcs: bool,
        has_ai: bool,
        has_rules: bool,
        has_telemetry: bool,
    ) -> List[DataProvenance]:
        """Build data provenance records."""
        provenance = []
        current_source = self._get_current_data_source()

        if has_dtcs:
            provenance.append(DataProvenance(
                source=current_source,
                description="Live OBD-II DTC scan" if current_source == DataSource.REAL else "Simulated DTC data",
                record_count=1,
            ))

        if has_ai and diagnosis_id:
            provenance.append(DataProvenance(
                source=current_source,
                description="AI diagnostic session",
                diagnosis_id=diagnosis_id,
                record_count=1,
            ))

        if has_rules:
            last_eval = self.rule_engine.get_last_evaluation()
            provenance.append(DataProvenance(
                source=current_source,
                description="Deterministic rule engine evaluation",
                evaluation_id=last_eval.evaluation_id if last_eval else None,
                record_count=len(last_eval.findings) if last_eval else 0,
            ))

        if has_telemetry and session_id:
            provenance.append(DataProvenance(
                source=current_source,
                description="Telemetry session data",
                session_id=session_id,
                record_count=1,
            ))

        return provenance

    # =========================================================================
    # VEHICLE HEALTH REPORT
    # =========================================================================

    def build_vehicle_health_report_data(self) -> VehicleHealthReportData:
        """Build vehicle health report data."""
        metadata = ReportMetadata(
            report_type=ReportType.VEHICLE_HEALTH,
            data_source=self._get_current_data_source(),
        )
        vehicle_info = self._get_vehicle_info()

        # Get latest diagnostic summary
        latest_diagnostic = self._get_latest_diagnostic_summary()

        # Get current DTCs
        current_dtcs = self._build_dtc_items()

        # Get latest rule findings
        rule_findings = self._build_rule_findings()

        # Get latest AI diagnosis
        ai_diagnosis = self._build_ai_diagnosis()

        # Get sensor availability
        sensor_availability = self._get_sensor_availability()

        # Get telemetry summary
        telemetry_summary = self._build_telemetry_summary()

        # Get maintenance data
        maintenance_history = self._get_maintenance_history()
        upcoming = self._get_upcoming_maintenance()
        overdue = self._get_overdue_maintenance()

        # Build component statuses
        component_statuses = self._build_component_statuses(
            current_dtcs, rule_findings, ai_diagnosis, sensor_availability
        )

        # Build overall conclusion
        overall_conclusion = self._build_overall_conclusion(
            current_dtcs, rule_findings, ai_diagnosis, component_statuses
        )

        # Build safety observations
        safety_observations = self._build_safety_observations(
            current_dtcs, rule_findings, ai_diagnosis
        )

        # Build provenance
        provenance = self._build_provenance(
            diagnosis_id=None,
            session_id=None,
            has_dtcs=bool(current_dtcs),
            has_ai=ai_diagnosis is not None,
            has_rules=bool(rule_findings),
            has_telemetry=telemetry_summary is not None,
        )

        return VehicleHealthReportData(
            metadata=metadata,
            vehicle_info=vehicle_info,
            overall_conclusion=overall_conclusion,
            latest_diagnostic_summary=latest_diagnostic,
            current_dtc_summary=current_dtcs,
            latest_rule_findings=rule_findings,
            latest_ai_diagnosis=ai_diagnosis,
            sensor_availability=sensor_availability,
            telemetry_summary=telemetry_summary,
            maintenance_history=maintenance_history,
            upcoming_maintenance=upcoming,
            overdue_maintenance=overdue,
            safety_observations=safety_observations,
            component_statuses=component_statuses,
            data_provenance=provenance,
        )

    def _get_latest_diagnostic_summary(self) -> Optional[Dict[str, Any]]:
        """Get latest diagnostic report summary."""
        reports = self.db.get_diagnostic_reports(limit=1)
        if not reports:
            return None

        report = reports[0]
        return {
            "scan_time": report.get("scan_time"),
            "dtc_count": report.get("dtc_count", 0),
            "summary": report.get("summary", ""),
            "is_demo": report.get("is_demo", True),
        }

    def _get_sensor_availability(self) -> Dict[str, bool]:
        """Get availability of key sensors."""
        readings = self.obd_service.get_all_readings()
        key_sensors = [
            "rpm", "speed_kmh", "coolant_temp_c", "throttle_pos_pct",
            "engine_load_pct", "stft_b1_pct", "ltft_b1_pct", "voltage_v",
            "maf_g_s", "map_kpa", "intake_pressure_kpa",
        ]

        available = set(readings.keys()) if readings else set()
        return {sensor: sensor in available for sensor in key_sensors}

    def _get_maintenance_history(self) -> List[Dict[str, Any]]:
        """Get maintenance history for report."""
        records = self.db.get_maintenance_records(limit=50)
        return records

    def _get_upcoming_maintenance(self) -> List[Dict[str, Any]]:
        """Get upcoming maintenance items."""
        # Get current odometer from latest telemetry or vehicle profile
        current_odometer = self._get_current_odometer()
        if current_odometer is None:
            return []

        return self.db.get_upcoming_maintenance(current_odometer)

    def _get_overdue_maintenance(self) -> List[Dict[str, Any]]:
        """Get overdue maintenance items."""
        records = self.db.get_maintenance_records(limit=100)
        overdue = []
        current_odometer = self._get_current_odometer()

        for record in records:
            next_km = record.get("next_service_km")
            next_date = record.get("next_service_date")

            is_overdue = False
            if next_km and current_odometer and current_odometer >= next_km:
                is_overdue = True
            elif next_date:
                try:
                    next_dt = datetime.fromisoformat(next_date)
                    if datetime.now() >= next_dt:
                        is_overdue = True
                except ValueError:
                    pass

            if is_overdue:
                overdue.append(record)

        return overdue

    def _get_current_odometer(self) -> Optional[int]:
        """Get current odometer from latest telemetry or profile."""
        # Try from active session records
        active = self.db.get_active_session()
        if active:
            records = self.db.get_session_records(active["id"])
            if records:
                # Odometer not directly stored, estimate from distance
                # For now, return None as we don't have odometer in telemetry
                pass

        # Try from vehicle profile
        profile = self.db.get_vehicle_profile()
        if profile and profile.get("odometer_km"):
            return profile["odometer_km"]

        # Try from latest maintenance record
        records = self.db.get_maintenance_records(limit=1)
        if records and records[0].get("odometer_km"):
            return records[0]["odometer_km"]

        return None

    def _build_component_statuses(
        self,
        dtcs: List[DTCReportItem],
        rule_findings: List[RuleFindingReportItem],
        ai_diagnosis: Optional[AIDiagnosisReportItem],
        sensor_availability: Dict[str, bool],
    ) -> List[ComponentStatus]:
        """Build component-level statuses."""
        statuses = []
        current_source = self._get_current_data_source()

        # Engine
        engine_status = "normal"
        engine_evidence = []
        if any(d.severity in [DiagnosticSeverity.CRITICAL, DiagnosticSeverity.MAJOR] for d in dtcs):
            engine_status = "critical_finding"
            engine_evidence.append("Active critical/major DTCs")
        elif any(f.severity in [ReportRuleSeverity.CRITICAL, ReportRuleSeverity.HIGH] for f in rule_findings if "engine" in f.rule_id.lower() or "ignition" in f.rule_id.lower() or "fuel" in f.rule_id.lower()):
            engine_status = "attention_recommended"
            engine_evidence.append("Rule engine findings")
        elif ai_diagnosis and ai_diagnosis.severity in [DiagnosticSeverity.CRITICAL, DiagnosticSeverity.MAJOR]:
            engine_status = "attention_recommended"
            engine_evidence.append("AI diagnosis indicates issue")

        statuses.append(ComponentStatus(
            name="Engine & Powertrain",
            status=engine_status,
            description="Engine mechanical, ignition, fuel systems",
            evidence=engine_evidence,
            data_source=current_source,
        ))

        # Cooling
        cooling_status = "normal"
        cooling_evidence = []
        if any("cool" in d.code.lower() or "thermostat" in d.description.lower() for d in dtcs):
            cooling_status = "critical_finding"
            cooling_evidence.append("Cooling-related DTC")
        elif any(f.severity in [ReportRuleSeverity.CRITICAL, ReportRuleSeverity.HIGH] for f in rule_findings if "cool" in f.rule_id.lower()):
            cooling_status = "attention_recommended"
            cooling_evidence.append("Rule engine cooling findings")

        statuses.append(ComponentStatus(
            name="Cooling System",
            status=cooling_status,
            description="Thermostat, water pump, radiator, coolant",
            evidence=cooling_evidence,
            data_source=current_source,
        ))

        # Electrical
        electrical_status = "normal"
        electrical_evidence = []
        if any("voltage" in f.rule_id.lower() or "battery" in f.rule_id.lower() or "electrical" in f.rule_id.lower() for f in rule_findings if f.severity in [ReportRuleSeverity.CRITICAL, ReportRuleSeverity.HIGH]):
            electrical_status = "attention_recommended"
            electrical_evidence.append("Rule engine electrical findings")

        statuses.append(ComponentStatus(
            name="Electrical System",
            status=electrical_status,
            description="Battery, alternator, charging system",
            evidence=electrical_evidence,
            data_source=current_source,
        ))

        # Emissions
        emissions_status = "normal"
        emissions_evidence = []
        if any("p0420" in d.code.lower() or "catalyst" in d.description.lower() or "evap" in d.description.lower() for d in dtcs):
            emissions_status = "attention_recommended"
            emissions_evidence.append("Emissions-related DTC")
        elif any(f.severity in [ReportRuleSeverity.HIGH] for f in rule_findings if "emission" in f.rule_id.lower() or "fuel_trim" in f.rule_id.lower()):
            emissions_status = "attention_recommended"
            emissions_evidence.append("Rule engine emissions findings")

        statuses.append(ComponentStatus(
            name="Emissions & Exhaust",
            status=emissions_status,
            description="Catalytic converter, EVAP, O2 sensors",
            evidence=emissions_evidence,
            data_source=current_source,
        ))

        # Transmission
        transmission_status = "normal"
        transmission_evidence = []
        if any("trans" in f.rule_id.lower() for f in rule_findings if f.severity in [ReportRuleSeverity.CRITICAL, ReportRuleSeverity.HIGH]):
            transmission_status = "attention_recommended"
            transmission_evidence.append("Rule engine transmission findings")

        statuses.append(ComponentStatus(
            name="Transmission",
            status=transmission_status,
            description="Manual transmission, clutch",
            evidence=transmission_evidence,
            data_source=current_source,
        ))

        # Sensors
        available_count = sum(1 for v in sensor_availability.values() if v)
        total_count = len(sensor_availability)
        if available_count < total_count * 0.5:
            sensor_status = "insufficient_data"
        elif available_count < total_count:
            sensor_status = "attention_recommended"
        else:
            sensor_status = "normal"

        statuses.append(ComponentStatus(
            name="Sensor Availability",
            status=sensor_status,
            description=f"{available_count}/{total_count} key sensors available",
            evidence=[f"Available: {available_count}/{total_count}"],
            data_source=current_source,
        ))

        return statuses

    def _build_overall_conclusion(
        self,
        dtcs: List[DTCReportItem],
        rule_findings: List[RuleFindingReportItem],
        ai_diagnosis: Optional[AIDiagnosisReportItem],
        component_statuses: List[ComponentStatus],
    ) -> str:
        """Build overall conclusion text."""
        critical_count = sum(1 for c in component_statuses if c.status == "critical_finding")
        attention_count = sum(1 for c in component_statuses if c.status == "attention_recommended")
        insufficient_count = sum(1 for c in component_statuses if c.status == "insufficient_data")

        if critical_count > 0:
            return f"CRITICAL: {critical_count} component(s) with critical findings. Immediate professional attention required."
        elif attention_count > 0:
            return f"ATTENTION RECOMMENDED: {attention_count} component(s) require attention. Schedule service soon."
        elif insufficient_count > 0:
            return f"INSUFFICIENT DATA: {insufficient_count} component(s) could not be fully evaluated. More data needed."
        else:
            return "NORMAL: No critical issues detected based on available data. Continue routine maintenance."

    def _build_safety_observations(
        self,
        dtcs: List[DTCReportItem],
        rule_findings: List[RuleFindingReportItem],
        ai_diagnosis: Optional[AIDiagnosisReportItem],
    ) -> List[str]:
        """Build safety observations."""
        observations = []

        # From DTCs
        for dtc in dtcs:
            if dtc.severity == DiagnosticSeverity.CRITICAL:
                observations.append(f"SAFETY: {dtc.code} - {dtc.description} (Critical severity)")

        # From rule findings
        for finding in rule_findings:
            if finding.severity == ReportRuleSeverity.CRITICAL:
                observations.append(f"SAFETY: {finding.rule_name} - {finding.explanation}")
            for note in finding.safety_notes:
                observations.append(f"SAFETY: {note}")

        # From AI diagnosis
        if ai_diagnosis:
            for warning in ai_diagnosis.safety_warnings:
                observations.append(f"SAFETY (AI): {warning}")

        return observations

    # =========================================================================
    # PERFORMANCE REPORT
    # =========================================================================

    def build_performance_report_data(
        self,
        session_id: Optional[int] = None,
    ) -> PerformanceReportData:
        """Build performance report data from a telemetry session."""
        metadata = ReportMetadata(
            report_type=ReportType.PERFORMANCE,
            data_source=self._get_current_data_source(),
        )
        vehicle_info = self._get_vehicle_info()

        # Determine session
        if session_id is None:
            active = self.db.get_active_session()
            if active:
                session_id = active["id"]

        if session_id is None:
            # Get latest session
            sessions = self.db.get_telemetry_sessions(limit=1)
            if sessions:
                session_id = sessions[0]["id"]

        if session_id is None:
            # No session available
            session_summary = PerformanceSessionSummary(
                session_id=0,
                session_name="No Session",
                scenario="unknown",
                start_time=datetime.now(),
                data_source=self._get_current_data_source(),
            )
            return PerformanceReportData(
                metadata=metadata,
                vehicle_info=vehicle_info,
                session=session_summary,
                data_provenance=[DataProvenance(
                    source=DataSource.UNKNOWN,
                    description="No telemetry session available",
                )],
            )

        # Get session details
        session_data = self._get_session_details(session_id)
        records = self.db.get_session_records(session_id)

        # Build session summary
        session_summary = PerformanceSessionSummary(
            session_id=session_data.get("id", session_id),
            session_name=session_data.get("session_name", f"Session {session_id}"),
            scenario=session_data.get("scenario", "unknown"),
            start_time=datetime.fromisoformat(session_data["start_time"]) if session_data.get("start_time") else datetime.now(),
            end_time=datetime.fromisoformat(session_data["end_time"]) if session_data.get("end_time") else None,
            duration_seconds=session_data.get("duration_seconds"),
            record_count=len(records),
            peak_rpm=session_data.get("peak_rpm"),
            max_speed_kmh=session_data.get("max_speed"),
            avg_speed_kmh=session_data.get("avg_speed"),
            max_coolant_temp_c=session_data.get("max_coolant_temp"),
            max_engine_load_pct=session_data.get("max_engine_load"),
            total_distance_km=session_data.get("total_distance_km"),
            fuel_consumed_l=session_data.get("fuel_consumed_l"),
            data_source=DataSource.SIMULATION if records and records[0].get("is_simulated", True) else DataSource.REAL,
        )

        # Build sensor statistics
        sensor_stats = self._build_sensor_statistics(records)

        # Build charts data
        charts_data = self._build_charts_data(records)

        # Build provenance
        provenance = [DataProvenance(
            source=session_summary.data_source,
            description=f"Telemetry session: {session_summary.session_name}",
            session_id=str(session_id),
            record_count=len(records),
            date_range={
                "start": records[0]["timestamp"] if records else None,
                "end": records[-1]["timestamp"] if records else None,
            } if records else None,
        )]

        return PerformanceReportData(
            metadata=metadata,
            vehicle_info=vehicle_info,
            session=session_summary,
            sensor_statistics=sensor_stats,
            charts_data=charts_data,
            data_provenance=provenance,
        )

    def _get_session_details(self, session_id: int) -> Dict[str, Any]:
        """Get session details from database."""
        sessions = self.db.get_telemetry_sessions(limit=100)
        for session in sessions:
            if session["id"] == session_id:
                return session
        return {}

    def _build_sensor_statistics(self, records: List[Dict]) -> List[SensorStatistics]:
        """Build statistical summary for each sensor."""
        if not records:
            return []

        sensor_configs = [
            ("rpm", "RPM"),
            ("speed_kmh", "km/h"),
            ("coolant_temp_c", "°C"),
            ("throttle_pos_pct", "%"),
            ("engine_load_pct", "%"),
            ("stft_b1_pct", "%"),
            ("ltft_b1_pct", "%"),
            ("voltage_v", "V"),
            ("maf_g_s", "g/s"),
            ("map_kpa", "kPa"),
        ]

        stats = []
        for sensor_key, unit in sensor_configs:
            values = [r.get(sensor_key) for r in records if r.get(sensor_key) is not None]
            if not values:
                continue

            import statistics
            stats.append(SensorStatistics(
                sensor_name=sensor_key,
                unit=unit,
                count=len(values),
                min_value=min(values),
                max_value=max(values),
                avg_value=sum(values) / len(values),
                std_dev=statistics.stdev(values) if len(values) > 1 else 0.0,
            ))

        return stats

    def _build_charts_data(self, records: List[Dict]) -> Dict[str, List[Dict]]:
        """Build data for chart rendering."""
        if not records:
            return {}

        # Prepare time-series data for each sensor
        chart_sensors = [
            "rpm", "speed_kmh", "coolant_temp_c",
            "throttle_pos_pct", "engine_load_pct",
            "stft_b1_pct", "ltft_b1_pct", "voltage_v",
        ]

        charts_data = {}
        for sensor in chart_sensors:
            data_points = []
            for r in records:
                if r.get(sensor) is not None and r.get("timestamp"):
                    data_points.append({
                        "timestamp": r["timestamp"],
                        "value": r[sensor],
                    })
            if data_points:
                charts_data[sensor] = data_points

        return charts_data

    # =========================================================================
    # MAINTENANCE REPORT
    # =========================================================================

    def build_maintenance_report_data(self) -> MaintenanceReportData:
        """Build maintenance report data."""
        metadata = ReportMetadata(
            report_type=ReportType.MAINTENANCE,
            data_source=DataSource.REAL,  # Maintenance records are always real
        )
        vehicle_info = self._get_vehicle_info()

        # Get current odometer
        odometer_km = self._get_current_odometer()

        # Get all maintenance records
        records = self.db.get_maintenance_records(limit=200)

        # Build history items
        history = []
        for r in records:
            history.append(MaintenanceRecordReportItem(
                record_id=r["id"],
                service_type=r["service_type"],
                description=r.get("description", ""),
                service_date=r["service_date"],
                odometer_km=r["odometer_km"],
                cost=r.get("cost"),
                notes=r.get("notes"),
                next_service_km=r.get("next_service_km"),
                next_service_date=r.get("next_service_date"),
                provider=r.get("provider"),
            ))

        # Categorize upcoming and overdue
        upcoming = []
        overdue = []
        current_odometer = odometer_km or 0

        for item in history:
            next_km = item.next_service_km
            next_date = item.next_service_date

            is_due = False
            if next_km and current_odometer and current_odometer >= next_km:
                is_due = True
            elif next_date:
                try:
                    next_dt = datetime.fromisoformat(next_date)
                    if datetime.now() >= next_dt:
                        is_due = True
                except ValueError:
                    pass

            if is_due:
                overdue.append(item)
            elif next_km or next_date:
                upcoming.append(item)

        # Build summary
        total_cost = sum(r.get("cost", 0) for r in records if r.get("cost"))
        cost_by_category = {}
        for r in records:
            if r.get("cost"):
                cat = r["service_type"]
                cost_by_category[cat] = cost_by_category.get(cat, 0) + r["cost"]

        last_record = records[0] if records else None

        summary = MaintenanceSummary(
            total_records=len(records),
            total_cost_inr=total_cost,
            cost_by_category=cost_by_category,
            overdue_count=len(overdue),
            upcoming_count=len(upcoming),
            last_service_date=last_record["service_date"] if last_record else None,
            last_service_odometer=last_record["odometer_km"] if last_record else None,
        )

        # Build provenance
        provenance = [DataProvenance(
            source=DataSource.REAL,
            description="Maintenance records from database",
            record_count=len(records),
        )]

        return MaintenanceReportData(
            metadata=metadata,
            vehicle_info=vehicle_info,
            odometer_km=odometer_km,
            maintenance_history=history,
            upcoming_items=upcoming,
            overdue_items=overdue,
            summary=summary,
            data_provenance=provenance,
        )

    # =============================================================================
    # PUBLIC API METHODS (matching expected interface)
    # =============================================================================

    def build_diagnostic_report(
        self,
        metadata: Optional[ReportMetadata] = None,
        vehicle_info: Optional[ReportVehicleInfo] = None,
        session_id: Optional[str] = None,
        diagnosis_id: Optional[str] = None,
    ) -> DiagnosticReportData:
        """Build diagnostic report with optional metadata and vehicle info override."""
        # Use provided metadata or create default
        if metadata is None:
            metadata = ReportMetadata(
                report_type=ReportType.DIAGNOSTIC,
                data_source=self._get_current_data_source(),
            )
        if vehicle_info is None:
            vehicle_info = self._get_vehicle_info()

        # Build the report data using internal method
        report_data = self.build_diagnostic_report_data(diagnosis_id, session_id)

        # Override metadata and vehicle_info if provided
        return DiagnosticReportData(
            metadata=metadata,
            vehicle_info=vehicle_info,
            diagnostic_session=report_data.diagnostic_session,
            dtcs=report_data.dtcs,
            ai_diagnosis=report_data.ai_diagnosis,
            rule_findings=report_data.rule_findings,
            telemetry_summary=report_data.telemetry_summary,
            recommendations=report_data.recommendations,
            limitations=report_data.limitations,
            data_provenance=report_data.data_provenance,
        )

    def build_vehicle_health_report(
        self,
        metadata: Optional[ReportMetadata] = None,
        vehicle_info: Optional[ReportVehicleInfo] = None,
    ) -> VehicleHealthReportData:
        """Build vehicle health report with optional metadata and vehicle info override."""
        if metadata is None:
            metadata = ReportMetadata(
                report_type=ReportType.VEHICLE_HEALTH,
                data_source=self._get_current_data_source(),
            )
        if vehicle_info is None:
            vehicle_info = self._get_vehicle_info()

        report_data = self.build_vehicle_health_report_data()

        return VehicleHealthReportData(
            metadata=metadata,
            vehicle_info=vehicle_info,
            overall_conclusion=report_data.overall_conclusion,
            latest_diagnostic_summary=report_data.latest_diagnostic_summary,
            current_dtc_summary=report_data.current_dtc_summary,
            latest_rule_findings=report_data.latest_rule_findings,
            latest_ai_diagnosis=report_data.latest_ai_diagnosis,
            sensor_availability=report_data.sensor_availability,
            telemetry_summary=report_data.telemetry_summary,
            component_statuses=report_data.component_statuses,
            maintenance_history=report_data.maintenance_history,
            upcoming_maintenance=report_data.upcoming_maintenance,
            overdue_maintenance=report_data.overdue_maintenance,
            safety_observations=report_data.safety_observations,
            data_provenance=report_data.data_provenance,
        )

    def build_performance_report(
        self,
        metadata: Optional[ReportMetadata] = None,
        vehicle_info: Optional[ReportVehicleInfo] = None,
        session_id: Optional[int] = None,
    ) -> PerformanceReportData:
        """Build performance report with optional metadata and vehicle info override."""
        if metadata is None:
            metadata = ReportMetadata(
                report_type=ReportType.PERFORMANCE,
                data_source=self._get_current_data_source(),
            )
        if vehicle_info is None:
            vehicle_info = self._get_vehicle_info()

        report_data = self.build_performance_report_data(session_id)

        return PerformanceReportData(
            metadata=metadata,
            vehicle_info=vehicle_info,
            session=report_data.session,
            sensor_statistics=report_data.sensor_statistics,
            charts_data=report_data.charts_data,
            data_provenance=report_data.data_provenance,
        )

    def build_maintenance_report(
        self,
        metadata: Optional[ReportMetadata] = None,
        vehicle_info: Optional[ReportVehicleInfo] = None,
    ) -> MaintenanceReportData:
        """Build maintenance report with optional metadata and vehicle info override."""
        if metadata is None:
            metadata = ReportMetadata(
                report_type=ReportType.MAINTENANCE,
                data_source=DataSource.REAL,
            )
        if vehicle_info is None:
            vehicle_info = self._get_vehicle_info()

        report_data = self.build_maintenance_report_data()

        return MaintenanceReportData(
            metadata=metadata,
            vehicle_info=vehicle_info,
            odometer_km=report_data.odometer_km,
            summary=report_data.summary,
            maintenance_history=report_data.maintenance_history,
            upcoming_items=report_data.upcoming_items,
            overdue_items=report_data.overdue_items,
            data_provenance=report_data.data_provenance,
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def build_diagnostic_report(
    diagnosis_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> DiagnosticReportData:
    """Convenience function to build diagnostic report data."""
    builder = ReportDataBuilder()
    return builder.build_diagnostic_report(diagnosis_id, session_id)


def build_vehicle_health_report() -> VehicleHealthReportData:
    """Convenience function to build vehicle health report data."""
    builder = ReportDataBuilder()
    return builder.build_vehicle_health_report()


def build_performance_report(session_id: Optional[int] = None) -> PerformanceReportData:
    """Convenience function to build performance report data."""
    builder = ReportDataBuilder()
    return builder.build_performance_report(session_id)


def build_maintenance_report() -> MaintenanceReportData:
    """Convenience function to build maintenance report data."""
    builder = ReportDataBuilder()
    return builder.build_maintenance_report()


def build_diagnostic_report_data(
    diagnosis_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> DiagnosticReportData:
    """Convenience function to build diagnostic report data."""
    builder = ReportDataBuilder()
    return builder.build_diagnostic_report_data(diagnosis_id, session_id)


def build_vehicle_health_report_data() -> VehicleHealthReportData:
    """Convenience function to build vehicle health report data."""
    builder = ReportDataBuilder()
    return builder.build_vehicle_health_report_data()


def build_performance_report_data(session_id: Optional[int] = None) -> PerformanceReportData:
    """Convenience function to build performance report data."""
    builder = ReportDataBuilder()
    return builder.build_performance_report_data(session_id)


def build_maintenance_report_data() -> MaintenanceReportData:
    """Convenience function to build maintenance report data."""
    builder = ReportDataBuilder()
    return builder.build_maintenance_report_data()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "ReportDataBuilder",
    "build_diagnostic_report",
    "build_vehicle_health_report",
    "build_performance_report",
    "build_maintenance_report",
    "build_diagnostic_report_data",
    "build_vehicle_health_report_data",
    "build_performance_report_data",
    "build_maintenance_report_data",
]
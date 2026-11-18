"""
Tests for report models (Pydantic models for all report types).
"""

import pytest
from datetime import datetime
from uuid import uuid4

from services.report_models import (
    ReportType,
    ReportFormat,
    DataSource,
    DiagnosticSeverity,
    RuleSeverity,
    MaintenanceStatus,
    ReportStatus,
    ReportMetadata,
    ReportVehicleInfo,
    DataProvenance,
    DTCReportItem,
    AIDiagnosisReportItem,
    RuleFindingReportItem,
    TelemetrySummary,
    DiagnosticReportData,
    ComponentStatus,
    VehicleHealthReportData,
    PerformanceSessionSummary,
    SensorStatistics,
    PerformanceReportData,
    MaintenanceRecordReportItem,
    MaintenanceSummary,
    MaintenanceReportData,
    GeneratedReport,
    ReportGenerationResult,
    ReportDataUnion,
)


class TestReportEnums:
    """Test enum values."""

    def test_report_type_values(self):
        assert ReportType.DIAGNOSTIC.value == "diagnostic"
        assert ReportType.VEHICLE_HEALTH.value == "vehicle_health"
        assert ReportType.PERFORMANCE.value == "performance"
        assert ReportType.MAINTENANCE.value == "maintenance"

    def test_report_format_values(self):
        assert ReportFormat.HTML.value == "html"
        assert ReportFormat.PDF.value == "pdf"

    def test_report_status_values(self):
        assert ReportStatus.PENDING.value == "pending"
        assert ReportStatus.GENERATING.value == "generating"
        assert ReportStatus.COMPLETED.value == "completed"
        assert ReportStatus.FAILED.value == "failed"

    def test_data_source_values(self):
        assert DataSource.REAL.value == "real"
        assert DataSource.SIMULATION.value == "simulation"
        assert DataSource.MIXED.value == "mixed"
        assert DataSource.UNKNOWN.value == "unknown"

    def test_diagnostic_severity_values(self):
        assert DiagnosticSeverity.CRITICAL.value == "critical"
        assert DiagnosticSeverity.MAJOR.value == "major"
        assert DiagnosticSeverity.MINOR.value == "minor"
        assert DiagnosticSeverity.INFO.value == "info"
        assert DiagnosticSeverity.UNKNOWN.value == "unknown"

    def test_rule_severity_values(self):
        assert RuleSeverity.INFORMATIONAL.value == "informational"
        assert RuleSeverity.LOW.value == "low"
        assert RuleSeverity.MEDIUM.value == "medium"
        assert RuleSeverity.HIGH.value == "high"
        assert RuleSeverity.CRITICAL.value == "critical"

    def test_maintenance_status_values(self):
        assert MaintenanceStatus.OVERDUE.value == "overdue"
        assert MaintenanceStatus.UPCOMING.value == "upcoming"
        assert MaintenanceStatus.COMPLETED.value == "completed"
        assert MaintenanceStatus.DUE_SOON.value == "due_soon"


class TestReportMetadata:
    """Test ReportMetadata model."""

    def test_valid_metadata(self):
        metadata = ReportMetadata(
            report_id="TEST123",
            report_type=ReportType.DIAGNOSTIC,
            generated_at=datetime.now(),
            format=ReportFormat.HTML,
            data_source=DataSource.SIMULATION,
        )
        assert metadata.report_id == "TEST123"
        assert metadata.report_type == ReportType.DIAGNOSTIC
        assert metadata.format == ReportFormat.HTML
        assert metadata.data_source == DataSource.SIMULATION
        assert metadata.version == "1.0"
        assert metadata.generated_by == "i20 AI Garage"

    def test_metadata_defaults(self):
        metadata = ReportMetadata(
            report_id="TEST123",
            report_type=ReportType.DIAGNOSTIC,
            generated_at=datetime.now(),
            format=ReportFormat.HTML,
            data_source=DataSource.SIMULATION,
        )
        assert metadata.version == "1.0"
        assert metadata.notes is None


class TestReportVehicleInfo:
    """Test ReportVehicleInfo model."""

    def test_valid_vehicle_info(self):
        vehicle = ReportVehicleInfo(
            make="Hyundai",
            model="i20 Asta",
            year=2023,
            engine="1.2L Naturally Aspirated Petrol",
            transmission="Manual",
            fuel_type="Petrol",
            market="India",
            ecu_tuning="Stock",
            diagnostic_mode="Simulation",
        )
        assert vehicle.make == "Hyundai"
        assert vehicle.model == "i20 Asta"
        assert vehicle.year == 2023
        assert vehicle.vin is None
        assert vehicle.odometer_km is None

    def test_vehicle_info_with_optional(self):
        vehicle = ReportVehicleInfo(
            make="Hyundai",
            model="i20 Asta",
            year=2023,
            engine="1.2L Naturally Aspirated Petrol",
            transmission="Manual",
            fuel_type="Petrol",
            market="India",
            ecu_tuning="Stock",
            diagnostic_mode="Simulation",
            vin="MALBM51BLKM123456",
            odometer_km=15000,
        )
        assert vehicle.vin == "MALBM51BLKM123456"
        assert vehicle.odometer_km == 15000

    def test_from_vehicle_profile(self):
        profile = {
            "make": "Hyundai",
            "model": "i20",
            "year": 2022,
            "engine": "1.0L Turbo",
            "transmission": "Automatic",
            "fuel_type": "Petrol",
            "market": "Europe",
            "ecu_tuning": "Stage 1",
            "diagnostic_mode": "Real",
            "vin": "TESTVIN123",
            "odometer_km": 20000,
        }
        vehicle = ReportVehicleInfo.from_vehicle_profile(profile)
        assert vehicle.make == "Hyundai"
        assert vehicle.model == "i20"
        assert vehicle.year == 2022
        assert vehicle.vin == "TESTVIN123"
        assert vehicle.odometer_km == 20000


class TestDataProvenance:
    """Test DataProvenance model."""

    def test_valid_data_provenance(self):
        prov = DataProvenance(
            source=DataSource.REAL,
            description="OBD-II telemetry data",
            session_id="sess_123",
            diagnosis_id="diag_456",
            evaluation_id="eval_789",
            record_count=150,
            date_range={"start": "2024-01-01", "end": "2024-01-15"},
        )
        assert prov.description == "OBD-II telemetry data"
        assert prov.source == DataSource.REAL
        assert prov.session_id == "sess_123"
        assert prov.record_count == 150
        assert prov.date_range == {"start": "2024-01-01", "end": "2024-01-15"}

    def test_defaults(self):
        prov = DataProvenance(
            source=DataSource.SIMULATION,
            description="Test data",
        )
        assert prov.record_count == 0
        assert prov.session_id is None
        assert prov.diagnosis_id is None
        assert prov.evaluation_id is None
        assert prov.date_range is None


class TestDTCReportItem:
    """Test DTCReportItem model."""

    def test_valid_dtc(self):
        dtc = DTCReportItem(
            code="P0300",
            description="Random/Multiple Cylinder Misfire Detected",
            severity=DiagnosticSeverity.MAJOR,
            status="active",
            possible_causes=["Faulty spark plug", "Ignition coil"],
            recommended_verification=["Check spark plugs", "Test ignition coils"],
            is_demo=True,
            data_source=DataSource.SIMULATION,
        )
        assert dtc.code == "P0300"
        assert dtc.severity == DiagnosticSeverity.MAJOR
        assert dtc.status == "active"
        assert dtc.is_demo is True
        assert dtc.data_source == DataSource.SIMULATION
        assert len(dtc.possible_causes) == 2

    def test_defaults(self):
        dtc = DTCReportItem(
            code="P0171",
            description="System Too Lean",
        )
        assert dtc.severity == DiagnosticSeverity.UNKNOWN
        assert dtc.status == "active"
        assert dtc.possible_causes == []
        assert dtc.recommended_verification == []
        assert dtc.is_demo is True
        assert dtc.data_source == DataSource.SIMULATION


class TestAIDiagnosisReportItem:
    """Test AIDiagnosisReportItem model."""

    def test_valid_ai_diagnosis(self):
        diagnosis = AIDiagnosisReportItem(
            diagnosis_id="diag_123",
            timestamp=datetime.now(),
            primary_diagnosis={"code": "P0300", "description": "Misfire"},
            secondary_diagnoses=[{"code": "P0301", "description": "Cylinder 1 Misfire"}],
            confidence=0.88,
            severity=DiagnosticSeverity.MAJOR,
            summary="Engine misfire detected",
            supporting_evidence=["RPM fluctuation", "DTC P0300 present"],
            contradictory_evidence=[],
            recommended_checks=["Check spark plugs", "Test compression"],
            recommended_actions=[{"action": "Replace spark plugs", "priority": "high"}],
            safety_warnings=["Do not drive at high speeds"],
            missing_information=["No freeze frame data"],
            data_quality="good",
            estimated_cost_inr="₹5,000 - ₹15,000",
            data_source=DataSource.SIMULATION,
        )
        assert diagnosis.diagnosis_id == "diag_123"
        assert diagnosis.confidence == 0.88
        assert diagnosis.severity == DiagnosticSeverity.MAJOR
        assert diagnosis.data_quality == "good"
        assert len(diagnosis.safety_warnings) == 1

    def test_confidence_clamping(self):
        # Test that confidence is clamped to 0-1 range
        diagnosis = AIDiagnosisReportItem(
            diagnosis_id="diag_123",
            timestamp=datetime.now(),
            confidence=1.5,  # Should be clamped to 1.0
        )
        assert diagnosis.confidence == 1.0

        diagnosis2 = AIDiagnosisReportItem(
            diagnosis_id="diag_124",
            timestamp=datetime.now(),
            confidence=-0.1,  # Should be clamped to 0.0
        )
        assert diagnosis2.confidence == 0.0

    def test_confidence_rounding(self):
        diagnosis = AIDiagnosisReportItem(
            diagnosis_id="diag_123",
            timestamp=datetime.now(),
            confidence=0.887654,  # Should be rounded to 2 decimal places
        )
        assert diagnosis.confidence == 0.89


class TestRuleFindingReportItem:
    """Test RuleFindingReportItem model."""

    def test_valid_rule_finding(self):
        finding = RuleFindingReportItem(
            finding_id="finding_001",
            rule_id="RULE_001",
            rule_name="High Coolant Temperature",
            category="cooling",
            rule_type="threshold",
            severity=RuleSeverity.CRITICAL,
            confidence=0.95,
            explanation="Coolant temp reached 115°C",
            observed_values={"coolant_temp": 115.0},
            expected_values={"coolant_temp": 110.0},
            evidence=["ECT=115°C", "Threshold=110°C"],
            recommended_checks=["Check coolant level", "Inspect radiator"],
            recommended_actions=["Stop vehicle immediately", "Allow engine to cool"],
            safety_notes=["Risk of engine damage"],
            data_source=DataSource.SIMULATION,
            dtc_hints=["P0217"],
        )
        assert finding.rule_id == "RULE_001"
        assert finding.severity == RuleSeverity.CRITICAL
        assert finding.confidence == 0.95
        assert len(finding.evidence) == 2
        assert finding.dtc_hints == ["P0217"]

    def test_confidence_clamping(self):
        finding = RuleFindingReportItem(
            finding_id="finding_001",
            rule_id="RULE_001",
            rule_name="Test Rule",
            category="test",
            rule_type="threshold",
            severity=RuleSeverity.LOW,
            confidence=1.5,  # Should be clamped to 1.0
            explanation="Test",
        )
        assert finding.confidence == 1.0


class TestTelemetrySummary:
    """Test TelemetrySummary model."""

    def test_valid_telemetry_summary(self):
        summary = TelemetrySummary(
            rpm=850.5,
            speed_kmh=45.2,
            coolant_temp_c=92.3,
            throttle_pos_pct=18.5,
            engine_load_pct=35.0,
            stft_b1_pct=2.5,
            ltft_b1_pct=-1.2,
            voltage_v=13.8,
            maf_g_s=4.2,
            map_kpa=45.0,
            data_source=DataSource.SIMULATION,
            record_count=100,
            timestamp=datetime.now(),
        )
        assert summary.rpm == 850.5
        assert summary.coolant_temp_c == 92.3
        assert summary.record_count == 100
        assert summary.data_source == DataSource.SIMULATION

    def test_defaults(self):
        summary = TelemetrySummary()
        assert summary.rpm is None
        assert summary.speed_kmh is None
        assert summary.data_source == DataSource.UNKNOWN
        assert summary.record_count == 0
        assert summary.timestamp is None


class TestDiagnosticReportData:
    """Test DiagnosticReportData model."""

    def test_valid_diagnostic_report(self):
        metadata = ReportMetadata(
            report_id="RPT123",
            report_type=ReportType.DIAGNOSTIC,
            generated_at=datetime.now(),
            format=ReportFormat.HTML,
            data_source=DataSource.SIMULATION,
        )
        vehicle = ReportVehicleInfo(
            make="Hyundai",
            model="i20 Asta",
            year=2023,
            engine="1.2L Naturally Aspirated Petrol",
            transmission="Manual",
            fuel_type="Petrol",
            market="India",
            ecu_tuning="Stock",
            diagnostic_mode="Simulation",
        )
        report = DiagnosticReportData(
            metadata=metadata,
            vehicle_info=vehicle,
            diagnostic_session={"session_id": "sess_123"},
            dtcs=[],
            ai_diagnosis=None,
            rule_findings=[],
            telemetry_summary=None,
            recommendations={
                "immediate_attention": [],
                "further_verification": [],
                "routine_maintenance": [],
                "monitoring": []
            },
            limitations=["Simulation data only"],
            data_provenance=[],
        )
        assert report.metadata.report_type == ReportType.DIAGNOSTIC
        assert report.limitations == ["Simulation data only"]
        assert "immediate_attention" in report.recommendations

    def test_default_recommendations(self):
        metadata = ReportMetadata(
            report_id="RPT123",
            report_type=ReportType.DIAGNOSTIC,
            generated_at=datetime.now(),
            format=ReportFormat.HTML,
            data_source=DataSource.SIMULATION,
        )
        vehicle = ReportVehicleInfo(
            make="Hyundai",
            model="i20 Asta",
            year=2023,
            engine="1.2L Naturally Aspirated Petrol",
            transmission="Manual",
            fuel_type="Petrol",
            market="India",
            ecu_tuning="Stock",
            diagnostic_mode="Simulation",
        )
        report = DiagnosticReportData(
            metadata=metadata,
            vehicle_info=vehicle,
        )
        assert "immediate_attention" in report.recommendations
        assert "further_verification" in report.recommendations
        assert "routine_maintenance" in report.recommendations
        assert "monitoring" in report.recommendations


class TestComponentStatus:
    """Test ComponentStatus model."""

    def test_valid_component_status(self):
        comp = ComponentStatus(
            name="Engine",
            status="normal",
            description="Engine running normally",
            evidence=["No DTCs", "Normal temperatures"],
            last_evaluated=datetime.now(),
            data_source=DataSource.SIMULATION,
        )
        assert comp.name == "Engine"
        assert comp.status == "normal"
        assert len(comp.evidence) == 2
        assert comp.data_source == DataSource.SIMULATION

    def test_status_literal_values(self):
        valid_statuses = ["normal", "attention_recommended", "critical_finding", "insufficient_data", "not_evaluated"]
        for status in valid_statuses:
            comp = ComponentStatus(
                name="Test",
                status=status,
                description="Test",
            )
            assert comp.status == status


class TestVehicleHealthReportData:
    """Test VehicleHealthReportData model."""

    def test_valid_vehicle_health_report(self):
        metadata = ReportMetadata(
            report_id="RPT456",
            report_type=ReportType.VEHICLE_HEALTH,
            generated_at=datetime.now(),
            format=ReportFormat.HTML,
            data_source=DataSource.MIXED,
        )
        vehicle = ReportVehicleInfo(
            make="Hyundai",
            model="i20 Asta",
            year=2023,
            engine="1.2L Naturally Aspirated Petrol",
            transmission="Manual",
            fuel_type="Petrol",
            market="India",
            ecu_tuning="Stock",
            diagnostic_mode="Simulation",
        )
        report = VehicleHealthReportData(
            metadata=metadata,
            vehicle_info=vehicle,
            overall_conclusion="Vehicle in good condition",
            latest_diagnostic_summary={"dtc_count": 0},
            current_dtc_summary=[],
            latest_rule_findings=[],
            latest_ai_diagnosis=None,
            sensor_availability={"RPM": True, "SPEED": True},
            telemetry_summary=None,
            maintenance_history=[],
            upcoming_maintenance=[],
            overdue_maintenance=[],
            safety_observations=[],
            component_statuses=[
                ComponentStatus(name="Engine", status="normal", description="OK", evidence=[])
            ],
            data_provenance=[],
        )
        assert report.metadata.report_type == ReportType.VEHICLE_HEALTH
        assert report.overall_conclusion == "Vehicle in good condition"
        assert report.component_statuses[0].name == "Engine"


class TestPerformanceSessionSummary:
    """Test PerformanceSessionSummary model."""

    def test_valid_session_summary(self):
        session = PerformanceSessionSummary(
            session_id=123,
            session_name="Test Drive",
            scenario="city",
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration_seconds=1800,
            record_count=1800,
            peak_rpm=6500.0,
            max_speed_kmh=120.0,
            avg_speed_kmh=45.0,
            max_coolant_temp_c=95.0,
            max_engine_load_pct=95.0,
            total_distance_km=25.5,
            fuel_consumed_l=2.3,
            data_source=DataSource.SIMULATION,
        )
        assert session.session_id == 123
        assert session.session_name == "Test Drive"
        assert session.scenario == "city"
        assert session.duration_seconds == 1800
        assert session.data_source == DataSource.SIMULATION


class TestSensorStatistics:
    """Test SensorStatistics model."""

    def test_valid_sensor_statistics(self):
        stat = SensorStatistics(
            sensor_name="RPM",
            unit="RPM",
            count=100,
            min_value=700.0,
            max_value=3500.0,
            avg_value=1800.0,
            std_dev=500.0,
        )
        assert stat.sensor_name == "RPM"
        assert stat.count == 100
        assert stat.min_value == 700.0
        assert stat.std_dev == 500.0


class TestPerformanceReportData:
    """Test PerformanceReportData model."""

    def test_valid_performance_report(self):
        metadata = ReportMetadata(
            report_id="RPT789",
            report_type=ReportType.PERFORMANCE,
            generated_at=datetime.now(),
            format=ReportFormat.HTML,
            data_source=DataSource.SIMULATION,
        )
        vehicle = ReportVehicleInfo(
            make="Hyundai",
            model="i20 Asta",
            year=2023,
            engine="1.2L Naturally Aspirated Petrol",
            transmission="Manual",
            fuel_type="Petrol",
            market="India",
            ecu_tuning="Stock",
            diagnostic_mode="Simulation",
        )
        session = PerformanceSessionSummary(
            session_id=123,
            session_name="Test Drive",
            scenario="city",
            start_time=datetime.now(),
            record_count=100,
            data_source=DataSource.SIMULATION,
        )
        report = PerformanceReportData(
            metadata=metadata,
            vehicle_info=vehicle,
            session=session,
            sensor_statistics=[],
            charts_data={},
            data_provenance=[],
        )
        assert report.metadata.report_type == ReportType.PERFORMANCE
        assert report.session.session_id == 123


class TestMaintenanceRecordReportItem:
    """Test MaintenanceRecordReportItem model."""

    def test_valid_maintenance_record(self):
        record = MaintenanceRecordReportItem(
            record_id=1,
            service_type="Oil Change",
            description="Engine oil and filter change",
            service_date="2024-01-15",
            odometer_km=10000,
            cost=2500.0,
            next_service_km=20000,
            next_service_date="2024-07-15",
            provider="Dealer",
            notes="Used synthetic oil",
        )
        assert record.service_type == "Oil Change"
        assert record.odometer_km == 10000
        assert record.cost == 2500.0
        assert record.next_service_km == 20000


class TestMaintenanceSummary:
    """Test MaintenanceSummary model."""

    def test_valid_maintenance_summary(self):
        summary = MaintenanceSummary(
            total_records=5,
            total_cost_inr=12500.0,
            upcoming_count=2,
            overdue_count=1,
            last_service_date="2024-01-15",
            last_service_odometer=10000,
            cost_by_category={"Oil Change": 5000.0, "Brake Service": 7500.0},
        )
        assert summary.total_records == 5
        assert summary.total_cost_inr == 12500.0
        assert summary.upcoming_count == 2
        assert summary.overdue_count == 1
        assert summary.cost_by_category["Oil Change"] == 5000.0


class TestMaintenanceReportData:
    """Test MaintenanceReportData model."""

    def test_valid_maintenance_report(self):
        metadata = ReportMetadata(
            report_id="RPT999",
            report_type=ReportType.MAINTENANCE,
            generated_at=datetime.now(),
            format=ReportFormat.HTML,
            data_source=DataSource.REAL,
        )
        vehicle = ReportVehicleInfo(
            make="Hyundai",
            model="i20 Asta",
            year=2023,
            engine="1.2L Naturally Aspirated Petrol",
            transmission="Manual",
            fuel_type="Petrol",
            market="India",
            ecu_tuning="Stock",
            diagnostic_mode="Simulation",
        )
        summary = MaintenanceSummary(
            total_records=5,
            total_cost_inr=12500.0,
            upcoming_count=2,
            overdue_count=1,
            cost_by_category={"Oil Change": 5000.0},
        )
        report = MaintenanceReportData(
            metadata=metadata,
            vehicle_info=vehicle,
            odometer_km=15000,
            maintenance_history=[],
            upcoming_items=[],
            overdue_items=[],
            summary=summary,
            data_provenance=[],
        )
        assert report.metadata.report_type == ReportType.MAINTENANCE
        assert report.odometer_km == 15000
        assert report.summary.total_records == 5


class TestGeneratedReport:
    """Test GeneratedReport model."""

    def test_valid_generated_report(self):
        metadata = ReportMetadata(
            report_id="RPT123",
            report_type=ReportType.DIAGNOSTIC,
            generated_at=datetime.now(),
            format=ReportFormat.HTML,
            data_source=DataSource.SIMULATION,
        )
        report = GeneratedReport(
            report_id="GEN123",
            report_type=ReportType.DIAGNOSTIC,
            format=ReportFormat.HTML,
            file_path="/tmp/report.html",
            file_name="diagnostic_report.html",
            file_size_bytes=1024,
            generated_at=datetime.now(),
            metadata=metadata,
        )
        assert report.report_id == "GEN123"
        assert report.format == ReportFormat.HTML
        assert report.file_size_bytes == 1024


class TestReportGenerationResult:
    """Test ReportGenerationResult model."""

    def test_success_result(self):
        metadata = ReportMetadata(
            report_id="RPT123",
            report_type=ReportType.DIAGNOSTIC,
            generated_at=datetime.now(),
            format=ReportFormat.HTML,
            data_source=DataSource.SIMULATION,
        )
        generated = GeneratedReport(
            report_id="GEN123",
            report_type=ReportType.DIAGNOSTIC,
            format=ReportFormat.HTML,
            file_path="/tmp/report.html",
            file_name="diagnostic_report.html",
            file_size_bytes=1024,
            generated_at=datetime.now(),
            metadata=metadata,
        )
        result = ReportGenerationResult(
            success=True,
            report=generated,
            generation_duration_ms=1500.0,
        )
        assert result.success is True
        assert result.report == generated
        assert result.generation_duration_ms == 1500.0
        assert result.error_message is None

    def test_failure_result(self):
        result = ReportGenerationResult(
            success=False,
            error_message="Template not found",
        )
        assert result.success is False
        assert result.report is None
        assert result.error_message == "Template not found"


class TestReportDataUnion:
    """Test ReportDataUnion type."""

    def test_union_accepts_all_types(self):
        metadata = ReportMetadata(
            report_id="TEST",
            report_type=ReportType.DIAGNOSTIC,
            generated_at=datetime.now(),
            format=ReportFormat.HTML,
            data_source=DataSource.SIMULATION,
        )
        vehicle = ReportVehicleInfo(
            make="Hyundai",
            model="i20 Asta",
            year=2023,
            engine="1.2L Naturally Aspirated Petrol",
            transmission="Manual",
            fuel_type="Petrol",
            market="India",
            ecu_tuning="Stock",
            diagnostic_mode="Simulation",
        )

        # Diagnostic
        diag = DiagnosticReportData(
            metadata=metadata,
            vehicle_info=vehicle,
            dtcs=[],
            ai_diagnosis=None,
            rule_findings=[],
            telemetry_summary=None,
            recommendations={},
            limitations=[],
            data_provenance=[],
        )
        assert isinstance(diag, ReportDataUnion)

        # Vehicle Health
        metadata.report_type = ReportType.VEHICLE_HEALTH
        health = VehicleHealthReportData(
            metadata=metadata,
            vehicle_info=vehicle,
            overall_conclusion="OK",
            latest_diagnostic_summary={},
            current_dtc_summary=[],
            latest_rule_findings=[],
            latest_ai_diagnosis=None,
            sensor_availability={},
            telemetry_summary=None,
            maintenance_history=[],
            upcoming_maintenance=[],
            overdue_maintenance=[],
            safety_observations=[],
            component_statuses=[],
            data_provenance=[],
        )
        assert isinstance(health, ReportDataUnion)

        # Performance
        metadata.report_type = ReportType.PERFORMANCE
        session = PerformanceSessionSummary(
            session_id=1,
            session_name="Test",
            scenario="city",
            start_time=datetime.now(),
            record_count=100,
            data_source=DataSource.SIMULATION,
        )
        perf = PerformanceReportData(
            metadata=metadata,
            vehicle_info=vehicle,
            session=session,
            sensor_statistics=[],
            charts_data={},
            data_provenance=[],
        )
        assert isinstance(perf, ReportDataUnion)

        # Maintenance
        metadata.report_type = ReportType.MAINTENANCE
        summary = MaintenanceSummary(
            total_records=0,
            total_cost_inr=0.0,
            upcoming_count=0,
            overdue_count=0,
            cost_by_category={},
        )
        maint = MaintenanceReportData(
            metadata=metadata,
            vehicle_info=vehicle,
            odometer_km=0,
            maintenance_history=[],
            upcoming_items=[],
            overdue_items=[],
            summary=summary,
            data_provenance=[],
        )
        assert isinstance(maint, ReportDataUnion)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
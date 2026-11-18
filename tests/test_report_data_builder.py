"""
Tests for report data builder.
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import os

from services.report_data_builder import ReportDataBuilder
from services.report_models import (
    ReportType,
    ReportFormat,
    DataSource,
    ReportMetadata,
    ReportVehicleInfo,
    DataProvenance,
)


class TestReportDataBuilder:
    """Test ReportDataBuilder class."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.fixture
    def builder(self, temp_db):
        """Create a ReportDataBuilder instance with temp database."""
        return ReportDataBuilder(database=temp_db)

    @pytest.fixture
    def metadata(self):
        """Create test metadata."""
        return ReportMetadata(
            report_id="TEST123",
            report_type=ReportType.DIAGNOSTIC,
            generated_at=datetime.now(),
            format=ReportFormat.HTML,
            data_source=DataSource.SIMULATION,
        )

    @pytest.fixture
    def vehicle_info(self):
        """Create test vehicle info."""
        return ReportVehicleInfo(
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

    def test_builder_initialization(self, builder):
        """Test builder initializes correctly."""
        assert builder.db_path is not None
        assert builder.diagnostic_engine is not None
        assert builder.rule_engine is not None
        assert builder.obd_service is not None
        assert builder.db is not None

    def test_get_vehicle_info(self, builder):
        """Test getting vehicle info from database."""
        vehicle = builder._get_vehicle_info()
        assert vehicle.make == "Hyundai"
        assert vehicle.model == "i20 Asta"
        assert vehicle.year == 2023
        assert vehicle.engine == "1.2L Naturally Aspirated Petrol"

    def test_build_diagnostic_report(self, builder, metadata, vehicle_info):
        """Test building diagnostic report."""
        report = builder.build_diagnostic_report(
            metadata=metadata,
            vehicle_info=vehicle_info,
            session_id=None,
            diagnosis_id=None,
        )
        assert report.metadata.report_type == ReportType.DIAGNOSTIC
        assert report.vehicle_info.make == "Hyundai"
        assert report.vehicle_info.model == "i20 Asta"
        assert isinstance(report.dtcs, list)
        assert isinstance(report.rule_findings, list)
        assert isinstance(report.data_provenance, list)
        assert isinstance(report.limitations, list)

    def test_build_vehicle_health_report(self, builder, metadata, vehicle_info):
        """Test building vehicle health report."""
        metadata.report_type = ReportType.VEHICLE_HEALTH
        metadata.data_source = DataSource.MIXED

        report = builder.build_vehicle_health_report(
            metadata=metadata,
            vehicle_info=vehicle_info,
        )
        assert report.metadata.report_type == ReportType.VEHICLE_HEALTH
        assert report.vehicle_info.make == "Hyundai"
        assert isinstance(report.current_dtc_summary, list)
        assert isinstance(report.latest_rule_findings, list)
        assert isinstance(report.sensor_availability, dict)
        assert isinstance(report.component_statuses, list)
        assert isinstance(report.maintenance_history, list)
        assert isinstance(report.upcoming_maintenance, list)
        assert isinstance(report.overdue_maintenance, list)
        assert isinstance(report.safety_observations, list)

    def test_build_performance_report(self, builder, metadata, vehicle_info):
        """Test building performance report."""
        metadata.report_type = ReportType.PERFORMANCE

        report = builder.build_performance_report(
            metadata=metadata,
            vehicle_info=vehicle_info,
            session_id=None,
        )
        assert report.metadata.report_type == ReportType.PERFORMANCE
        assert report.vehicle_info.make == "Hyundai"
        assert report.session is not None
        assert isinstance(report.sensor_statistics, list)
        assert isinstance(report.charts_data, dict)

    def test_build_maintenance_report(self, builder, metadata, vehicle_info):
        """Test building maintenance report."""
        metadata.report_type = ReportType.MAINTENANCE
        metadata.data_source = DataSource.REAL

        report = builder.build_maintenance_report(
            metadata=metadata,
            vehicle_info=vehicle_info,
        )
        assert report.metadata.report_type == ReportType.MAINTENANCE
        assert report.vehicle_info.make == "Hyundai"
        assert report.summary is not None
        assert isinstance(report.maintenance_history, list)
        assert isinstance(report.upcoming_items, list)
        assert isinstance(report.overdue_items, list)

    def test_data_provenance_tracking(self, builder, metadata, vehicle_info):
        """Test that data provenance is tracked in reports."""
        report = builder.build_diagnostic_report(
            metadata=metadata,
            vehicle_info=vehicle_info,
        )

        # Check that provenance entries exist
        assert len(report.data_provenance) > 0
        for prov in report.data_provenance:
            assert isinstance(prov, DataProvenance)
            assert prov.description is not None
            assert prov.source in [DataSource.REAL, DataSource.SIMULATION, DataSource.MIXED, DataSource.UNKNOWN]

    def test_limitations_in_diagnostic_report(self, builder, metadata, vehicle_info):
        """Test that limitations are included in diagnostic report."""
        report = builder.build_diagnostic_report(
            metadata=metadata,
            vehicle_info=vehicle_info,
        )

        # Should have limitations for simulation data
        assert isinstance(report.limitations, list)
        assert len(report.limitations) > 0
        # Check for simulation-specific limitations
        limitation_text = " ".join(report.limitations).lower()
        assert "simulation" in limitation_text or "demo" in limitation_text


class TestReportDataBuilderConvenience:
    """Test convenience functions."""

    def test_build_diagnostic_report_convenience(self):
        """Test convenience function for diagnostic report."""
        from services.report_data_builder import build_diagnostic_report

        report = build_diagnostic_report()
        assert report.metadata.report_type == ReportType.DIAGNOSTIC

    def test_build_vehicle_health_report_convenience(self):
        """Test convenience function for vehicle health report."""
        from services.report_data_builder import build_vehicle_health_report

        report = build_vehicle_health_report()
        assert report.metadata.report_type == ReportType.VEHICLE_HEALTH

    def test_build_performance_report_convenience(self):
        """Test convenience function for performance report."""
        from services.report_data_builder import build_performance_report

        report = build_performance_report()
        assert report.metadata.report_type == ReportType.PERFORMANCE

    def test_build_maintenance_report_convenience(self):
        """Test convenience function for maintenance report."""
        from services.report_data_builder import build_maintenance_report

        report = build_maintenance_report()
        assert report.metadata.report_type == ReportType.MAINTENANCE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
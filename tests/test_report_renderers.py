"""
Tests for report renderers (HTML and PDF).
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import os

from services.report_models import (
    ReportType,
    ReportFormat,
    DataSource,
    DiagnosticSeverity,
    RuleSeverity,
    ReportMetadata,
    ReportVehicleInfo,
    DiagnosticReportData,
    VehicleHealthReportData,
    PerformanceReportData,
    MaintenanceReportData,
    PerformanceSessionSummary,
    MaintenanceSummary,
    DataProvenance,
    ComponentStatus,
    SensorStatistics,
    DTCReportItem,
    AIDiagnosisReportItem,
    RuleFindingReportItem,
    TelemetrySummary,
)
from services.report_renderers import HTMLRenderer, PDFRenderer


class TestHTMLRenderer:
    """Test HTMLRenderer class."""

    @pytest.fixture
    def renderer(self):
        """Create HTMLRenderer instance."""
        return HTMLRenderer()

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

    @pytest.fixture
    def diagnostic_report(self, metadata, vehicle_info):
        """Create a minimal diagnostic report."""
        return DiagnosticReportData(
            metadata=metadata,
            vehicle_info=vehicle_info,
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
            data_provenance=[
                DataProvenance(
                    description="Test data",
                    source=DataSource.SIMULATION,
                    record_count=100,
                )
            ],
            limitations=["Test limitation"],
        )

    @pytest.fixture
    def vehicle_health_report(self, metadata, vehicle_info):
        """Create a minimal vehicle health report."""
        metadata.report_type = ReportType.VEHICLE_HEALTH
        metadata.data_source = DataSource.MIXED

        return VehicleHealthReportData(
            metadata=metadata,
            vehicle_info=vehicle_info,
            overall_conclusion="Vehicle in good condition",
            latest_diagnostic_summary={"dtc_count": 0},
            current_dtc_summary=[],
            latest_rule_findings=[],
            latest_ai_diagnosis=None,
            sensor_availability={"RPM": True, "SPEED": True},
            telemetry_summary=None,
            component_statuses=[
                ComponentStatus(name="Engine", status="normal", description="OK", evidence=[])
            ],
            maintenance_history=[],
            upcoming_maintenance=[],
            overdue_maintenance=[],
            safety_observations=[],
            data_provenance=[],
        )

    @pytest.fixture
    def performance_report(self, metadata, vehicle_info):
        """Create a minimal performance report."""
        metadata.report_type = ReportType.PERFORMANCE

        return PerformanceReportData(
            metadata=metadata,
            vehicle_info=vehicle_info,
            session=PerformanceSessionSummary(
                session_id=123,
                session_name="Test Drive",
                scenario="city",
                start_time=datetime.now(),
                record_count=100,
                data_source=DataSource.SIMULATION,
            ),
            sensor_statistics=[
                SensorStatistics(
                    sensor_name="RPM",
                    unit="RPM",
                    count=100,
                    min_value=700.0,
                    max_value=3500.0,
                    avg_value=1800.0,
                    std_dev=500.0,
                )
            ],
            charts_data={},
            data_provenance=[],
        )

    @pytest.fixture
    def maintenance_report(self, metadata, vehicle_info):
        """Create a minimal maintenance report."""
        metadata.report_type = ReportType.MAINTENANCE
        metadata.data_source = DataSource.REAL

        return MaintenanceReportData(
            metadata=metadata,
            vehicle_info=vehicle_info,
            odometer_km=15000,
            summary=MaintenanceSummary(
                total_records=5,
                total_cost_inr=12500.0,
                upcoming_count=2,
                overdue_count=1,
                cost_by_category={"Oil Change": 5000.0},
            ),
            maintenance_history=[],
            upcoming_items=[],
            overdue_items=[],
            data_provenance=[],
        )

    def test_render_diagnostic_report(self, renderer, diagnostic_report):
        """Test rendering diagnostic report to HTML."""
        html = renderer.render_diagnostic_report(diagnostic_report)
        assert isinstance(html, str)
        assert len(html) > 0
        assert "i20 AI Garage" in html
        assert "Comprehensive Diagnostic Report" in html
        assert "TEST123" in html
        assert "Hyundai i20" in html
        # Check for key sections
        assert "DTC Scan Results" in html or "No DTCs" in html
        assert "Data Provenance" in html
        assert "Report Limitations" in html

    def test_render_vehicle_health_report(self, renderer, vehicle_health_report):
        """Test rendering vehicle health report to HTML."""
        html = renderer.render_vehicle_health_report(vehicle_health_report)
        assert isinstance(html, str)
        assert len(html) > 0
        assert "i20 AI Garage" in html
        assert "Vehicle Health Report" in html
        assert "Vehicle in good condition" in html
        assert "Component Status Summary" in html

    def test_render_performance_report(self, renderer, performance_report):
        """Test rendering performance report to HTML."""
        html = renderer.render_performance_report(performance_report)
        assert isinstance(html, str)
        assert len(html) > 0
        assert "i20 AI Garage" in html
        assert "Performance Report" in html
        assert "Test Drive" in html
        assert "Sensor Statistics" in html

    def test_render_maintenance_report(self, renderer, maintenance_report):
        """Test rendering maintenance report to HTML."""
        html = renderer.render_maintenance_report(maintenance_report)
        assert isinstance(html, str)
        assert len(html) > 0
        assert "i20 AI Garage" in html
        assert "Maintenance Report" in html
        assert "Current Vehicle Status" in html
        assert "Manufacturer Recommended Intervals" in html

    def test_render_report_union(self, renderer, diagnostic_report, vehicle_health_report,
                                  performance_report, maintenance_report):
        """Test render_report method with different report types."""
        for report in [diagnostic_report, vehicle_health_report, performance_report, maintenance_report]:
            html = renderer.render_report(report)
            assert isinstance(html, str)
            assert len(html) > 0
            assert "i20 AI Garage" in html

    def test_save_report(self, renderer, diagnostic_report):
        """Test saving report to file."""
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
            temp_path = Path(f.name)

        try:
            result = renderer.save_report(diagnostic_report, temp_path)
            assert result is True
            assert temp_path.exists()
            content = temp_path.read_text(encoding='utf-8')
            assert "i20 AI Garage" in content
            assert "TEST123" in content
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_html_escaping(self, renderer, metadata, vehicle_info):
        """Test that HTML escaping is applied."""
        # Create report with potentially dangerous content
        report = DiagnosticReportData(
            metadata=metadata,
            vehicle_info=vehicle_info,
            dtcs=[DTCReportItem(
                code="P0300",
                description="<script>alert('xss')</script>",
                severity=DiagnosticSeverity.MAJOR,
                status="active",
                data_source=DataSource.SIMULATION,
            )],
            ai_diagnosis=None,
            rule_findings=[],
            telemetry_summary=None,
            recommendations={},
            data_provenance=[],
            limitations=[],
        )

        html = renderer.render_diagnostic_report(report)
        # The dangerous content should be escaped
        assert "<script>" not in html
        # Check that escaped version is present (html.escape converts < to <, > to >)
        assert "&lt;script&gt;" in html
        assert "alert" in html


class TestPDFRenderer:
    """Test PDFRenderer class."""

    @pytest.fixture
    def renderer(self):
        """Create PDFRenderer instance."""
        return PDFRenderer()

    @pytest.fixture
    def metadata(self):
        """Create test metadata."""
        return ReportMetadata(
            report_id="TEST123",
            report_type=ReportType.DIAGNOSTIC,
            generated_at=datetime.now(),
            format=ReportFormat.PDF,
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

    @pytest.fixture
    def diagnostic_report(self, metadata, vehicle_info):
        """Create a minimal diagnostic report."""
        return DiagnosticReportData(
            metadata=metadata,
            vehicle_info=vehicle_info,
            dtcs=[],
            ai_diagnosis=None,
            rule_findings=[],
            telemetry_summary=None,
            recommendations={},
            data_provenance=[
                DataProvenance(
                    description="Test data",
                    source=DataSource.SIMULATION,
                    record_count=100,
                )
            ],
            limitations=["Test limitation"],
        )

    def test_render_report_bytes(self, renderer, diagnostic_report):
        """Test rendering report to PDF bytes."""
        pdf_bytes = renderer.render_report_bytes(diagnostic_report)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        # Check for PDF header
        assert pdf_bytes[:4] == b'%PDF'

    def test_render_report_to_file(self, renderer, diagnostic_report):
        """Test rendering report to PDF file."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = Path(f.name)

        try:
            result = renderer.render_report(diagnostic_report, temp_path)
            assert result is True
            assert temp_path.exists()
            assert temp_path.stat().st_size > 0
            # Check for PDF header
            with open(temp_path, 'rb') as f:
                header = f.read(4)
                assert header == b'%PDF'
        finally:
            if temp_path.exists():
                temp_path.unlink()


class TestConvenienceFunctions:
    """Test convenience functions."""

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

    def test_render_diagnostic_report_html(self, metadata, vehicle_info):
        """Test HTML convenience function."""
        from services.report_renderers import render_diagnostic_report_html

        report = DiagnosticReportData(
            metadata=metadata,
            vehicle_info=vehicle_info,
            dtcs=[],
            ai_diagnosis=None,
            rule_findings=[],
            telemetry_summary=None,
            recommendations={},
            data_provenance=[],
            limitations=[],
        )
        html = render_diagnostic_report_html(report)
        assert isinstance(html, str)
        assert "Comprehensive Diagnostic Report" in html

    def test_render_vehicle_health_report_html(self, metadata, vehicle_info):
        """Test HTML convenience function."""
        from services.report_renderers import render_vehicle_health_report_html

        metadata.report_type = ReportType.VEHICLE_HEALTH
        report = VehicleHealthReportData(
            metadata=metadata,
            vehicle_info=vehicle_info,
            overall_conclusion="OK",
            latest_diagnostic_summary={},
            current_dtc_summary=[],
            latest_rule_findings=[],
            latest_ai_diagnosis=None,
            sensor_availability={},
            telemetry_summary=None,
            component_statuses=[],
            maintenance_history=[],
            upcoming_maintenance=[],
            overdue_maintenance=[],
            safety_observations=[],
            data_provenance=[],
        )
        html = render_vehicle_health_report_html(report)
        assert isinstance(html, str)
        assert "Vehicle Health Report" in html

    def test_render_performance_report_html(self, metadata, vehicle_info):
        """Test HTML convenience function."""
        from services.report_renderers import render_performance_report_html

        metadata.report_type = ReportType.PERFORMANCE
        report = PerformanceReportData(
            metadata=metadata,
            vehicle_info=vehicle_info,
            session=PerformanceSessionSummary(
                session_id=1,
                session_name="Test",
                scenario="city",
                start_time=datetime.now(),
                record_count=100,
                data_source=DataSource.SIMULATION,
            ),
            sensor_statistics=[],
            charts_data={},
            data_provenance=[],
        )
        html = render_performance_report_html(report)
        assert isinstance(html, str)
        assert "Performance Report" in html

    def test_render_maintenance_report_html(self, metadata, vehicle_info):
        """Test HTML convenience function."""
        from services.report_renderers import render_maintenance_report_html

        metadata.report_type = ReportType.MAINTENANCE
        report = MaintenanceReportData(
            metadata=metadata,
            vehicle_info=vehicle_info,
            odometer_km=0,
            summary=MaintenanceSummary(
                total_records=0,
                total_cost_inr=0.0,
                upcoming_count=0,
                overdue_count=0,
                cost_by_category={},
            ),
            maintenance_history=[],
            upcoming_items=[],
            overdue_items=[],
            data_provenance=[],
        )
        html = render_maintenance_report_html(report)
        assert isinstance(html, str)
        assert "Maintenance Report" in html

    def test_render_diagnostic_report_pdf(self, metadata, vehicle_info):
        """Test PDF convenience function."""
        from services.report_renderers import render_diagnostic_report_pdf

        report = DiagnosticReportData(
            metadata=metadata,
            vehicle_info=vehicle_info,
            dtcs=[],
            ai_diagnosis=None,
            rule_findings=[],
            telemetry_summary=None,
            recommendations={},
            data_provenance=[],
            limitations=[],
        )
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = Path(f.name)

        try:
            result = render_diagnostic_report_pdf(report, temp_path)
            assert result is True
            assert temp_path.exists()
            assert temp_path.stat().st_size > 0
        finally:
            if temp_path.exists():
                temp_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

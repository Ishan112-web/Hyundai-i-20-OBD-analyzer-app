"""
Tests for report generator orchestrator.
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import os

from services.report_models import (
    ReportType,
    ReportFormat,
)
from services.report_generator import ReportGenerator


class TestReportGenerator:
    """Test ReportGenerator class."""

    @pytest.fixture
    def generator(self):
        """Create ReportGenerator instance."""
        return ReportGenerator()

    def test_generator_initialization(self, generator):
        """Test generator initializes correctly."""
        assert generator.data_builder is not None
        assert generator.html_renderer is not None
        assert generator.pdf_renderer is not None
        assert generator.output_dir.exists()

    def test_generate_diagnostic_report_html(self, generator):
        """Test generating diagnostic report in HTML format."""
        html = generator.generate_diagnostic_report(
            session_id=None,
            diagnosis_id=None,
            format_type=ReportFormat.HTML,
        )
        assert isinstance(html, str)
        assert len(html) > 0
        assert "i20 AI Garage" in html
        assert "Comprehensive Diagnostic Report" in html
        assert "Data Provenance" in html
        assert "Report Limitations" in html

    def test_generate_diagnostic_report_pdf(self, generator):
        """Test generating diagnostic report in PDF format."""
        pdf_bytes = generator.generate_diagnostic_report(
            session_id=None,
            diagnosis_id=None,
            format_type=ReportFormat.PDF,
        )
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b'%PDF'

    def test_generate_diagnostic_report_html_to_file(self, generator):
        """Test generating diagnostic report and saving to HTML file."""
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
            temp_path = Path(f.name)

        try:
            result = generator.generate_diagnostic_report(
                format_type=ReportFormat.HTML,
                output_path=temp_path,
            )
            assert result == temp_path
            assert temp_path.exists()
            content = temp_path.read_text(encoding='utf-8')
            assert "i20 AI Garage" in content
            assert "Comprehensive Diagnostic Report" in content
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_generate_diagnostic_report_pdf_to_file(self, generator):
        """Test generating diagnostic report and saving to PDF file."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = Path(f.name)

        try:
            result = generator.generate_diagnostic_report(
                format_type=ReportFormat.PDF,
                output_path=temp_path,
            )
            assert result == temp_path
            assert temp_path.exists()
            assert temp_path.stat().st_size > 0
            with open(temp_path, 'rb') as f:
                header = f.read(4)
                assert header == b'%PDF'
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_generate_vehicle_health_report_html(self, generator):
        """Test generating vehicle health report in HTML format."""
        html = generator.generate_vehicle_health_report(
            format_type=ReportFormat.HTML,
        )
        assert isinstance(html, str)
        assert len(html) > 0
        assert "i20 AI Garage" in html
        assert "Vehicle Health Report" in html
        assert "Component Status Summary" in html
        assert "Maintenance History" in html

    def test_generate_vehicle_health_report_pdf(self, generator):
        """Test generating vehicle health report in PDF format."""
        pdf_bytes = generator.generate_vehicle_health_report(
            format_type=ReportFormat.PDF,
        )
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b'%PDF'

    def test_generate_performance_report_html(self, generator):
        """Test generating performance report in HTML format."""
        html = generator.generate_performance_report(
            session_id=None,
            format_type=ReportFormat.HTML,
        )
        assert isinstance(html, str)
        assert len(html) > 0
        assert "i20 AI Garage" in html
        assert "Performance Report" in html
        assert "Session Summary" in html
        assert "Sensor Statistics" in html

    def test_generate_performance_report_pdf(self, generator):
        """Test generating performance report in PDF format."""
        pdf_bytes = generator.generate_performance_report(
            session_id=None,
            format_type=ReportFormat.PDF,
        )
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b'%PDF'

    def test_generate_maintenance_report_html(self, generator):
        """Test generating maintenance report in HTML format."""
        html = generator.generate_maintenance_report(
            format_type=ReportFormat.HTML,
        )
        assert isinstance(html, str)
        assert len(html) > 0
        assert "i20 AI Garage" in html
        assert "Maintenance Report" in html
        assert "Current Vehicle Status" in html
        assert "Manufacturer Recommended Intervals" in html

    def test_generate_maintenance_report_pdf(self, generator):
        """Test generating maintenance report in PDF format."""
        pdf_bytes = generator.generate_maintenance_report(
            format_type=ReportFormat.PDF,
        )
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b'%PDF'

    def test_generate_report_by_type(self, generator):
        """Test generate_report method with different types."""
        for report_type in [ReportType.DIAGNOSTIC, ReportType.VEHICLE_HEALTH,
                           ReportType.PERFORMANCE, ReportType.MAINTENANCE]:
            html = generator.generate_report(
                report_type=report_type,
                format_type=ReportFormat.HTML,
            )
            assert isinstance(html, str)
            assert len(html) > 0
            assert "i20 AI Garage" in html

    def test_generate_all_reports(self, generator):
        """Test generating all reports at once."""
        results = generator.generate_all_reports(
            format_type=ReportFormat.HTML,
        )

        assert isinstance(results, dict)
        assert len(results) == 4
        assert ReportType.DIAGNOSTIC in results
        assert ReportType.VEHICLE_HEALTH in results
        assert ReportType.PERFORMANCE in results
        assert ReportType.MAINTENANCE in results

        for report_type, content in results.items():
            assert isinstance(content, str)
            assert len(content) > 0
            assert "i20 AI Garage" in content

    def test_generate_all_reports_to_directory(self, generator):
        """Test generating all reports to a directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            results = generator.generate_all_reports(
                format_type=ReportFormat.HTML,
                output_dir=temp_path,
            )

            for report_type, result in results.items():
                assert isinstance(result, Path)
                assert result.exists()
                assert result.suffix == '.html'
                content = result.read_text(encoding='utf-8')
                assert "i20 AI Garage" in content

    def test_get_available_sessions(self, generator):
        """Test getting available sessions."""
        sessions = generator.get_available_sessions()
        assert isinstance(sessions, list)
        # Sessions list may be empty in test environment

    def test_get_available_diagnoses(self, generator):
        """Test getting available diagnoses."""
        diagnoses = generator.get_available_diagnoses()
        assert isinstance(diagnoses, list)
        # Diagnoses list may be empty in test environment

    def test_vehicle_override(self, generator):
        """Test vehicle info override."""
        vehicle_override = {
            "make": "TestMake",
            "model": "TestModel",
            "year": 2025,
            "engine": "Test Engine",
            "transmission": "Automatic",
            "fuel_type": "Electric",
            "market": "Test Market",
            "odometer_km": 50000,
            "vin": "TESTVIN123456789",
        }

        html = generator.generate_diagnostic_report(
            format_type=ReportFormat.HTML,
            vehicle_override=vehicle_override,
        )

        assert "TestMake" in html
        assert "TestModel" in html
        assert "2025" in html
        assert "50000 km" in html
        assert "TESTVIN123456789" in html


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_generate_diagnostic_report(self):
        """Test convenience function for diagnostic report."""
        from services.report_generator import generate_diagnostic_report

        html = generate_diagnostic_report(format_type=ReportFormat.HTML)
        assert isinstance(html, str)
        assert "Comprehensive Diagnostic Report" in html

    def test_generate_vehicle_health_report(self):
        """Test convenience function for vehicle health report."""
        from services.report_generator import generate_vehicle_health_report

        html = generate_vehicle_health_report(format_type=ReportFormat.HTML)
        assert isinstance(html, str)
        assert "Vehicle Health Report" in html

    def test_generate_performance_report(self):
        """Test convenience function for performance report."""
        from services.report_generator import generate_performance_report

        html = generate_performance_report(format_type=ReportFormat.HTML)
        assert isinstance(html, str)
        assert "Performance Report" in html

    def test_generate_maintenance_report(self):
        """Test convenience function for maintenance report."""
        from services.report_generator import generate_maintenance_report

        html = generate_maintenance_report(format_type=ReportFormat.HTML)
        assert isinstance(html, str)
        assert "Maintenance Report" in html


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
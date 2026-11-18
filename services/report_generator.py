"""
i20 AI Garage - Report Generator Orchestrator

Orchestrates report generation by combining data building and rendering.
Provides a unified interface for generating all report types in HTML and PDF formats.
"""

import io
from pathlib import Path
from typing import Optional, Union, Dict, Any, List
from datetime import datetime
from uuid import uuid4

from services.report_models import (
    ReportType,
    ReportFormat,
    DataSource,
    DiagnosticReportData,
    VehicleHealthReportData,
    PerformanceReportData,
    MaintenanceReportData,
    ReportDataUnion,
    ReportMetadata,
    ReportVehicleInfo,
    DataProvenance,
)
from services.report_data_builder import ReportDataBuilder
from services.report_renderers import HTMLRenderer, PDFRenderer


class ReportGenerator:
    """
    Orchestrates report generation for all report types.

    Combines data assembly from ReportDataBuilder with rendering from
    HTMLRenderer and PDFRenderer to produce professional reports.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        templates_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None,
    ):
        """
        Initialize the report generator.

        Args:
            db_path: Path to SQLite database
            templates_dir: Path to Jinja2 templates directory
            output_dir: Default output directory for generated reports
        """
        self.data_builder = ReportDataBuilder(database=db_path)
        self.html_renderer = HTMLRenderer(templates_dir=templates_dir)
        self.pdf_renderer = PDFRenderer()
        self.output_dir = output_dir or Path("reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _create_metadata(
        self,
        report_type: ReportType,
        data_source: DataSource,
        format_type: ReportFormat,
    ) -> ReportMetadata:
        """Create report metadata."""
        return ReportMetadata(
            report_id=str(uuid4())[:8].upper(),
            report_type=report_type,
            generated_at=datetime.now(),
            format=format_type,
            data_source=data_source,
            generator_version="1.0.0",
        )

    def _create_vehicle_info(self, vehicle_data: Union[Dict[str, Any], "ReportVehicleInfo"]) -> ReportVehicleInfo:
        """Create ReportVehicleInfo from database data or existing object."""
        if isinstance(vehicle_data, ReportVehicleInfo):
            return vehicle_data
        return ReportVehicleInfo(
            make=vehicle_data.get("make", "Hyundai"),
            model=vehicle_data.get("model", "i20 Asta"),
            year=vehicle_data.get("year", 2023),
            engine=vehicle_data.get("engine", "1.2L Naturally Aspirated Petrol"),
            transmission=vehicle_data.get("transmission", "Manual"),
            fuel_type=vehicle_data.get("fuel_type", "Petrol"),
            market=vehicle_data.get("market", "India"),
            ecu_tuning=vehicle_data.get("ecu_tuning", "Stock"),
            odometer_km=vehicle_data.get("odometer_km"),
            vin=vehicle_data.get("vin"),
        )

    def generate_diagnostic_report(
        self,
        session_id: Optional[str] = None,
        diagnosis_id: Optional[str] = None,
        format_type: ReportFormat = ReportFormat.HTML,
        output_path: Optional[Path] = None,
        vehicle_override: Optional[Dict[str, Any]] = None,
    ) -> Union[str, bytes, Path]:
        """
        Generate a comprehensive diagnostic report.

        Args:
            session_id: OBD session ID (for real data)
            diagnosis_id: AI diagnosis ID (for real data)
            format_type: Output format (HTML or PDF)
            output_path: Optional path to save file
            vehicle_override: Optional vehicle info override

        Returns:
            HTML string, PDF bytes, or saved file path
        """
        # Determine data source
        data_source = DataSource.REAL if session_id or diagnosis_id else DataSource.SIMULATION

        # Build report data
        metadata = self._create_metadata(ReportType.DIAGNOSTIC, data_source, format_type)
        vehicle_data = vehicle_override or self.data_builder._get_vehicle_info()
        vehicle_info = self._create_vehicle_info(vehicle_data)

        report_data = self.data_builder.build_diagnostic_report(
            metadata=metadata,
            vehicle_info=vehicle_info,
            session_id=session_id,
            diagnosis_id=diagnosis_id,
        )

        # Render
        if format_type == ReportFormat.HTML:
            html_content = self.html_renderer.render_report(report_data)
            if output_path:
                self.html_renderer.save_report(report_data, output_path)
                return output_path
            return html_content
        else:
            pdf_bytes = self.pdf_renderer.render_report_bytes(report_data)
            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(pdf_bytes)
                return output_path
            return pdf_bytes

    def generate_vehicle_health_report(
        self,
        format_type: ReportFormat = ReportFormat.HTML,
        output_path: Optional[Path] = None,
        vehicle_override: Optional[Dict[str, Any]] = None,
    ) -> Union[str, bytes, Path]:
        """
        Generate a vehicle health report.

        Args:
            format_type: Output format (HTML or PDF)
            output_path: Optional path to save file
            vehicle_override: Optional vehicle info override

        Returns:
            HTML string, PDF bytes, or saved file path
        """
        metadata = self._create_metadata(ReportType.VEHICLE_HEALTH, DataSource.MIXED, format_type)
        vehicle_data = vehicle_override or self.data_builder._get_vehicle_info()
        vehicle_info = self._create_vehicle_info(vehicle_data)

        report_data = self.data_builder.build_vehicle_health_report(
            metadata=metadata,
            vehicle_info=vehicle_info,
        )

        if format_type == ReportFormat.HTML:
            html_content = self.html_renderer.render_report(report_data)
            if output_path:
                self.html_renderer.save_report(report_data, output_path)
                return output_path
            return html_content
        else:
            pdf_bytes = self.pdf_renderer.render_report_bytes(report_data)
            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(pdf_bytes)
                return output_path
            return pdf_bytes

    def generate_performance_report(
        self,
        session_id: Optional[str] = None,
        format_type: ReportFormat = ReportFormat.HTML,
        output_path: Optional[Path] = None,
        vehicle_override: Optional[Dict[str, Any]] = None,
    ) -> Union[str, bytes, Path]:
        """
        Generate a performance report.

        Args:
            session_id: OBD session ID (for real data)
            format_type: Output format (HTML or PDF)
            output_path: Optional path to save file
            vehicle_override: Optional vehicle info override

        Returns:
            HTML string, PDF bytes, or saved file path
        """
        data_source = DataSource.REAL if session_id else DataSource.SIMULATION

        metadata = self._create_metadata(ReportType.PERFORMANCE, data_source, format_type)
        vehicle_data = vehicle_override or self.data_builder._get_vehicle_info()
        vehicle_info = self._create_vehicle_info(vehicle_data)

        report_data = self.data_builder.build_performance_report(
            metadata=metadata,
            vehicle_info=vehicle_info,
            session_id=session_id,
        )

        if format_type == ReportFormat.HTML:
            html_content = self.html_renderer.render_report(report_data)
            if output_path:
                self.html_renderer.save_report(report_data, output_path)
                return output_path
            return html_content
        else:
            pdf_bytes = self.pdf_renderer.render_report_bytes(report_data)
            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(pdf_bytes)
                return output_path
            return pdf_bytes

    def generate_maintenance_report(
        self,
        format_type: ReportFormat = ReportFormat.HTML,
        output_path: Optional[Path] = None,
        vehicle_override: Optional[Dict[str, Any]] = None,
    ) -> Union[str, bytes, Path]:
        """
        Generate a maintenance report.

        Args:
            format_type: Output format (HTML or PDF)
            output_path: Optional path to save file
            vehicle_override: Optional vehicle info override

        Returns:
            HTML string, PDF bytes, or saved file path
        """
        metadata = self._create_metadata(ReportType.MAINTENANCE, DataSource.REAL, format_type)
        vehicle_data = vehicle_override or self.data_builder._get_vehicle_info()
        vehicle_info = self._create_vehicle_info(vehicle_data)

        report_data = self.data_builder.build_maintenance_report(
            metadata=metadata,
            vehicle_info=vehicle_info,
        )

        if format_type == ReportFormat.HTML:
            html_content = self.html_renderer.render_report(report_data)
            if output_path:
                self.html_renderer.save_report(report_data, output_path)
                return output_path
            return html_content
        else:
            pdf_bytes = self.pdf_renderer.render_report_bytes(report_data)
            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(pdf_bytes)
                return output_path
            return pdf_bytes

    def generate_report(
        self,
        report_type: ReportType,
        format_type: ReportFormat = ReportFormat.HTML,
        output_path: Optional[Path] = None,
        **kwargs,
    ) -> Union[str, bytes, Path]:
        """
        Generate any report type by name.

        Args:
            report_type: Type of report to generate
            format_type: Output format
            output_path: Optional path to save file
            **kwargs: Additional arguments passed to specific generators

        Returns:
            HTML string, PDF bytes, or saved file path
        """
        generators = {
            ReportType.DIAGNOSTIC: self.generate_diagnostic_report,
            ReportType.VEHICLE_HEALTH: self.generate_vehicle_health_report,
            ReportType.PERFORMANCE: self.generate_performance_report,
            ReportType.MAINTENANCE: self.generate_maintenance_report,
        }

        generator = generators.get(report_type)
        if not generator:
            raise ValueError(f"Unknown report type: {report_type}")

        return generator(
            format_type=format_type,
            output_path=output_path,
            **kwargs,
        )

    def generate_all_reports(
        self,
        format_type: ReportFormat = ReportFormat.HTML,
        output_dir: Optional[Path] = None,
        **kwargs,
    ) -> Dict[ReportType, Union[str, bytes, Path]]:
        """
        Generate all four report types at once.

        Args:
            format_type: Output format for all reports
            output_dir: Directory to save files (if saving). If None, returns content strings/bytes.
            **kwargs: Additional arguments passed to generators

        Returns:
            Dictionary mapping report types to generated content/paths
        """
        save_to_files = output_dir is not None
        if save_to_files:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = "html" if format_type == ReportFormat.HTML else "pdf"

        results = {}

        # Diagnostic Report
        diag_path = output_dir / f"diagnostic_report_{timestamp}.{ext}" if save_to_files else None
        results[ReportType.DIAGNOSTIC] = self.generate_diagnostic_report(
            format_type=format_type,
            output_path=diag_path,
            **kwargs,
        )

        # Vehicle Health Report
        health_path = output_dir / f"vehicle_health_report_{timestamp}.{ext}" if save_to_files else None
        results[ReportType.VEHICLE_HEALTH] = self.generate_vehicle_health_report(
            format_type=format_type,
            output_path=health_path,
            **kwargs,
        )

        # Performance Report
        perf_path = output_dir / f"performance_report_{timestamp}.{ext}" if save_to_files else None
        results[ReportType.PERFORMANCE] = self.generate_performance_report(
            format_type=format_type,
            output_path=perf_path,
            **kwargs,
        )

        # Maintenance Report
        maint_path = output_dir / f"maintenance_report_{timestamp}.{ext}" if save_to_files else None
        results[ReportType.MAINTENANCE] = self.generate_maintenance_report(
            format_type=format_type,
            output_path=maint_path,
            **kwargs,
        )

        return results

    def get_available_sessions(self) -> List[Dict[str, Any]]:
        """Get list of available OBD sessions for report generation."""
        import sqlite3

        sessions = []
        try:
            with sqlite3.connect(self.data_builder.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT session_id, session_name, scenario, start_time, end_time,
                           duration_seconds, record_count, data_source
                    FROM obd_sessions
                    ORDER BY start_time DESC
                """)
                for row in cursor.fetchall():
                    sessions.append(dict(row))
        except Exception as e:
            print(f"Error fetching sessions: {e}")

        return sessions

    def get_available_diagnoses(self) -> List[Dict[str, Any]]:
        """Get list of available AI diagnoses for report generation."""
        import sqlite3

        diagnoses = []
        try:
            with sqlite3.connect(self.data_builder.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT diagnosis_id, session_id, timestamp, confidence,
                           severity, data_quality, data_source, estimated_cost_inr
                    FROM ai_diagnoses
                    ORDER BY timestamp DESC
                """)
                for row in cursor.fetchall():
                    diagnoses.append(dict(row))
        except Exception as e:
            print(f"Error fetching diagnoses: {e}")

        return diagnoses


# Convenience functions for direct use
def generate_diagnostic_report(
    session_id: Optional[str] = None,
    diagnosis_id: Optional[str] = None,
    format_type: ReportFormat = ReportFormat.HTML,
    output_path: Optional[Path] = None,
    db_path: Optional[str] = None,
) -> Union[str, bytes, Path]:
    """Generate a diagnostic report (convenience function)."""
    generator = ReportGenerator(db_path=db_path)
    return generator.generate_diagnostic_report(
        session_id=session_id,
        diagnosis_id=diagnosis_id,
        format_type=format_type,
        output_path=output_path,
    )


def generate_vehicle_health_report(
    format_type: ReportFormat = ReportFormat.HTML,
    output_path: Optional[Path] = None,
    db_path: Optional[str] = None,
) -> Union[str, bytes, Path]:
    """Generate a vehicle health report (convenience function)."""
    generator = ReportGenerator(db_path=db_path)
    return generator.generate_vehicle_health_report(
        format_type=format_type,
        output_path=output_path,
    )


def generate_performance_report(
    session_id: Optional[str] = None,
    format_type: ReportFormat = ReportFormat.HTML,
    output_path: Optional[Path] = None,
    db_path: Optional[str] = None,
) -> Union[str, bytes, Path]:
    """Generate a performance report (convenience function)."""
    generator = ReportGenerator(db_path=db_path)
    return generator.generate_performance_report(
        session_id=session_id,
        format_type=format_type,
        output_path=output_path,
    )


def generate_maintenance_report(
    format_type: ReportFormat = ReportFormat.HTML,
    output_path: Optional[Path] = None,
    db_path: Optional[str] = None,
) -> Union[str, bytes, Path]:
    """Generate a maintenance report (convenience function)."""
    generator = ReportGenerator(db_path=db_path)
    return generator.generate_maintenance_report(
        format_type=format_type,
        output_path=output_path,
    )
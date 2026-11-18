"""
i20 AI Garage - HTML Report Renderer

Renders professional HTML reports using Jinja2 templates.
Generates standalone HTML files that work offline and print cleanly.
"""

from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

from jinja2 import Environment, FileSystemLoader, select_autoescape

from services.report_models import (
    ReportType,
    ReportFormat,
    DiagnosticReportData,
    VehicleHealthReportData,
    PerformanceReportData,
    MaintenanceReportData,
    ReportDataUnion,
)


class HTMLRenderer:
    """
    Renders report data to professional HTML using Jinja2 templates.

    Features:
    - Offline-capable (embedded CSS, no external dependencies)
    - Print-optimized with proper page breaks
    - Responsive design
    - HTML escaping for security
    """

    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize the HTML renderer.

        Args:
            templates_dir: Path to templates directory (defaults to services/report_templates)
        """
        if templates_dir is None:
            templates_dir = Path(__file__).parent.parent / "report_templates"

        self.templates_dir = Path(templates_dir)

        # Setup Jinja2 environment with autoescaping for security
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters
        self.env.filters["tojson"] = self._to_json_filter

    def _to_json_filter(self, value: Any) -> str:
        """Convert value to JSON string for template use."""
        import json
        return json.dumps(value, default=str)

    def _prepare_template_context(self, report_data: ReportDataUnion) -> Dict[str, Any]:
        """Prepare context dictionary for template rendering."""
        # Convert Pydantic models to dict without JSON serialization to preserve enums
        context = report_data.model_dump()

        # Let Jinja2's autoescape handle HTML escaping for security
        # No pre-sanitization needed - autoescape will escape all strings during rendering

        # Add computed fields
        context["report_id"] = context["metadata"]["report_id"]
        # Handle generated_at - could be datetime object or ISO format string
        generated_at = context["metadata"]["generated_at"]
        if isinstance(generated_at, datetime):
            context["generated_at"] = generated_at
        else:
            context["generated_at"] = datetime.fromisoformat(generated_at)
        # Keep enums as enum objects for template access (e.g., data_source.value)
        # The template expects enums, not strings
        context["format"] = context["metadata"]["format"]
        context["data_source"] = context["metadata"]["data_source"]
        context["report_type"] = context["metadata"]["report_type"]
        context["report_title"] = self._get_report_title(context["report_type"])
        context["vehicle_info"] = context["vehicle_info"]

        return context

    def _get_report_title(self, report_type: str) -> str:
        """Get display title for report type."""
        titles = {
            "diagnostic": "Comprehensive Diagnostic Report",
            "vehicle_health": "Vehicle Health Report",
            "performance": "Performance Report",
            "maintenance": "Maintenance Report",
        }
        return titles.get(report_type, "Report")

    def render_diagnostic_report(self, report_data: DiagnosticReportData) -> str:
        """Render diagnostic report to HTML string."""
        template = self.env.get_template("diagnostic_report.html")
        context = self._prepare_template_context(report_data)
        return template.render(**context)

    def render_vehicle_health_report(self, report_data: VehicleHealthReportData) -> str:
        """Render vehicle health report to HTML string."""
        template = self.env.get_template("vehicle_health_report.html")
        context = self._prepare_template_context(report_data)
        return template.render(**context)

    def render_performance_report(self, report_data: PerformanceReportData) -> str:
        """Render performance report to HTML string."""
        template = self.env.get_template("performance_report.html")
        context = self._prepare_template_context(report_data)
        return template.render(**context)

    def render_maintenance_report(self, report_data: MaintenanceReportData) -> str:
        """Render maintenance report to HTML string."""
        template = self.env.get_template("maintenance_report.html")
        context = self._prepare_template_context(report_data)
        return template.render(**context)

    def render_report(self, report_data: ReportDataUnion) -> str:
        """
        Render any report type to HTML string.

        Args:
            report_data: The report data model

        Returns:
            Rendered HTML string
        """
        if isinstance(report_data, DiagnosticReportData):
            return self.render_diagnostic_report(report_data)
        elif isinstance(report_data, VehicleHealthReportData):
            return self.render_vehicle_health_report(report_data)
        elif isinstance(report_data, PerformanceReportData):
            return self.render_performance_report(report_data)
        elif isinstance(report_data, MaintenanceReportData):
            return self.render_maintenance_report(report_data)
        else:
            raise ValueError(f"Unknown report type: {type(report_data)}")

    def save_report(self, report_data: ReportDataUnion, output_path: Path) -> bool:
        """
        Render and save report to file.

        Args:
            report_data: The report data model
            output_path: Path to save HTML file

        Returns:
            True if successful
        """
        try:
            html_content = self.render_report(report_data)
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html_content, encoding="utf-8")
            return True
        except Exception as e:
            print(f"Error saving HTML report: {e}")
            return False


# Convenience functions
def render_diagnostic_report_html(report_data: DiagnosticReportData) -> str:
    """Render diagnostic report to HTML string."""
    renderer = HTMLRenderer()
    return renderer.render_diagnostic_report(report_data)


def render_vehicle_health_report_html(report_data: VehicleHealthReportData) -> str:
    """Render vehicle health report to HTML string."""
    renderer = HTMLRenderer()
    return renderer.render_vehicle_health_report(report_data)


def render_performance_report_html(report_data: PerformanceReportData) -> str:
    """Render performance report to HTML string."""
    renderer = HTMLRenderer()
    return renderer.render_performance_report(report_data)


def render_maintenance_report_html(report_data: MaintenanceReportData) -> str:
    """Render maintenance report to HTML string."""
    renderer = HTMLRenderer()
    return renderer.render_maintenance_report(report_data)
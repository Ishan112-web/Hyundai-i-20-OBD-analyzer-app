"""
i20 AI Garage - Report Renderers Package
"""

from .html_renderer import (
    HTMLRenderer,
    render_diagnostic_report_html,
    render_vehicle_health_report_html,
    render_performance_report_html,
    render_maintenance_report_html,
)
from .pdf_renderer import (
    PDFRenderer,
    render_diagnostic_report_pdf,
    render_vehicle_health_report_pdf,
    render_performance_report_pdf,
    render_maintenance_report_pdf,
)

__all__ = [
    "HTMLRenderer",
    "PDFRenderer",
    "render_diagnostic_report_html",
    "render_vehicle_health_report_html",
    "render_performance_report_html",
    "render_maintenance_report_html",
    "render_diagnostic_report_pdf",
    "render_vehicle_health_report_pdf",
    "render_performance_report_pdf",
    "render_maintenance_report_pdf",
]
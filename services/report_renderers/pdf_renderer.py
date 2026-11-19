"""
i20 AI Garage - PDF Report Renderer

Renders professional PDF reports using ReportLab.
Pure Python implementation, Windows-compatible, no external dependencies.
"""

import io
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from decimal import Decimal

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm, inch
from reportlab.lib.colors import HexColor, black, white, Color
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable, Frame, PageTemplate,
    BaseDocTemplate, NextPageTemplate
)
from reportlab.platypus.flowables import Flowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.charts.legends import Legend
from reportlab.lib.validators import Auto

from services.report_models import (
    ReportType,
    ReportFormat,
    DiagnosticReportData,
    VehicleHealthReportData,
    PerformanceReportData,
    MaintenanceReportData,
    ReportDataUnion,
)


# =============================================================================
# COLOR PALETTE
# =============================================================================

class ReportColors:
    """Professional color palette for reports."""
    BG_PRIMARY = HexColor("#1a1d21")
    BG_SECONDARY = HexColor("#23272e")
    BG_CARD = HexColor("#2a2e36")
    BORDER = HexColor("#3a3f4a")
    TEXT_PRIMARY = HexColor("#e8eaed")
    TEXT_SECONDARY = HexColor("#9aa3ad")
    ACCENT_BLUE = HexColor("#00b4d8")
    ACCENT_GREEN = HexColor("#2ecc71")
    ACCENT_AMBER = HexColor("#f39c12")
    ACCENT_RED = HexColor("#e74c3c")
    ACCENT_PURPLE = HexColor("#9b59b6")

    # Severity colors
    SEVERITY_CRITICAL = ACCENT_RED
    SEVERITY_MAJOR = ACCENT_AMBER
    SEVERITY_MINOR = HexColor("#3498db")
    SEVERITY_INFO = ACCENT_PURPLE
    SEVERITY_UNKNOWN = TEXT_SECONDARY
    SEVERITY_INFORMATIONAL = HexColor("#3498db")
    SEVERITY_LOW = ACCENT_GREEN
    SEVERITY_MEDIUM = ACCENT_AMBER
    SEVERITY_HIGH = ACCENT_RED

    # Status colors
    STATUS_NORMAL = ACCENT_GREEN
    STATUS_ATTENTION = ACCENT_AMBER
    STATUS_CRITICAL = ACCENT_RED
    STATUS_INSUFFICIENT = TEXT_SECONDARY


# =============================================================================
# CUSTOM FLOWABLES
# =============================================================================

class ColoredBox(Flowable):
    """A colored rectangle with text."""

    def __init__(self, width, height, bg_color, text="", text_color=white, font_size=10, padding=4):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.text = text
        self.text_color = text_color
        self.font_size = font_size
        self.padding = padding

    def draw(self):
        self.canv.setFillColor(self.bg_color)
        self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        if self.text:
            self.canv.setFillColor(self.text_color)
            self.canv.setFont("Helvetica-Bold", self.font_size)
            self.canv.drawString(self.padding, self.height/2 - self.font_size/3, self.text)


class SeverityBadge(Flowable):
    """A badge showing severity level."""

    SEVERITY_COLORS = {
        "critical": ReportColors.SEVERITY_CRITICAL,
        "major": ReportColors.SEVERITY_MAJOR,
        "minor": ReportColors.SEVERITY_MINOR,
        "info": ReportColors.SEVERITY_INFO,
        "unknown": ReportColors.SEVERITY_UNKNOWN,
        "informational": ReportColors.SEVERITY_INFORMATIONAL,
        "low": ReportColors.SEVERITY_LOW,
        "medium": ReportColors.SEVERITY_MEDIUM,
        "high": ReportColors.SEVERITY_HIGH,
    }

    def __init__(self, severity: str, font_size=7):
        Flowable.__init__(self)
        self.severity = severity.lower()
        self.font_size = font_size
        self.text = severity.upper()
        self.bg_color = self.SEVERITY_COLORS.get(self.severity, ReportColors.TEXT_SECONDARY)
        # Calculate width based on text
        self.width = len(self.text) * self.font_size * 0.6 + 10
        self.height = self.font_size * 1.8

    def draw(self):
        self.canv.setFillColor(self.bg_color)
        self.canv.roundRect(0, 0, self.width, self.height, 3, fill=1, stroke=0)
        self.canv.setFillColor(white)
        self.canv.setFont("Helvetica-Bold", self.font_size)
        text_width = self.canv.stringWidth(self.text, "Helvetica-Bold", self.font_size)
        self.canv.drawString((self.width - text_width) / 2, (self.height - self.font_size) / 2, self.text)


class DataSourceBadge(Flowable):
    """A badge showing data source."""

    SOURCE_COLORS = {
        "real": (ReportColors.ACCENT_GREEN, "REAL"),
        "simulation": (ReportColors.ACCENT_AMBER, "SIMULATION"),
        "mixed": (ReportColors.ACCENT_PURPLE, "MIXED"),
        "unknown": (ReportColors.TEXT_SECONDARY, "UNKNOWN"),
    }

    def __init__(self, source: str, font_size=7):
        Flowable.__init__(self)
        self.source = source.lower()
        self.font_size = font_size
        color, text = self.SOURCE_COLORS.get(self.source, (ReportColors.TEXT_SECONDARY, source.upper()))
        self.bg_color = color
        self.text = text
        self.width = len(self.text) * self.font_size * 0.6 + 10
        self.height = self.font_size * 1.8

    def draw(self):
        self.canv.setFillColor(self.bg_color)
        self.canv.roundRect(0, 0, self.width, self.height, 3, fill=1, stroke=0)
        self.canv.setFillColor(white)
        self.canv.setFont("Helvetica-Bold", self.font_size)
        text_width = self.canv.stringWidth(self.text, "Helvetica-Bold", self.font_size)
        self.canv.drawString((self.width - text_width) / 2, (self.height - self.font_size) / 2, self.text)


class StatusBadge(Flowable):
    """A badge showing component status."""

    STATUS_COLORS = {
        "normal": ReportColors.STATUS_NORMAL,
        "attention_recommended": ReportColors.STATUS_ATTENTION,
        "critical_finding": ReportColors.STATUS_CRITICAL,
        "insufficient_data": ReportColors.STATUS_INSUFFICIENT,
        "not_evaluated": ReportColors.TEXT_SECONDARY,
    }

    def __init__(self, status: str, font_size=7):
        Flowable.__init__(self)
        self.status = status.lower()
        self.font_size = font_size
        self.bg_color = self.STATUS_COLORS.get(self.status, ReportColors.TEXT_SECONDARY)
        self.text = status.replace("_", " ").title()
        self.width = len(self.text) * self.font_size * 0.6 + 10
        self.height = self.font_size * 1.8

    def draw(self):
        self.canv.setFillColor(self.bg_color)
        self.canv.roundRect(0, 0, self.width, self.height, 3, fill=1, stroke=0)
        self.canv.setFillColor(white)
        self.canv.setFont("Helvetica-Bold", self.font_size)
        text_width = self.canv.stringWidth(self.text, "Helvetica-Bold", self.font_size)
        self.canv.drawString((self.width - text_width) / 2, (self.height - self.font_size) / 2, self.text)


# =============================================================================
# PDF RENDERER
# =============================================================================

class PDFRenderer:
    """
    Renders report data to professional PDF using ReportLab.

    Features:
    - Professional title page/header
    - Consistent styling with HTML reports
    - Proper page breaks and headers/footers
    - Page numbers
    - Tables with repeated headers
    - Unicode and INR currency support
    """

    def __init__(self):
        """Initialize the PDF renderer with styles."""
        self._setup_styles()
        self.page_width, self.page_height = A4
        self.margin = 2 * cm
        self.content_width = self.page_width - 2 * self.margin

    def _setup_styles(self):
        """Setup paragraph styles."""
        self.styles = getSampleStyleSheet()

        # Title style
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Title'],
            fontSize=22,
            leading=26,
            textColor=ReportColors.TEXT_PRIMARY,
            spaceAfter=6,
            fontName='Helvetica-Bold',
        ))

        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='ReportSubtitle',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=14,
            textColor=ReportColors.TEXT_SECONDARY,
            spaceAfter=16,
            fontName='Helvetica',
        ))

        # Section heading
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading1'],
            fontSize=14,
            leading=18,
            textColor=ReportColors.ACCENT_BLUE,
            spaceBefore=16,
            spaceAfter=10,
            fontName='Helvetica-Bold',
            borderWidth=0,
            borderPadding=0,
        ))

        # Sub-section heading
        self.styles.add(ParagraphStyle(
            name='SubSectionHeading',
            parent=self.styles['Heading2'],
            fontSize=11,
            leading=14,
            textColor=ReportColors.TEXT_PRIMARY,
            spaceBefore=10,
            spaceAfter=6,
            fontName='Helvetica-Bold',
        ))

        # Body text
        self.styles.add(ParagraphStyle(
            name='BodyText2',
            parent=self.styles['Normal'],
            fontSize=9,
            leading=12,
            textColor=ReportColors.TEXT_PRIMARY,
            spaceAfter=4,
            fontName='Helvetica',
        ))

        # Small text
        self.styles.add(ParagraphStyle(
            name='SmallText',
            parent=self.styles['Normal'],
            fontSize=8,
            leading=10,
            textColor=ReportColors.TEXT_SECONDARY,
            spaceAfter=2,
            fontName='Helvetica',
        ))

        # Bullet text
        self.styles.add(ParagraphStyle(
            name='BulletText',
            parent=self.styles['Normal'],
            fontSize=9,
            leading=12,
            textColor=ReportColors.TEXT_PRIMARY,
            spaceAfter=3,
            leftIndent=16,
            bulletIndent=4,
            fontName='Helvetica',
        ))

        # Footer
        self.styles.add(ParagraphStyle(
            name='FooterText',
            parent=self.styles['Normal'],
            fontSize=7,
            leading=9,
            textColor=ReportColors.TEXT_SECONDARY,
            alignment=TA_CENTER,
            fontName='Helvetica',
        ))

        # Table header
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            parent=self.styles['Normal'],
            fontSize=8,
            leading=10,
            textColor=ReportColors.TEXT_SECONDARY,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
        ))

        # Table cell
        self.styles.add(ParagraphStyle(
            name='TableCell',
            parent=self.styles['Normal'],
            fontSize=8,
            leading=10,
            textColor=ReportColors.TEXT_PRIMARY,
            fontName='Helvetica',
            alignment=TA_LEFT,
        ))

        # Table cell center
        self.styles.add(ParagraphStyle(
            name='TableCellCenter',
            parent=self.styles['TableCell'],
            alignment=TA_CENTER,
        ))

        # Meta label
        self.styles.add(ParagraphStyle(
            name='MetaLabel',
            parent=self.styles['Normal'],
            fontSize=7,
            leading=9,
            textColor=ReportColors.TEXT_SECONDARY,
            fontName='Helvetica-Bold',
        ))

        # Meta value
        self.styles.add(ParagraphStyle(
            name='MetaValue',
            parent=self.styles['Normal'],
            fontSize=9,
            leading=11,
            textColor=ReportColors.TEXT_PRIMARY,
            fontName='Helvetica',
        ))

    def _create_doc_template(self, output_path: Path) -> BaseDocTemplate:
        """Create document template with page templates."""
        doc = BaseDocTemplate(
            str(output_path),
            pagesize=A4,
            leftMargin=self.margin,
            rightMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin,
            title="i20 AI Garage Report",
            author="i20 AI Garage",
        )

        # Define frame for content
        frame = Frame(
            self.margin, self.margin,
            self.content_width, self.page_height - 2 * self.margin,
            id='main'
        )

        # Page template with header/footer
        def header_footer(canvas, doc):
            canvas.saveState()

            # Header line
            canvas.setStrokeColor(ReportColors.ACCENT_BLUE)
            canvas.setLineWidth(1.5)
            canvas.line(self.margin, self.page_height - self.margin + 10,
                       self.page_width - self.margin, self.page_height - self.margin + 10)

            # Footer
            canvas.setFont('Helvetica', 7)
            canvas.setFillColor(ReportColors.TEXT_SECONDARY)
            canvas.drawCentredString(
                self.page_width / 2, self.margin - 10,
                f"i20 AI Garage - Hyundai i20 Asta 2023 - Page {doc.page}"
            )

            canvas.restoreState()

        template = PageTemplate(id='main', frames=[frame], onPage=header_footer)
        doc.addPageTemplates([template])

        return doc

    def _header_row(self, label: str, value: str) -> List:
        """Create a key-value row for metadata tables."""
        return [
            Paragraph(label, self.styles['MetaLabel']),
            Paragraph(value, self.styles['MetaValue']),
        ]

    def _kv_table(self, pairs: List[tuple], col_widths=None) -> Table:
        """Create a key-value table."""
        if col_widths is None:
            col_widths = [self.content_width * 0.3, self.content_width * 0.7]

        data = [[Paragraph(k, self.styles['MetaLabel']), Paragraph(v, self.styles['MetaValue'])] for k, v in pairs]
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        return table

    def _data_table(self, headers: List[str], rows: List[List], col_widths=None) -> Table:
        """Create a styled data table."""
        # Convert headers to paragraphs
        header_row = [Paragraph(h, self.styles['TableHeader']) for h in headers]

        # Convert rows to paragraphs
        data = [header_row]
        for row in rows:
            data.append([Paragraph(str(cell), self.styles['TableCell']) for cell in row])

        if col_widths is None:
            col_widths = [self.content_width / len(headers)] * len(headers)

        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), ReportColors.BG_SECONDARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), ReportColors.TEXT_SECONDARY),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),

            # Body
            ('BACKGROUND', (0, 1), (-1, -1), ReportColors.BG_CARD),
            ('TEXTCOLOR', (0, 1), (-1, -1), ReportColors.TEXT_PRIMARY),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),

            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, ReportColors.BORDER),
            ('LINEBELOW', (0, 0), (-1, 0), 1.5, ReportColors.ACCENT_BLUE),

            # Alternating rows
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [ReportColors.BG_CARD, ReportColors.BG_SECONDARY]),
        ]))
        return table

    def _format_currency(self, value: Optional[float]) -> str:
        """Format currency in INR."""
        if value is None:
            return "—"
        return f"₹{value:,.2f}"

    def _format_datetime(self, value: Union[str, datetime, None]) -> str:
        """Format datetime for display."""
        if value is None:
            return "—"
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                return value
        return value.strftime('%Y-%m-%d %H:%M:%S')

    def _format_date(self, value: Union[str, datetime, None]) -> str:
        """Format date for display."""
        if value is None:
            return "—"
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                return value
        return value.strftime('%Y-%m-%d')

    def _severity_badge_cell(self, severity: str):
        """Create a table cell with severity badge."""
        return SeverityBadge(severity)

    def _source_badge_cell(self, source: str):
        """Create a table cell with data source badge."""
        return DataSourceBadge(source)

    def _status_badge_cell(self, status: str):
        """Create a table cell with status badge."""
        return StatusBadge(status)

    def _build_story(self, report_data: ReportDataUnion) -> List:
        """Build the story (content) for the PDF."""
        story = []

        # Title page / header
        story.append(Paragraph(self._get_report_title(report_data.metadata.report_type), self.styles['ReportTitle']))
        story.append(Paragraph("i20 AI Garage - Professional Automotive Report", self.styles['ReportSubtitle']))

        # Metadata table
        meta_pairs = [
            ("Report ID", report_data.metadata.report_id),
            ("Generated", self._format_datetime(report_data.metadata.generated_at)),
            ("Format", report_data.metadata.format.value.upper()),
            ("Data Source", report_data.metadata.data_source.value.upper()),
        ]
        story.append(self._kv_table(meta_pairs))
        story.append(Spacer(1, 12))

        # Vehicle info
        story.append(Paragraph("Vehicle Information", self.styles['SectionHeading']))
        vi = report_data.vehicle_info
        vi_pairs = [
            ("Make / Model", f"{vi.make} {vi.model}"),
            ("Year", str(vi.year)),
            ("Engine", vi.engine),
            ("Transmission", vi.transmission),
            ("Fuel Type", vi.fuel_type),
            ("Market", vi.market),
            ("ECU Tuning", vi.ecu_tuning),
            ("Diagnostic Mode", vi.diagnostic_mode),
        ]
        if vi.vin:
            vi_pairs.append(("VIN", vi.vin))
        if vi.odometer_km:
            vi_pairs.append(("Odometer", f"{vi.odometer_km} km"))
        story.append(self._kv_table(vi_pairs))
        story.append(Spacer(1, 16))

        # Report-specific content
        if isinstance(report_data, DiagnosticReportData):
            story.extend(self._build_diagnostic_content(report_data))
        elif isinstance(report_data, VehicleHealthReportData):
            story.extend(self._build_vehicle_health_content(report_data))
        elif isinstance(report_data, PerformanceReportData):
            story.extend(self._build_performance_content(report_data))
        elif isinstance(report_data, MaintenanceReportData):
            story.extend(self._build_maintenance_content(report_data))

        # Data provenance
        if report_data.data_provenance:
            story.append(Spacer(1, 16))
            story.append(Paragraph("Data Provenance", self.styles['SectionHeading']))
            for prov in report_data.data_provenance:
                prov_text = f"<b>{prov.description}</b> — Source: {prov.source.value.upper()}"
                if prov.session_id:
                    prov_text += f" | Session: {prov.session_id}"
                if prov.diagnosis_id:
                    prov_text += f" | Diagnosis: {prov.diagnosis_id}"
                if prov.evaluation_id:
                    prov_text += f" | Evaluation: {prov.evaluation_id}"
                if prov.record_count:
                    prov_text += f" | Records: {prov.record_count}"
                story.append(Paragraph(prov_text, self.styles['BodyText2']))

        # Limitations
        if report_data.metadata.report_type == ReportType.DIAGNOSTIC and hasattr(report_data, 'limitations') and report_data.limitations:
            story.append(Spacer(1, 16))
            story.append(Paragraph("Report Limitations", self.styles['SectionHeading']))
            for lim in report_data.limitations:
                story.append(Paragraph(f"• {lim}", self.styles['BulletText']))

        return story

    def _get_report_title(self, report_type: ReportType) -> str:
        """Get display title for report type."""
        titles = {
            ReportType.DIAGNOSTIC: "Comprehensive Diagnostic Report",
            ReportType.VEHICLE_HEALTH: "Vehicle Health Report",
            ReportType.PERFORMANCE: "Performance Report",
            ReportType.MAINTENANCE: "Maintenance Report",
        }
        return titles.get(report_type, "Report")

    def _build_diagnostic_content(self, report_data: DiagnosticReportData) -> List:
        """Build diagnostic report content."""
        story = []

        # Diagnostic Session Info
        if report_data.diagnostic_session:
            story.append(Paragraph("Diagnostic Session Information", self.styles['SectionHeading']))
            ds = report_data.diagnostic_session
            pairs = []
            if ds.get('session_id'):
                pairs.append(("Session ID", ds['session_id']))
            if ds.get('diagnosis_id'):
                pairs.append(("Diagnosis ID", ds['diagnosis_id']))
            pairs.append(("Data Source", ds.get('data_source', 'unknown').upper()))
            pairs.append(("Operating Mode", ds.get('operating_mode', 'unknown')))
            pairs.append(("Available Sensors", str(ds.get('available_sensor_count', 0))))
            pairs.append(("Available DTCs", str(ds.get('available_dtc_count', 0))))
            if ds.get('diagnosis_timestamp'):
                pairs.append(("Diagnosis Time", self._format_datetime(ds['diagnosis_timestamp'])))
            if ds.get('telemetry_record_count'):
                pairs.append(("Telemetry Records", str(ds['telemetry_record_count'])))
            story.append(self._kv_table(pairs))
            story.append(Spacer(1, 10))

        # DTCs
        if report_data.dtcs:
            story.append(Paragraph("DTC Scan Results", self.styles['SectionHeading']))
            headers = ["Code", "Description", "Severity", "Status", "Source"]
            rows = []
            for dtc in report_data.dtcs:
                rows.append([
                    dtc.code,
                    dtc.description,
                    SeverityBadge(dtc.severity.value),
                    dtc.status,
                    DataSourceBadge(dtc.data_source.value),
                ])
            story.append(self._data_table(headers, rows))
            story.append(Spacer(1, 10))

        # AI Diagnosis
        if report_data.ai_diagnosis:
            story.append(Paragraph("AI Diagnostic Findings", self.styles['SectionHeading']))
            ai = report_data.ai_diagnosis

            pairs = [
                ("Diagnosis ID", ai.diagnosis_id),
                ("Timestamp", self._format_datetime(ai.timestamp)),
                ("Confidence", f"{ai.confidence:.0%}"),
                ("Severity", ai.severity.value.upper()),
                ("Data Quality", ai.data_quality),
                ("Source", ai.data_source.value.upper()),
            ]
            story.append(self._kv_table(pairs))

            if ai.summary:
                story.append(Spacer(1, 6))
                story.append(Paragraph("<b>Summary:</b>", self.styles['BodyText2']))
                story.append(Paragraph(ai.summary, self.styles['BodyText2']))

            if ai.primary_diagnosis:
                story.append(Spacer(1, 8))
                story.append(Paragraph("Primary Diagnosis", self.styles['SubSectionHeading']))
                pd = ai.primary_diagnosis
                story.append(Paragraph(f"<b>{pd['code']}</b> - {pd['description']}", self.styles['BodyText2']))
                story.append(Paragraph(f"Confidence: {pd['confidence']:.0%} | Severity: {pd['severity'].upper()}", self.styles['SmallText']))

                if pd.get('probable_causes'):
                    story.append(Spacer(1, 4))
                    story.append(Paragraph("<b>Probable Causes:</b>", self.styles['BodyText2']))
                    for cause in pd['probable_causes']:
                        cause_text = f"• {cause['cause']} ({cause['confidence']:.0%} confidence, {cause['urgency']})"
                        story.append(Paragraph(cause_text, self.styles['BulletText']))
                        story.append(Paragraph(f"  {cause['explanation']}", self.styles['SmallText']))
                        if cause.get('verification_steps'):
                            story.append(Paragraph(f"  Verification: {', '.join(cause['verification_steps'])}", self.styles['SmallText']))

            if ai.safety_warnings:
                story.append(Spacer(1, 8))
                story.append(Paragraph("<b>Safety Warnings:</b>", self.styles['BodyText2']))
                for warning in ai.safety_warnings:
                    story.append(Paragraph(f"⚠ {warning}", self.styles['BulletText']))

            if ai.estimated_cost_inr:
                story.append(Spacer(1, 8))
                story.append(Paragraph(f"<b>Estimated Repair Cost: {ai.estimated_cost_inr}</b>", self.styles['BodyText2']))
                story.append(Paragraph("<i>Estimate only - not a verified quotation</i>", self.styles['SmallText']))

            story.append(Spacer(1, 10))

        # Rule Findings
        if report_data.rule_findings:
            story.append(Paragraph("Deterministic Rule Engine Findings", self.styles['SectionHeading']))
            headers = ["Rule ID", "Name", "Category", "Severity", "Confidence", "Source"]
            rows = []
            for finding in report_data.rule_findings:
                rows.append([
                    finding.rule_id,
                    finding.rule_name,
                    finding.category,
                    SeverityBadge(finding.severity.value),
                    f"{finding.confidence:.0%}",
                    DataSourceBadge(finding.data_source.value),
                ])
            story.append(self._data_table(headers, rows))

            # Details
            for finding in report_data.rule_findings:
                story.append(Spacer(1, 8))
                story.append(Paragraph(f"{finding.rule_id} - {finding.rule_name}", self.styles['SubSectionHeading']))
                story.append(Paragraph(finding.explanation, self.styles['BodyText2']))
                if finding.evidence:
                    story.append(Paragraph("<b>Evidence:</b>", self.styles['BodyText2']))
                    for ev in finding.evidence:
                        story.append(Paragraph(f"• {ev}", self.styles['BulletText']))
                if finding.recommended_checks:
                    story.append(Paragraph("<b>Recommended Checks:</b>", self.styles['BodyText2']))
                    for check in finding.recommended_checks:
                        story.append(Paragraph(f"• {check}", self.styles['BulletText']))
                if finding.recommended_actions:
                    story.append(Paragraph("<b>Recommended Actions:</b>", self.styles['BodyText2']))
                    for action in finding.recommended_actions:
                        story.append(Paragraph(f"• {action}", self.styles['BulletText']))
                if finding.safety_notes:
                    story.append(Paragraph("<b>Safety Notes:</b>", self.styles['BodyText2']))
                    for note in finding.safety_notes:
                        story.append(Paragraph(f"⚠ {note}", self.styles['BulletText']))

            story.append(Spacer(1, 10))

        # Telemetry Summary
        if report_data.telemetry_summary:
            story.append(Paragraph("Telemetry Summary", self.styles['SectionHeading']))
            ts = report_data.telemetry_summary
            pairs = []
            if ts.rpm is not None:
                pairs.append(("Engine RPM", f"{ts.rpm:.0f} RPM"))
            if ts.speed_kmh is not None:
                pairs.append(("Vehicle Speed", f"{ts.speed_kmh:.1f} km/h"))
            if ts.coolant_temp_c is not None:
                pairs.append(("Coolant Temperature", f"{ts.coolant_temp_c:.1f} °C"))
            if ts.throttle_pos_pct is not None:
                pairs.append(("Throttle Position", f"{ts.throttle_pos_pct:.1f}%"))
            if ts.engine_load_pct is not None:
                pairs.append(("Engine Load", f"{ts.engine_load_pct:.1f}%"))
            if ts.stft_b1_pct is not None:
                pairs.append(("STFT (B1)", f"{ts.stft_b1_pct:.1f}%"))
            if ts.ltft_b1_pct is not None:
                pairs.append(("LTFT (B1)", f"{ts.ltft_b1_pct:.1f}%"))
            if ts.voltage_v is not None:
                pairs.append(("Battery Voltage", f"{ts.voltage_v:.2f} V"))
            if ts.maf_g_s is not None:
                pairs.append(("MAF", f"{ts.maf_g_s:.1f} g/s"))
            if ts.map_kpa is not None:
                pairs.append(("MAP", f"{ts.map_kpa:.1f} kPa"))
            pairs.append(("Data Source", ts.data_source.value.upper()))
            pairs.append(("Records", str(ts.record_count)))
            if ts.timestamp:
                pairs.append(("Last Update", self._format_datetime(ts.timestamp)))
            story.append(self._kv_table(pairs))
            story.append(Spacer(1, 10))

        # Recommendations
        if report_data.recommendations:
            story.append(Paragraph("Recommendations", self.styles['SectionHeading']))

            if report_data.recommendations.get('immediate_attention'):
                story.append(Paragraph("<b>Immediate Attention:</b>", self.styles['BodyText2']))
                for rec in report_data.recommendations['immediate_attention']:
                    story.append(Paragraph(f"🔴 {rec}", self.styles['BulletText']))

            if report_data.recommendations.get('further_verification'):
                story.append(Paragraph("<b>Further Verification:</b>", self.styles['BodyText2']))
                for rec in report_data.recommendations['further_verification']:
                    story.append(Paragraph(f"🟡 {rec}", self.styles['BulletText']))

            if report_data.recommendations.get('routine_maintenance'):
                story.append(Paragraph("<b>Routine Maintenance:</b>", self.styles['BodyText2']))
                for rec in report_data.recommendations['routine_maintenance']:
                    story.append(Paragraph(f"🔵 {rec}", self.styles['BulletText']))

            if report_data.recommendations.get('monitoring'):
                story.append(Paragraph("<b>Monitoring:</b>", self.styles['BodyText2']))
                for rec in report_data.recommendations['monitoring']:
                    story.append(Paragraph(f"⚪ {rec}", self.styles['BulletText']))

        return story

    def _build_vehicle_health_content(self, report_data: VehicleHealthReportData) -> List:
        """Build vehicle health report content."""
        story = []

        # Overall Conclusion
        story.append(Paragraph("Overall Assessment", self.styles['SectionHeading']))
        story.append(Paragraph(report_data.overall_conclusion, self.styles['BodyText2']))
        story.append(Spacer(1, 10))

        # Latest Diagnostic Summary
        if report_data.latest_diagnostic_summary:
            story.append(Paragraph("Latest Diagnostic Scan", self.styles['SectionHeading']))
            lds = report_data.latest_diagnostic_summary
            pairs = [
                ("Scan Time", self._format_datetime(lds.get('scan_time'))),
                ("DTC Count", str(lds.get('dtc_count', 0))),
                ("Type", "Simulation" if lds.get('is_demo') else "Real"),
            ]
            story.append(self._kv_table(pairs))
            if lds.get('summary'):
                story.append(Spacer(1, 6))
                story.append(Paragraph(lds['summary'], self.styles['BodyText2']))
            story.append(Spacer(1, 10))

        # Current DTCs
        if report_data.current_dtc_summary:
            story.append(Paragraph("Current DTC Status", self.styles['SectionHeading']))
            headers = ["Code", "Description", "Severity", "Source"]
            rows = [[dtc.code, dtc.description, SeverityBadge(dtc.severity.value), DataSourceBadge(dtc.data_source.value)] for dtc in report_data.current_dtc_summary]
            story.append(self._data_table(headers, rows))
            story.append(Spacer(1, 10))
        else:
            story.append(Paragraph("Current DTC Status", self.styles['SectionHeading']))
            story.append(Paragraph("No active DTCs detected.", self.styles['BodyText2']))
            story.append(Spacer(1, 10))

        # Rule Findings
        if report_data.latest_rule_findings:
            story.append(Paragraph("Latest Rule Engine Findings", self.styles['SectionHeading']))
            headers = ["Rule ID", "Name", "Category", "Severity", "Confidence"]
            rows = [[f.rule_id, f.rule_name, f.category, SeverityBadge(f.severity.value), f"{f.confidence:.0%}"] for f in report_data.latest_rule_findings]
            story.append(self._data_table(headers, rows))
            story.append(Spacer(1, 10))

        # AI Diagnosis
        if report_data.latest_ai_diagnosis:
            story.append(Paragraph("Latest AI Diagnosis", self.styles['SectionHeading']))
            ai = report_data.latest_ai_diagnosis
            pairs = [
                ("Diagnosis ID", ai.diagnosis_id),
                ("Timestamp", self._format_datetime(ai.timestamp)),
                ("Confidence", f"{ai.confidence:.0%}"),
                ("Severity", ai.severity.value.upper()),
                ("Data Quality", ai.data_quality),
                ("Source", ai.data_source.value.upper()),
            ]
            story.append(self._kv_table(pairs))
            if ai.summary:
                story.append(Spacer(1, 6))
                story.append(Paragraph(ai.summary, self.styles['BodyText2']))
            if ai.estimated_cost_inr:
                story.append(Spacer(1, 6))
                story.append(Paragraph(f"<b>Estimated Repair Cost: {ai.estimated_cost_inr}</b>", self.styles['BodyText2']))
                story.append(Paragraph("<i>Estimate only - not a verified quotation</i>", self.styles['SmallText']))
            story.append(Spacer(1, 10))

        # Sensor Availability
        story.append(Paragraph("Sensor Availability", self.styles['SectionHeading']))
        headers = ["Sensor", "Status"]
        rows = [[sensor, "Available" if available else "Unavailable"] for sensor, available in report_data.sensor_availability.items()]
        story.append(self._data_table(headers, rows))
        story.append(Spacer(1, 10))

        # Telemetry Summary
        if report_data.telemetry_summary:
            story.append(Paragraph("Current Telemetry Snapshot", self.styles['SectionHeading']))
            ts = report_data.telemetry_summary
            pairs = []
            if ts.rpm is not None:
                pairs.append(("Engine RPM", f"{ts.rpm:.0f} RPM"))
            if ts.speed_kmh is not None:
                pairs.append(("Vehicle Speed", f"{ts.speed_kmh:.1f} km/h"))
            if ts.coolant_temp_c is not None:
                pairs.append(("Coolant Temperature", f"{ts.coolant_temp_c:.1f} °C"))
            if ts.throttle_pos_pct is not None:
                pairs.append(("Throttle Position", f"{ts.throttle_pos_pct:.1f}%"))
            if ts.engine_load_pct is not None:
                pairs.append(("Engine Load", f"{ts.engine_load_pct:.1f}%"))
            if ts.stft_b1_pct is not None:
                pairs.append(("STFT (B1)", f"{ts.stft_b1_pct:.1f}%"))
            if ts.ltft_b1_pct is not None:
                pairs.append(("LTFT (B1)", f"{ts.ltft_b1_pct:.1f}%"))
            if ts.voltage_v is not None:
                pairs.append(("Battery Voltage", f"{ts.voltage_v:.2f} V"))
            pairs.append(("Data Source", ts.data_source.value.upper()))
            pairs.append(("Records", str(ts.record_count)))
            if ts.timestamp:
                pairs.append(("Last Update", self._format_datetime(ts.timestamp)))
            story.append(self._kv_table(pairs))
            story.append(Spacer(1, 10))

        # Component Statuses
        if report_data.component_statuses:
            story.append(Paragraph("Component Status Summary", self.styles['SectionHeading']))
            headers = ["Component", "Status", "Description", "Evidence"]
            rows = []
            for comp in report_data.component_statuses:
                rows.append([
                    comp.name,
                    StatusBadge(comp.status),
                    comp.description,
                    ", ".join(comp.evidence) if comp.evidence else "—",
                ])
            story.append(self._data_table(headers, rows))
            story.append(Spacer(1, 10))

        # Maintenance History
        if report_data.maintenance_history:
            story.append(Paragraph("Maintenance History", self.styles['SectionHeading']))
            headers = ["Date", "Service Type", "Description", "Odometer", "Cost (INR)"]
            rows = []
            for record in report_data.maintenance_history[:20]:
                rows.append([
                    record.get('service_date', '—'),
                    record.get('service_type', '—'),
                    record.get('description', '—') or '—',
                    f"{record.get('odometer_km', 0)} km",
                    self._format_currency(record.get('cost')),
                ])
            story.append(self._data_table(headers, rows))
            if len(report_data.maintenance_history) > 20:
                story.append(Paragraph(f"<i>Showing 20 of {len(report_data.maintenance_history)} records.</i>", self.styles['SmallText']))
            story.append(Spacer(1, 10))

        # Upcoming Maintenance
        if report_data.upcoming_maintenance:
            story.append(Paragraph("Upcoming Maintenance", self.styles['SectionHeading']))
            headers = ["Service Type", "Due Date", "Due Odometer", "Description"]
            rows = []
            for item in report_data.upcoming_maintenance:
                rows.append([
                    item.get('service_type', '—'),
                    item.get('next_service_date', '—') or '—',
                    f"{item.get('next_service_km', '—')} km" if item.get('next_service_km') else '—',
                    item.get('description', '—') or '—',
                ])
            story.append(self._data_table(headers, rows))
            story.append(Spacer(1, 10))

        # Overdue Maintenance
        if report_data.overdue_maintenance:
            story.append(Paragraph("Overdue Maintenance", self.styles['SectionHeading']))
            headers = ["Service Type", "Due Date", "Due Odometer", "Current Odometer", "Description"]
            rows = []
            for item in report_data.overdue_maintenance:
                rows.append([
                    item.get('service_type', '—'),
                    item.get('next_service_date', '—') or '—',
                    f"{item.get('next_service_km', '—')} km" if item.get('next_service_km') else '—',
                    f"{report_data.vehicle_info.odometer_km or 'Unknown'} km",
                    item.get('description', '—') or '—',
                ])
            story.append(self._data_table(headers, rows))
            story.append(Spacer(1, 10))

        # Safety Observations
        if report_data.safety_observations:
            story.append(Paragraph("Safety Observations", self.styles['SectionHeading']))
            for obs in report_data.safety_observations:
                story.append(Paragraph(f"⚠ {obs}", self.styles['BulletText']))

        return story

    def _build_performance_content(self, report_data: PerformanceReportData) -> List:
        """Build performance report content."""
        story = []

        # Session Summary
        s = report_data.session
        story.append(Paragraph("Session Summary", self.styles['SectionHeading']))
        pairs = [
            ("Session ID", str(s.session_id)),
            ("Session Name", s.session_name),
            ("Scenario", s.scenario),
            ("Start Time", self._format_datetime(s.start_time)),
        ]
        if s.end_time:
            pairs.append(("End Time", self._format_datetime(s.end_time)))
        if s.duration_seconds:
            pairs.append(("Duration", f"{s.duration_seconds/60:.1f} min ({s.duration_seconds:.0f} sec)"))
        pairs.append(("Records", str(s.record_count)))
        pairs.append(("Data Source", s.data_source.value.upper()))
        story.append(self._kv_table(pairs))
        story.append(Spacer(1, 10))

        # Key Metrics
        story.append(Paragraph("Key Performance Metrics", self.styles['SectionHeading']))
        pairs = []
        if s.peak_rpm is not None:
            pairs.append(("Peak RPM", f"{s.peak_rpm:.0f} RPM"))
        if s.max_speed_kmh is not None:
            pairs.append(("Max Speed", f"{s.max_speed_kmh:.1f} km/h"))
        if s.avg_speed_kmh is not None:
            pairs.append(("Avg Speed", f"{s.avg_speed_kmh:.1f} km/h"))
        if s.max_coolant_temp_c is not None:
            pairs.append(("Max Coolant Temp", f"{s.max_coolant_temp_c:.1f} °C"))
        if s.max_engine_load_pct is not None:
            pairs.append(("Max Engine Load", f"{s.max_engine_load_pct:.1f}%"))
        if s.total_distance_km is not None:
            pairs.append(("Distance", f"{s.total_distance_km:.2f} km"))
        if s.fuel_consumed_l is not None:
            pairs.append(("Fuel Consumed", f"{s.fuel_consumed_l:.2f} L"))

        if pairs:
            story.append(self._kv_table(pairs))
        else:
            story.append(Paragraph("<i>No key metrics available for this session.</i>", self.styles['SmallText']))
        story.append(Spacer(1, 10))

        # Sensor Statistics
        if report_data.sensor_statistics:
            story.append(Paragraph("Sensor Statistics", self.styles['SectionHeading']))
            headers = ["Sensor", "Unit", "Count", "Min", "Max", "Average", "Std Dev"]
            rows = []
            for stat in report_data.sensor_statistics:
                rows.append([
                    stat.sensor_name,
                    stat.unit,
                    str(stat.count),
                    f"{stat.min_value:.2f}" if stat.min_value is not None else "—",
                    f"{stat.max_value:.2f}" if stat.max_value is not None else "—",
                    f"{stat.avg_value:.2f}" if stat.avg_value is not None else "—",
                    f"{stat.std_dev:.2f}" if stat.std_dev is not None else "—",
                ])
            story.append(self._data_table(headers, rows))
            story.append(Spacer(1, 10))

        # Charts Data Availability
        if report_data.charts_data:
            story.append(Paragraph("Time-Series Data Availability", self.styles['SectionHeading']))
            headers = ["Sensor", "Data Points", "Time Range"]
            rows = []
            for sensor, data_points in report_data.charts_data.items():
                time_range = "—"
                if data_points:
                    time_range = f"{data_points[0].get('timestamp', '—')} to {data_points[-1].get('timestamp', '—')}"
                rows.append([sensor, str(len(data_points)), time_range])
            story.append(self._data_table(headers, rows))
            story.append(Spacer(1, 6))
            story.append(Paragraph(
                "<i>Note: Charts are rendered in the interactive HTML view. "
                "PDF reports include tabular summaries above. "
                "For full interactive charts, view the HTML report in a browser.</i>",
                self.styles['SmallText']
            ))

        return story

    def _build_maintenance_content(self, report_data: MaintenanceReportData) -> List:
        """Build maintenance report content."""
        story = []

        # Current Vehicle Status
        story.append(Paragraph("Current Vehicle Status", self.styles['SectionHeading']))
        pairs = []
        if report_data.odometer_km:
            pairs.append(("Current Odometer", f"{report_data.odometer_km} km"))
        elif report_data.vehicle_info.odometer_km:
            pairs.append(("Current Odometer", f"{report_data.vehicle_info.odometer_km} km"))
        else:
            pairs.append(("Current Odometer", "Unknown"))

        pairs.extend([
            ("Total Records", str(report_data.summary.total_records)),
            ("Total Cost", self._format_currency(report_data.summary.total_cost_inr)),
            ("Upcoming Items", str(report_data.summary.upcoming_count)),
            ("Overdue Items", str(report_data.summary.overdue_count)),
        ])
        if report_data.summary.last_service_date:
            pairs.append(("Last Service", report_data.summary.last_service_date))
        if report_data.summary.last_service_odometer:
            pairs.append(("Last Service Odometer", f"{report_data.summary.last_service_odometer} km"))
        story.append(self._kv_table(pairs))
        story.append(Spacer(1, 10))

        # Cost Summary by Category
        if report_data.summary.cost_by_category:
            story.append(Paragraph("Cost Summary by Category", self.styles['SectionHeading']))
            headers = ["Service Category", "Total Cost (INR)"]
            rows = [[cat, self._format_currency(cost)] for cat, cost in report_data.summary.cost_by_category.items()]
            story.append(self._data_table(headers, rows))
            story.append(Spacer(1, 10))

        # Overdue Maintenance
        if report_data.overdue_items:
            story.append(Paragraph("Overdue Maintenance", self.styles['SectionHeading']))
            headers = ["Service Type", "Last Service Date", "Last Odometer", "Due Date", "Due Odometer", "Description"]
            rows = []
            for item in report_data.overdue_items:
                rows.append([
                    item.service_type,
                    item.service_date,
                    f"{item.odometer_km} km",
                    item.next_service_date or "—",
                    f"{item.next_service_km} km" if item.next_service_km else "—",
                    item.description or "—",
                ])
            story.append(self._data_table(headers, rows))
            story.append(Spacer(1, 10))

        # Upcoming Maintenance
        if report_data.upcoming_items:
            story.append(Paragraph("Upcoming Maintenance", self.styles['SectionHeading']))
            headers = ["Service Type", "Last Service Date", "Last Odometer", "Due Date", "Due Odometer", "Description"]
            rows = []
            for item in report_data.upcoming_items:
                rows.append([
                    item.service_type,
                    item.service_date,
                    f"{item.odometer_km} km",
                    item.next_service_date or "—",
                    f"{item.next_service_km} km" if item.next_service_km else "—",
                    item.description or "—",
                ])
            story.append(self._data_table(headers, rows))
            story.append(Spacer(1, 10))

        # Complete History
        if report_data.maintenance_history:
            story.append(Paragraph("Complete Maintenance History", self.styles['SectionHeading']))
            headers = ["Date", "Service Type", "Description", "Odometer", "Cost (INR)", "Next Due Date", "Next Due Odometer"]
            rows = []
            for record in report_data.maintenance_history:
                rows.append([
                    record.service_date,
                    record.service_type,
                    record.description or "—",
                    f"{record.odometer_km} km",
                    self._format_currency(record.cost),
                    record.next_service_date or "—",
                    f"{record.next_service_km} km" if record.next_service_km else "—",
                ])
            story.append(self._data_table(headers, rows))
            story.append(Spacer(1, 10))

        # Manufacturer Intervals Reference
        story.append(Paragraph("Manufacturer Recommended Intervals (Reference)", self.styles['SectionHeading']))
        story.append(Paragraph(
            "Standard intervals for Hyundai i20 Asta 2023 1.2L Petrol (India market)",
            self.styles['SmallText']
        ))
        headers = ["Service Item", "Interval", "Description"]
        intervals = [
            ("Engine Oil Change", "10,000 km", "Engine Oil Change"),
            ("Oil Filter Replacement", "10,000 km", "Oil Filter Replacement"),
            ("Air Filter Replacement", "20,000 km", "Air Filter Replacement"),
            ("Cabin Air Filter", "15,000 km", "Cabin Air Filter Replacement"),
            ("Spark Plug Replacement", "40,000 km", "Spark Plug Replacement"),
            ("Coolant Replacement", "60,000 km", "Coolant Replacement"),
            ("Brake Fluid Replacement", "40,000 km", "Brake Fluid Replacement"),
            ("Manual Transmission Oil", "60,000 km", "Manual Transmission Oil"),
            ("Front Brake Pads Inspection", "30,000 km", "Front Brake Pads Inspection"),
            ("Rear Brake Pads Inspection", "40,000 km", "Rear Brake Pads Inspection"),
            ("Tyre Rotation", "10,000 km", "Tyre Rotation"),
            ("Battery Health Check", "40,000 km", "Battery Health Check"),
        ]
        rows = [[item, interval, desc] for item, interval, desc in intervals]
        story.append(self._data_table(headers, rows))
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            "<i>Note: Intervals are manufacturer recommendations for normal driving conditions. "
            "Severe conditions (dust, extreme temperatures, short trips) may require more frequent service. "
            "Always refer to your vehicle's owner's manual for authoritative service schedules.</i>",
            self.styles['SmallText']
        ))

        return story

    def render_report(self, report_data: ReportDataUnion, output_path: Path) -> bool:
        """
        Render report to PDF file.

        Args:
            report_data: The report data model
            output_path: Path to save PDF file

        Returns:
            True if successful
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            doc = self._create_doc_template(output_path)
            story = self._build_story(report_data)
            doc.build(story)
            return True
        except Exception as e:
            print(f"Error generating PDF: {e}")
            import traceback
            traceback.print_exc()
            return False

    def render_report_bytes(self, report_data: ReportDataUnion) -> bytes:
        """
        Render report to PDF bytes.

        Args:
            report_data: The report data model

        Returns:
            PDF bytes
        """
        buffer = io.BytesIO()
        doc = BaseDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=self.margin,
            rightMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin,
        )

        frame = Frame(
            self.margin, self.margin,
            self.content_width, self.page_height - 2 * self.margin,
            id='main'
        )

        def header_footer(canvas, doc):
            canvas.saveState()
            canvas.setStrokeColor(ReportColors.ACCENT_BLUE)
            canvas.setLineWidth(1.5)
            canvas.line(self.margin, self.page_height - self.margin + 10,
                       self.page_width - self.margin, self.page_height - self.margin + 10)
            canvas.setFont('Helvetica', 7)
            canvas.setFillColor(ReportColors.TEXT_SECONDARY)
            canvas.drawCentredString(
                self.page_width / 2, self.margin - 10,
                f"i20 AI Garage - Hyundai i20 Asta 2023 - Page {doc.page}"
            )
            canvas.restoreState()

        template = PageTemplate(id='main', frames=[frame], onPage=header_footer)
        doc.addPageTemplates([template])

        story = self._build_story(report_data)
        doc.build(story)

        buffer.seek(0)
        return buffer.read()


# Convenience functions
def render_diagnostic_report_pdf(report_data: DiagnosticReportData, output_path: Path) -> bool:
    """Render diagnostic report to PDF file."""
    renderer = PDFRenderer()
    return renderer.render_report(report_data, output_path)


def render_vehicle_health_report_pdf(report_data: VehicleHealthReportData, output_path: Path) -> bool:
    """Render vehicle health report to PDF file."""
    renderer = PDFRenderer()
    return renderer.render_report(report_data, output_path)


def render_performance_report_pdf(report_data: PerformanceReportData, output_path: Path) -> bool:
    """Render performance report to PDF file."""
    renderer = PDFRenderer()
    return renderer.render_report(report_data, output_path)


def render_maintenance_report_pdf(report_data: MaintenanceReportData, output_path: Path) -> bool:
    """Render maintenance report to PDF file."""
    renderer = PDFRenderer()
    return renderer.render_report(report_data, output_path)
"""
i20 AI Garage - Diagnostics Module (Stage 5.3 Redesign)

Professional diagnostic interface with DTC scanning, detailed code information,
diagnostic report generation, AI-powered diagnosis, deterministic rule evaluation,
and history — all using the Stage 3 design system.
FULLY RESPONSIVE: mobile-first fluid grid, auto-fit cards, responsive tables.
"""

import streamlit as st
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from config import THEME, DTC_SEVERITY, DEMO_DTCS
from services import get_obd_service, get_database, get_diagnostic_engine, get_ai_service
from services.obd_service import DTC as OBDDTC
from services.diagnostic_models import DiagnosticResult, DiagnosticSeverity, DiagnosticStatus, DataSource

# Rule Engine imports (Phase 3)
try:
    from services import get_rule_engine
    from services.types import DTC
    from services.rule_models import RuleSeverity, RuleStatus, DataSource as RuleDataSource
    from services.rule_evaluator import SensorReading
    RULE_ENGINE_AVAILABLE = True
except ImportError:
    RULE_ENGINE_AVAILABLE = False
    get_rule_engine = None
    DTC = None
    RuleSeverity = None
    RuleStatus = None
    RuleDataSource = None
    SensorReading = None

# Design System imports
from components.ui.components import (
    # Components
    button_primary, button_secondary, button_ghost, button_danger,
    badge, BadgeVariant,
    alert, AlertVariant,
    card_simple, CardProps, card,
    empty_state, EmptyStateProps,
    table, TableProps, TableColumn,
    spinner, skeleton,
    selectbox,
    section_header,
)
from components.ui.tokens import (
    # Tokens
    ACCENT_PRIMARY, ACCENT_SECONDARY,
    STATUS_SUCCESS, STATUS_WARNING, STATUS_CRITICAL, STATUS_INFO, STATUS_NEUTRAL,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_ON_ACCENT,
    SURFACE_PRIMARY, SURFACE_SECONDARY, SURFACE_ELEVATED,
    BORDER_DEFAULT, BORDER_SUBTLE,
    SPACE_1, SPACE_2, SPACE_3, SPACE_4, SPACE_5, SPACE_6,
    GAP_INLINE, GAP_FIELD,
    RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_PILL,
    SHADOW_SM, SHADOW_MD, SHADOW_LG,
    FONT_FAMILY_BASE, FONT_FAMILY_MONO,
    FONT_SIZE_H1, FONT_SIZE_H2, FONT_SIZE_H3, FONT_SIZE_H4,
    FONT_SIZE_BODY, FONT_SIZE_BODY_SM, FONT_SIZE_LABEL, FONT_SIZE_CAPTION,
    FONT_WEIGHT_LABEL, FONT_WEIGHT_BODY, FONT_WEIGHT_NUMERIC,
    LETTER_SPACING_LABEL, LETTER_SPACING_CAPTION,
)
from components.charts_v2 import (
    create_gauge, GaugeConfig,
    create_sparkline, SparklineConfig,
    create_line_chart, LineChartConfig, LineSeries,
    create_bar_chart, BarChartConfig, BarSeries,
    create_pie_chart, PieChartConfig,
    create_status_indicator,
    SERIES_PALETTE, CHART_GOOD, CHART_WARNING, CHART_SERIOUS, CHART_CRITICAL,
    I20_TEMPLATE,
)
from components.ui.layout import (
    grid_container, responsive_container,
    AUTO_FIT_CARD_CSS, AUTO_FIT_METRIC_CSS,
)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class DiagnosticCode:
    """Structured diagnostic trouble code with full details."""
    code: str
    description: str
    severity: str
    possible_causes: List[str]
    recommended_verification: List[str]
    is_demo: bool = True
    status: str = "active"  # active, pending, history
    freeze_frame: Optional[Dict[str, Any]] = None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_demo_dtcs() -> List[DiagnosticCode]:
    """Convert config DEMO_DTCS to DiagnosticCode objects."""
    dtcs = []
    for dtc_data in DEMO_DTCS:
        dtcs.append(DiagnosticCode(
            code=dtc_data["code"],
            description=dtc_data["description"],
            severity=dtc_data["severity"],
            possible_causes=dtc_data["possible_causes"],
            recommended_verification=dtc_data["recommended_verification"],
            is_demo=dtc_data.get("is_demo", True),
        ))
    return dtcs


def get_severity_info(severity: str) -> Dict[str, Any]:
    """Get severity display info from config."""
    return DTC_SEVERITY.get(severity, {
        "color": "#9b59b6",
        "label": "Unknown",
        "description": "Severity information not available"
    })


def get_severity_badge_variant(severity: str) -> BadgeVariant:
    """Map DTC severity to badge variant."""
    severity_lower = severity.lower()
    if severity_lower in ("critical", "serious"):
        return BadgeVariant.CRITICAL
    elif severity_lower in ("high", "major"):
        return BadgeVariant.WARNING
    elif severity_lower in ("medium", "moderate"):
        return BadgeVariant.INFO
    elif severity_lower in ("low", "minor"):
        return BadgeVariant.SUCCESS
    return BadgeVariant.NEUTRAL


def get_rule_severity_badge_variant(severity) -> BadgeVariant:
    """Map RuleSeverity to badge variant."""
    if severity == RuleSeverity.CRITICAL:
        return BadgeVariant.CRITICAL
    elif severity == RuleSeverity.HIGH:
        return BadgeVariant.WARNING
    elif severity == RuleSeverity.MEDIUM:
        return BadgeVariant.INFO
    elif severity in (RuleSeverity.LOW, RuleSeverity.INFORMATIONAL):
        return BadgeVariant.SUCCESS
    return BadgeVariant.NEUTRAL


def get_rule_status_badge_variant(status) -> BadgeVariant:
    """Map RuleStatus to badge variant."""
    if status == RuleStatus.TRIGGERED:
        return BadgeVariant.CRITICAL
    elif status == RuleStatus.NOT_TRIGGERED:
        return BadgeVariant.SUCCESS
    elif status == RuleStatus.SKIPPED:
        return BadgeVariant.WARNING
    elif status == RuleStatus.ERROR:
        return BadgeVariant.CRITICAL
    elif status == RuleStatus.INSUFFICIENT_DATA:
        return BadgeVariant.NEUTRAL
    return BadgeVariant.NEUTRAL


def get_diagnostic_severity_badge_variant(severity: DiagnosticSeverity) -> BadgeVariant:
    """Map DiagnosticSeverity to badge variant."""
    if severity == DiagnosticSeverity.CRITICAL:
        return BadgeVariant.CRITICAL
    elif severity == DiagnosticSeverity.MAJOR:
        return BadgeVariant.WARNING
    elif severity == DiagnosticSeverity.MINOR:
        return BadgeVariant.INFO
    elif severity == DiagnosticSeverity.INFO:
        return BadgeVariant.SUCCESS
    return BadgeVariant.NEUTRAL


def get_diagnostic_status_badge_variant(status: DiagnosticStatus) -> BadgeVariant:
    """Map DiagnosticStatus to badge variant."""
    if status == DiagnosticStatus.COMPLETE:
        return BadgeVariant.SUCCESS
    elif status == DiagnosticStatus.INCONCLUSIVE:
        return BadgeVariant.WARNING
    elif status == DiagnosticStatus.ERROR:
        return BadgeVariant.CRITICAL
    elif status == DiagnosticStatus.INSUFFICIENT_DATA:
        return BadgeVariant.NEUTRAL
    return BadgeVariant.NEUTRAL


def get_data_source_badge_variant(source) -> BadgeVariant:
    """Map DataSource to badge variant."""
    if hasattr(source, 'value'):
        source_val = source.value
    else:
        source_val = str(source).lower()

    if source_val == "real":
        return BadgeVariant.SUCCESS
    elif source_val == "simulation":
        return BadgeVariant.WARNING
    return BadgeVariant.INFO


# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

def init_diagnostics_session_state():
    """Initialize all diagnostics-specific session state keys."""
    defaults = {
        "scan_results": [],
        "scan_status": "idle",
        "selected_dtc": None,
        "last_scan_time": None,
        "scan_mode": "demo",
        "ai_diagnosis_result": None,
        "ai_diagnosis_status": "idle",
        "ai_diagnosis_time": None,
        "rule_evaluation_result": None,
        "rule_evaluation_status": "idle",
        "rule_evaluation_time": None,
    }

    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


# =============================================================================
# SCAN OPERATIONS
# =============================================================================

def perform_scan(obd):
    """Perform DTC scan using OBD service."""
    st.session_state.scan_status = "scanning"
    st.session_state.selected_dtc = None

    try:
        import time
        time.sleep(0.5)

        if obd.mode.value == "simulation":
            obd_dtcs = obd.scan_dtcs()
            results = []
            for dtc in obd_dtcs:
                demo_match = next((d for d in DEMO_DTCS if d["code"] == dtc.code), None)
                if demo_match:
                    results.append(DiagnosticCode(
                        code=dtc.code,
                        description=dtc.description,
                        severity=dtc.severity,
                        possible_causes=demo_match["possible_causes"],
                        recommended_verification=demo_match["recommended_verification"],
                        is_demo=True,
                        status=dtc.status,
                    ))
                else:
                    results.append(DiagnosticCode(
                        code=dtc.code,
                        description=dtc.description,
                        severity=dtc.severity,
                        possible_causes=[],
                        recommended_verification=[],
                        is_demo=dtc.is_demo,
                        status=dtc.status,
                    ))
            st.session_state.scan_results = results
        else:
            obd_dtcs = obd.scan_dtcs()
            results = []
            for dtc in obd_dtcs:
                results.append(DiagnosticCode(
                    code=dtc.code,
                    description=dtc.description,
                    severity=dtc.severity,
                    possible_causes=[],
                    recommended_verification=[],
                    is_demo=dtc.is_demo,
                    status=dtc.status,
                ))
            st.session_state.scan_results = results

        st.session_state.scan_status = "complete"
        st.session_state.last_scan_time = datetime.now()

    except Exception as e:
        st.session_state.scan_status = "error"
        st.error(f"Scan failed: {str(e)}")

    st.rerun()


def clear_scan_results():
    """Clear all scan results and reset state."""
    st.session_state.scan_results = []
    st.session_state.scan_status = "idle"
    st.session_state.selected_dtc = None
    st.session_state.last_scan_time = None
    st.rerun()


# =============================================================================
# REPORT GENERATION
# =============================================================================

def generate_report_text(obd) -> str:
    """Generate formatted diagnostic report text."""
    status = obd.get_status()
    vehicle = status.get("vehicle_info", {})

    lines = [
        "=" * 60,
        "i20 AI GARAGE - DIAGNOSTIC SCAN REPORT",
        "=" * 60,
        "",
        f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Scan Mode: {status['mode'].upper()}",
        f"Connection: {status['connection_state'].title()}",
        "",
        "VEHICLE INFORMATION",
        "-" * 60,
        f"Make/Model: Hyundai i20 Asta (2023)",
        f"Engine: 1.2L Naturally Aspirated Petrol",
        f"Transmission: Manual 5-speed",
        f"Fuel: Petrol (BS6)",
        f"Market: India",
        f"ECU Tuning: Stock",
        f"Diagnostic Mode: {status['mode'].title()}",
        "",
        "DIAGNOSTIC TROUBLE CODES",
        "-" * 60,
    ]

    if not st.session_state.scan_results:
        lines.append("No DTCs found.")
    else:
        for i, dtc in enumerate(st.session_state.scan_results, 1):
            severity_info = get_severity_info(dtc.severity)
            lines.extend([
                "",
                f"--- DTC #{i} ---",
                f"Code: {dtc.code}",
                f"Description: {dtc.description}",
                f"Severity: {severity_info['label']} ({severity_info['description']})",
                f"Status: {dtc.status.title()}",
                f"Mode: {'DEMO (Simulated)' if dtc.is_demo else 'Live'}",
                "",
                "Possible Causes:",
            ])
            for cause in dtc.possible_causes:
                lines.append(f"  • {cause}")

            lines.append("")
            lines.append("Recommended Verification:")
            for verify in dtc.recommended_verification:
                lines.append(f"  • {verify}")

    lines.extend([
        "",
        "=" * 60,
        "DISCLAIMER",
        "-" * 60,
        "This report is generated by i20 AI Garage diagnostic software.",
    ])

    if status['mode'] == 'simulation':
        lines.append("⚠ SIMULATION MODE: All DTCs are simulated for demonstration only.")
        lines.append("They do not represent actual vehicle faults.")
    else:
        lines.append("This report reflects DTCs read from the vehicle's ECU via OBD-II.")

    lines.extend([
        "",
        "This report is for informational purposes only and does not",
        "constitute a professional diagnosis. For repairs, consult a",
        "qualified automotive technician with proper diagnostic equipment.",
        "",
        "i20 AI Garage does not clear codes, execute ECU commands,",
        "or perform actuator tests through this interface.",
        "=" * 60,
    ])

    return "\n".join(lines)


def save_report(db, report_text: str):
    """Save diagnostic report to database."""
    try:
        active_session = db.get_active_session()
        session_id = active_session["id"] if active_session else None

        codes = []
        for dtc in st.session_state.scan_results:
            codes.append({
                "code": dtc.code,
                "description": dtc.description,
                "severity": dtc.severity,
                "status": dtc.status,
                "is_demo": dtc.is_demo,
                "possible_causes": dtc.possible_causes,
                "recommended_verification": dtc.recommended_verification,
            })

        summary = f"Scan completed - {len(codes)} DTC(s) found ({'DEMO' if all(c['is_demo'] for c in codes) else 'LIVE'})"

        report_id = db.save_diagnostic_report(
            session_id=session_id,
            dtc_count=len(codes),
            codes=codes,
            summary=summary,
            is_demo=all(c['is_demo'] for c in codes) if codes else True
        )

        st.success(f"Diagnostic report saved (ID: {report_id})")
    except Exception as e:
        st.error(f"Failed to save report: {str(e)}")


# =============================================================================
# RULE ENGINE OPERATIONS
# =============================================================================

def run_rule_evaluation(obd, db):
    """Run deterministic rule evaluation."""
    st.session_state.rule_evaluation_status = "running"
    st.session_state.rule_evaluation_result = None

    try:
        engine = get_rule_engine()

        readings_dict = obd.get_all_readings()
        current_readings = {}
        for key, reading in readings_dict.items():
            current_readings[key] = SensorReading(
                pid=reading.pid,
                name=reading.name,
                value=reading.value,
                unit=reading.unit,
                timestamp=reading.timestamp,
                is_simulated=reading.is_simulated
            )

        engine.add_sensor_readings(list(current_readings.values()))

        active_dtcs = []
        for dtc in st.session_state.scan_results:
            active_dtcs.append(DTC(
                code=dtc.code,
                description=dtc.description,
                severity=dtc.severity,
                status=dtc.status,
                is_demo=dtc.is_demo
            ))

        result = engine.evaluate(
            current_readings=current_readings,
            active_dtcs=active_dtcs if active_dtcs else None,
            diagnostic_session_id=db.get_active_session().get("id") if db.get_active_session() else None
        )

        st.session_state.rule_evaluation_result = result
        st.session_state.rule_evaluation_status = "complete"
        st.session_state.rule_evaluation_time = datetime.now()

        st.success(f"Rule evaluation completed! {len(result.findings)} finding(s) found.")

    except Exception as e:
        st.session_state.rule_evaluation_status = "error"
        st.error(f"Rule evaluation failed: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

    st.rerun()


def clear_rule_evaluation():
    """Clear rule evaluation results."""
    st.session_state.rule_evaluation_result = None
    st.session_state.rule_evaluation_status = "idle"
    st.session_state.rule_evaluation_time = None
    st.rerun()


# =============================================================================
# AI DIAGNOSIS OPERATIONS
# =============================================================================

def run_ai_diagnosis(obd, db):
    """Run AI diagnosis using the diagnostic engine."""
    st.session_state.ai_diagnosis_status = "running"
    st.session_state.ai_diagnosis_result = None

    try:
        engine = get_diagnostic_engine()
        result = engine.run_diagnosis()

        st.session_state.ai_diagnosis_result = result
        st.session_state.ai_diagnosis_status = "complete"
        st.session_state.ai_diagnosis_time = datetime.now()

        st.success("AI diagnosis completed!")

    except Exception as e:
        st.session_state.ai_diagnosis_status = "error"
        st.error(f"AI diagnosis failed: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

    st.rerun()


def clear_ai_diagnosis():
    """Clear AI diagnosis results."""
    st.session_state.ai_diagnosis_result = None
    st.session_state.ai_diagnosis_status = "idle"
    st.session_state.ai_diagnosis_time = None
    st.rerun()


# =============================================================================
# RESPONSIVE UI COMPONENTS
# =============================================================================

def _render_responsive_card_grid(items_html: List[str], min_width: str = "320px") -> str:
    """Render a responsive auto-fit card grid."""
    return grid_container(items_html, grid_type="auto-fit")


def _render_responsive_button_row(buttons: List[Dict[str, Any]], gap: str = "var(--i20-gap-field)") -> str:
    """Render a responsive button row that stacks on mobile."""
    button_html = ""
    for btn in buttons:
        disabled_attr = ' disabled' if btn.get('disabled') else ''
        variant_class = btn.get('variant', 'secondary')
        button_html += f"""
        <button class="i20-btn i20-btn-{variant_class} i20-responsive-btn"
                style="flex: 1 1 140px; min-width: 140px; padding: var(--i20-spacing-sm) var(--i20-spacing-md);"
                {disabled_attr}
                data-action="{btn.get('action', '')}"
                data-key="{btn.get('key', '')}">
            {btn['label']}
        </button>
        """

    return f"""
    <div class="i20-btn-group" style="display: flex; flex-wrap: wrap; gap: {gap};">
        {button_html}
    </div>
    """


# =============================================================================
# UI COMPONENTS - SCAN PANEL (RESPONSIVE)
# =============================================================================

def render_scan_panel(obd):
    """Render the DTC scan control panel using design system components - RESPONSIVE."""
    status = obd.get_status()

    card_simple(f"""
    <h3 style="margin: 0 0 {SPACE_4} 0; color: {TEXT_PRIMARY}; font-size: {FONT_SIZE_H3};">Scan for DTCs</h3>
    """)

    # Scan controls - responsive button group
    scan_disabled = st.session_state.scan_status == "scanning"
    has_results = bool(st.session_state.scan_results)

    # Use Streamlit columns for actual button functionality (they need callbacks)
    col1, col2, col3 = st.columns(3, gap="small")
    with col1:
        if button_primary("🔍 Scan for Codes", disabled=scan_disabled, use_container_width=True, key="btn_scan"):
            perform_scan(obd)

    with col2:
        if button_secondary("🔄 Rescan", disabled=scan_disabled, use_container_width=True, key="btn_rescan"):
            perform_scan(obd)

    with col3:
        if button_ghost("✖ Clear Results", disabled=not has_results, use_container_width=True, key="btn_clear_scan"):
            clear_scan_results()

    # Scan status indicator
    status_config = {
        "idle": {"label": "Ready to scan", "variant": AlertVariant.INFO},
        "scanning": {"label": "Scanning ECU for codes...", "variant": AlertVariant.INFO},
        "complete": {"label": f"Scan complete — {len(st.session_state.scan_results)} code(s) found", "variant": AlertVariant.SUCCESS},
        "error": {"label": "Scan failed", "variant": AlertVariant.CRITICAL}
    }

    sc = status_config.get(st.session_state.scan_status, status_config["idle"])
    alert("", sc["label"], variant=sc["variant"])

    # Last scan time
    if st.session_state.last_scan_time:
        st.caption(f"Last scan: {st.session_state.last_scan_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Mode info
    st.caption(f"Mode: {status['mode'].upper()} • Connection: {status['connection_state'].title()}")


# =============================================================================
# UI COMPONENTS - DTC LIST (RESPONSIVE TABLE)
# =============================================================================

def render_dtc_list():
    """Render the list of found DTCs using responsive table/card layout."""
    if not st.session_state.scan_results:
        empty_state(EmptyStateProps(
            title="No DTCs Found",
            message="Click \"Scan for Codes\" to check for diagnostic trouble codes",
            icon="🔍"
        ))
        return

    # Build table data
    table_data = []
    for dtc in st.session_state.scan_results:
        severity_info = get_severity_info(dtc.severity)
        table_data.append({
            "code": dtc.code,
            "description": dtc.description,
            "severity": severity_info["label"],
            "severity_raw": dtc.severity,
            "status": dtc.status.title(),
            "is_demo": dtc.is_demo,
            "_dtc_obj": dtc,  # Keep reference for selection
        })

    columns = [
        TableColumn(key="code", header="Code", width="90px", format=lambda v: f'<code style="font-family: {FONT_FAMILY_MONO}; font-size: {FONT_SIZE_BODY};">{v}</code>'),
        TableColumn(key="description", header="Description"),
        TableColumn(key="severity", header="Severity", width="120px", format=lambda v, row: (
            badge(label=get_severity_info(row["severity_raw"])["label"], variant=get_severity_badge_variant(row["severity_raw"]), key=f"dtc_sev_{row['code']}") +
            (badge(label="DEMO", variant=BadgeVariant.WARNING, key=f"dtc_demo_{row['code']}") if row["is_demo"] else "")
        )),
        TableColumn(key="status", header="Status", width="100px"),
    ]

    # Custom selection handling - responsive table with horizontal scroll on mobile
    selected = table(TableProps(
        columns=columns,
        data=table_data,
        key="dtc_list_table",
        selectable=True,
        on_row_click=lambda row: _on_dtc_select(row["_dtc_obj"]),
        empty_message="No DTCs found",
        striped=True,
        hoverable=True,
    ))


def _on_dtc_select(dtc: DiagnosticCode):
    """Handle DTC selection from table."""
    st.session_state.selected_dtc = dtc.code
    st.rerun()


# =============================================================================
# UI COMPONENTS - DTC DETAIL PANEL (RESPONSIVE CARDS)
# =============================================================================

def render_dtc_detail():
    """Render detailed information for the selected DTC using design system cards - RESPONSIVE."""
    if not st.session_state.selected_dtc or not st.session_state.scan_results:
        empty_state(EmptyStateProps(
            title="Select a DTC",
            message="Click on a code from the list to view detailed information",
            icon="📋"
        ))
        return

    dtc = next((d for d in st.session_state.scan_results if d.code == st.session_state.selected_dtc), None)
    if not dtc:
        empty_state(EmptyStateProps(
            title="DTC Not Found",
            message="The selected DTC is no longer in the scan results",
            icon="⚠"
        ))
        return

    severity_info = get_severity_info(dtc.severity)

    # Header card
    card(CardProps(
        title=dtc.code,
        subtitle=f"{dtc.description} • {severity_info['label']} • {dtc.status.title()}{' • DEMO' if dtc.is_demo else ''}",
        content="",
        elevated=True,
    ))

    # Description
    card_simple(f"""
    <h4 style="margin: 0 0 {SPACE_2} 0; color: {TEXT_SECONDARY}; font-size: {FONT_SIZE_LABEL}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_LABEL};">Description</h4>
    <p style="margin: 0; color: {TEXT_PRIMARY}; line-height: 1.6;">{dtc.description}</p>
    """)

    # Severity classification
    card_simple(f"""
    <h4 style="margin: 0 0 {SPACE_2} 0; color: {TEXT_SECONDARY}; font-size: {FONT_SIZE_LABEL}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_LABEL};">Severity Classification</h4>
    <p style="margin: 0; color: {TEXT_PRIMARY}; line-height: 1.6;">
        <strong style="color: {severity_info['color']};">{severity_info['label']}</strong>: {severity_info['description']}
    </p>
    """)

    # Possible causes
    if dtc.possible_causes:
        causes_html = "".join([f"<li>{cause}</li>" for cause in dtc.possible_causes])
        card_simple(f"""
        <h4 style="margin: 0 0 {SPACE_2} 0; color: {TEXT_SECONDARY}; font-size: {FONT_SIZE_LABEL}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_LABEL};">Possible Causes</h4>
        <ul style="margin: 0; padding-left: {SPACE_5}; color: {TEXT_PRIMARY};">{causes_html}</ul>
        """)

    # Recommended verification
    if dtc.recommended_verification:
        verify_html = "".join([f"<li>{verify}</li>" for verify in dtc.recommended_verification])
        card_simple(f"""
        <h4 style="margin: 0 0 {SPACE_2} 0; color: {TEXT_SECONDARY}; font-size: {FONT_SIZE_LABEL}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_LABEL};">Recommended Verification</h4>
        <ul style="margin: 0; padding-left: {SPACE_5}; color: {TEXT_PRIMARY};">{verify_html}</ul>
        """)

    # Freeze frame data
    if dtc.freeze_frame:
        ff_rows = []
        for key, value in dtc.freeze_frame.items():
            ff_rows.append(f"""
            <tr>
                <td style="padding: {SPACE_2} {SPACE_3}; color: {TEXT_SECONDARY}; border-bottom: 1px solid {BORDER_SUBTLE};">{key}</td>
                <td style="padding: {SPACE_2} {SPACE_3}; color: {TEXT_PRIMARY}; font-family: {FONT_FAMILY_MONO}; border-bottom: 1px solid {BORDER_SUBTLE};">{value}</td>
            </tr>
            """)

        card_simple(f"""
        <h4 style="margin: 0 0 {SPACE_2} 0; color: {TEXT_SECONDARY}; font-size: {FONT_SIZE_LABEL}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_LABEL};">Freeze Frame Data</h4>
        <table style="width: 100%; border-collapse: collapse;">{"".join(ff_rows)}</table>
        """)

    # Demo disclaimer
    if dtc.is_demo:
        alert("Demo Code", "This DTC is simulated for demonstration purposes only. It does not indicate an actual fault in your vehicle. Always verify with a real OBD-II scan before any repair.", variant=AlertVariant.WARNING)


# =============================================================================
# UI COMPONENTS - REPORT PANEL (RESPONSIVE)
# =============================================================================

def render_report_panel(obd, db):
    """Render diagnostic report generation panel using design system - RESPONSIVE."""
    if not st.session_state.scan_results:
        empty_state(EmptyStateProps(
            title="No Scan Results to Report",
            message="Perform a scan first to generate a diagnostic report",
            icon="📄"
        ))
        return

    # Report preview
    report_text = generate_report_text(obd)

    card(CardProps(
        title="Diagnostic Report",
        subtitle=f"{len(st.session_state.scan_results)} DTC(s) • {'DEMO' if all(d.is_demo for d in st.session_state.scan_results) else 'LIVE'} mode",
        content=f"""
        <div style="
            background: {SURFACE_SECONDARY};
            border: 1px solid {BORDER_DEFAULT};
            border-radius: {RADIUS_MD};
            padding: {SPACE_4};
            max-height: 300px;
            overflow-y: auto;
            font-family: {FONT_FAMILY_MONO};
            font-size: {FONT_SIZE_CAPTION};
            color: {TEXT_PRIMARY};
            white-space: pre-wrap;
            line-height: 1.5;
        ">{report_text}</div>
        """,
    ))

    # Action buttons - responsive (stack on mobile)
    col1, col2 = st.columns(2, gap="small")
    with col1:
        if button_primary("💾 Save Report", use_container_width=True, key="btn_save_report"):
            save_report(db, report_text)

    with col2:
        st.download_button(
            label="📥 Download Report",
            data=report_text,
            file_name=f"i20_diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True,
            key="btn_download_report"
        )


# =============================================================================
# UI COMPONENTS - AI DIAGNOSIS PANEL (RESPONSIVE)
# =============================================================================

def render_ai_diagnosis_panel(obd, db):
    """Render the AI Diagnosis panel using design system components - RESPONSIVE."""
    ai_service = get_ai_service()
    ai_connected = ai_service.check_connection()

    if not ai_connected:
        empty_state(EmptyStateProps(
            title="AI Service Unavailable",
            message="LM Studio is not connected. Start LM Studio and load a model to use AI diagnosis.",
            icon="🤖"
        ))
        return

    if not st.session_state.scan_results:
        empty_state(EmptyStateProps(
            title="No Scan Results",
            message="Perform a DTC scan first, then run AI diagnosis for intelligent analysis.",
            icon="🤖"
        ))
        return

    # Run AI Diagnosis button - responsive
    run_disabled = st.session_state.ai_diagnosis_status == "running"
    has_result = st.session_state.ai_diagnosis_result is not None

    col1, col2 = st.columns([3, 1], gap="small")
    with col1:
        if button_primary("🧠 Run AI Diagnosis", disabled=run_disabled, use_container_width=True, key="btn_ai_diag"):
            run_ai_diagnosis(obd, db)
    with col2:
        if has_result and button_ghost("🗑 Clear", use_container_width=True, key="btn_clear_ai"):
            clear_ai_diagnosis()

    # Status indicator
    status_config = {
        "idle": {"label": "Ready to run AI diagnosis", "variant": AlertVariant.INFO},
        "running": {"label": "Analyzing with AI...", "variant": AlertVariant.INFO},
        "complete": {"label": "AI diagnosis complete", "variant": AlertVariant.SUCCESS},
        "error": {"label": "AI diagnosis failed", "variant": AlertVariant.CRITICAL}
    }
    sc = status_config.get(st.session_state.ai_diagnosis_status, status_config["idle"])
    alert("", sc["label"], variant=sc["variant"])

    # Display AI diagnosis result
    if st.session_state.ai_diagnosis_result:
        render_ai_diagnosis_result(st.session_state.ai_diagnosis_result)

    if st.session_state.ai_diagnosis_time:
        st.caption(f"Last run: {st.session_state.ai_diagnosis_time.strftime('%Y-%m-%d %H:%M:%S')}")


def render_ai_diagnosis_result(result: DiagnosticResult):
    """Render the AI diagnosis result using design system cards and badges - RESPONSIVE."""
    # Data source badge
    data_source_label = "SIMULATION" if result.data_source == DataSource.SIMULATION else "REAL VEHICLE"
    data_source_variant = get_data_source_badge_variant(result.data_source)

    # Overall severity badge
    severity_variant = get_diagnostic_severity_badge_variant(result.severity)
    status_variant = get_diagnostic_status_badge_variant(result.diagnostic_status)

    # Summary card
    card(CardProps(
        title=f"Diagnosis ID: {result.diagnosis_id}",
        subtitle=f"Status: {result.diagnostic_status.value.replace('_', ' ').title()} • Confidence: {result.confidence:.0%} • Data: {data_source_label}",
        content=f"""
        <div style="margin-bottom: {SPACE_3};">
            <strong>Summary:</strong> {result.summary or 'No summary provided'}
        </div>
        <div style="display: flex; flex-wrap: wrap; gap: {GAP_INLINE}; margin-bottom: {SPACE_3};">
            {badge(label=result.severity.value.upper(), variant=severity_variant, key=f"ai_diag_sev_{result.diagnosis_id}")}
            {badge(label=result.diagnostic_status.value.upper().replace('_', ' '), variant=status_variant, key=f"ai_diag_status_{result.diagnosis_id}")}
            {badge(label=data_source_label, variant=data_source_variant, key=f"ai_diag_source_{result.diagnosis_id}")}
        </div>
        """,
        elevated=True,
    ))

    # Detected Symptoms
    if result.detected_symptoms:
        symptoms_html = "".join([f"<li>{s}</li>" for s in result.detected_symptoms])
        card_simple(f"""
        <h4 style="margin: 0 0 {SPACE_2} 0; color: {TEXT_SECONDARY}; font-size: {FONT_SIZE_LABEL}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_LABEL};">Detected Symptoms</h4>
        <ul style="margin: 0; padding-left: {SPACE_5}; color: {TEXT_PRIMARY};">{symptoms_html}</ul>
        """)

    # Confirmed Faults
    if result.confirmed_faults:
        faults_html = "".join([f'<li><code style="font-family: {FONT_FAMILY_MONO};">{dtc}</code></li>' for dtc in result.confirmed_faults])
        card_simple(f"""
        <h4 style="margin: 0 0 {SPACE_2} 0; color: {TEXT_SECONDARY}; font-size: {FONT_SIZE_LABEL}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_LABEL};">Confirmed Faults (DTCs)</h4>
        <ul style="margin: 0; padding-left: {SPACE_5}; color: {TEXT_PRIMARY};">{faults_html}</ul>
        """)

    # Primary Diagnosis
    if result.primary_diagnosis:
        _render_diagnosis_card(result.primary_diagnosis, "Primary Diagnosis", True)

    # Secondary Diagnoses
    if result.secondary_diagnoses:
        for sd in result.secondary_diagnoses:
            _render_diagnosis_card(sd, "Secondary Diagnosis", False)

    # Recommended Actions
    if result.recommended_actions:
        _render_recommended_actions(result.recommended_actions)

    # Safety Warnings
    if result.safety_warnings:
        warnings_html = "".join([f'<li style="color: {STATUS_CRITICAL};">{w}</li>' for w in result.safety_warnings])
        card_simple(f"""
        <h4 style="margin: 0 0 {SPACE_2} 0; color: {TEXT_SECONDARY}; font-size: {FONT_SIZE_LABEL}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_LABEL};">⚠ Safety Warnings</h4>
        <ul style="margin: 0; padding-left: {SPACE_5};">{warnings_html}</ul>
        """)

    # Missing Information
    if result.missing_information:
        missing_html = "".join([f"<li>{m}</li>" for m in result.missing_information])
        card_simple(f"""
        <h4 style="margin: 0 0 {SPACE_2} 0; color: {TEXT_SECONDARY}; font-size: {FONT_SIZE_LABEL}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_LABEL};">Missing Information</h4>
        <ul style="margin: 0; padding-left: {SPACE_5}; color: {TEXT_SECONDARY};">{missing_html}</ul>
        """)

    # Metadata
    meta_lines = [
        f"<strong>Model:</strong> {result.model_information.get('model', 'Unknown')}",
        f"<strong>Temperature:</strong> {result.model_information.get('temperature', 'N/A')}",
        f"<strong>Max Tokens:</strong> {result.model_information.get('max_tokens', 'N/A')}",
        f"<strong>Data Quality:</strong> {result.data_quality.value.upper()}",
        f"<strong>Rule Engine Findings:</strong> {', '.join(result.rule_engine_findings) if result.rule_engine_findings else 'None'}",
        f"<strong>RAG Sources:</strong> {', '.join(result.rag_sources) if result.rag_sources else 'None'}",
    ]
    card_simple(f"""
    <div style="font-size: {FONT_SIZE_CAPTION}; color: {TEXT_MUTED}; line-height: 2;">
        {'<br>'.join(meta_lines)}
    </div>
    """)

    # Simulation disclaimer
    if result.data_source == DataSource.SIMULATION:
        alert("Simulation Data", "This diagnosis is based on simulated telemetry data and does not represent an actual diagnosis of your vehicle. Always verify with a real OBD-II scan and consult a qualified technician before any repair.", variant=AlertVariant.WARNING)


def _render_diagnosis_card(diagnosis, title: str, is_primary: bool):
    """Render a primary or secondary diagnosis card - RESPONSIVE."""
    border_color = ACCENT_PRIMARY if is_primary else ACCENT_SECONDARY

    card(CardProps(
        title=f"{title}: {diagnosis.code} - {diagnosis.description}",
        subtitle=f"Confidence: {diagnosis.confidence:.0%} • Severity: {diagnosis.severity.value.upper()}",
        content="",
        elevated=True,
    ))

    for i, cause in enumerate(diagnosis.probable_causes):
        conf_class = "confidence-high" if cause.confidence >= 0.7 else "confidence-medium" if cause.confidence >= 0.4 else "confidence-low"

        card_simple(f"""
        <div style="border-left: 3px solid {border_color}; padding-left: {SPACE_4}; margin-bottom: {SPACE_4};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: {SPACE_2};">
                <strong>{i+1}. {cause.cause}</strong>
                <span style="background: {STATUS_SUCCESS if cause.confidence >= 0.7 else STATUS_WARNING if cause.confidence >= 0.4 else STATUS_CRITICAL}22; color: {STATUS_SUCCESS if cause.confidence >= 0.7 else STATUS_WARNING if cause.confidence >= 0.4 else STATUS_CRITICAL}; padding: 2px 8px; border-radius: 12px; font-size: {FONT_SIZE_CAPTION}; font-weight: 600;">{cause.confidence:.0%}</span>
            </div>
            <p style="margin: 0 0 {SPACE_2} 0; color: {TEXT_SECONDARY}; font-size: {FONT_SIZE_BODY_SM};">{cause.explanation}</p>
            {_render_evidence_list(cause.supporting_evidence, "Supporting Evidence", CHART_GOOD) if cause.supporting_evidence else ''}
            {_render_evidence_list(cause.contradictory_evidence, "Contradictory Evidence", CHART_CRITICAL) if cause.contradictory_evidence else ''}
            {_render_evidence_list(cause.verification_steps, "Verification Steps", ACCENT_PRIMARY) if cause.verification_steps else ''}
            <div style="margin-top: {SPACE_2};">
                {_render_urgency_badge(cause.urgency)}
            </div>
        </div>
        """)


def _render_evidence_list(items: List[str], label: str, color: str) -> str:
    """Render an evidence list (supporting, contradictory, verification)."""
    if not items:
        return ""
    items_html = "".join([f'<li style="color: {TEXT_SECONDARY}; font-size: {FONT_SIZE_CAPTION};">{item}</li>' for item in items])
    return f"""
    <div style="margin-top: {SPACE_2};">
        <strong style="color: {color}; font-size: {FONT_SIZE_CAPTION};">{label}:</strong>
        <ul style="margin: {SPACE_1} 0 0 {SPACE_4}; padding: 0;">{items_html}</ul>
    </div>
    """


def _render_urgency_badge(urgency: str) -> str:
    """Render urgency badge."""
    urgency_colors = {
        "immediate": STATUS_CRITICAL,
        "soon": STATUS_WARNING,
        "schedule": ACCENT_PRIMARY,
        "monitor": STATUS_INFO,
    }
    color = urgency_colors.get(urgency, STATUS_NEUTRAL)
    return f'<span style="background: {color}22; color: {color}; padding: 2px 8px; border-radius: 8px; font-size: {FONT_SIZE_CAPTION}; font-weight: 600; text-transform: uppercase;">{urgency.upper()}</span>'


def _render_recommended_actions(actions: List):
    """Render recommended actions with priority, safety, cost - RESPONSIVE."""
    for i, rec in enumerate(actions):
        safety_colors = {
            "safe": STATUS_SUCCESS,
            "caution": STATUS_WARNING,
            "professional": STATUS_CRITICAL,
        }
        safety_color = safety_colors.get(rec.safety_level.value, STATUS_NEUTRAL)

        card(CardProps(
            title=f"{i+1}. {rec.recommendation}",
            subtitle=f"Priority: {rec.priority}/10 • Safety: {rec.safety_level.value.upper()}{' • PROFESSIONAL REQUIRED' if rec.requires_professional else ''}",
            content=f"""
            <p style="margin: 0 0 {SPACE_2} 0; color: {TEXT_SECONDARY};">{rec.rationale}</p>
            <div style="display: flex; flex-wrap: wrap; gap: {GAP_INLINE}; margin-bottom: {SPACE_2};">
                <span style="background: {safety_color}22; color: {safety_color}; padding: 2px 8px; border-radius: 8px; font-size: {FONT_SIZE_CAPTION}; font-weight: 600; text-transform: uppercase;">{rec.safety_level.value.upper()}</span>
                {'<span style="background: '+STATUS_CRITICAL+'22; color: '+STATUS_CRITICAL+'; padding: 2px 8px; border-radius: 8px; font-size: '+FONT_SIZE_CAPTION+'; font-weight: 600; text-transform: uppercase;">PROFESSIONAL REQUIRED</span>' if rec.requires_professional else ''}
            </div>
            {_render_evidence_list(rec.supporting_evidence, "Supporting Evidence", CHART_GOOD) if rec.supporting_evidence else ''}
            {f'<p style="margin: 0; font-size: {FONT_SIZE_CAPTION}; color: {TEXT_SECONDARY};"><strong>Estimated Cost:</strong> {rec.estimated_cost_inr}</p>' if rec.estimated_cost_inr else ''}
            """,
        ))


# =============================================================================
# UI COMPONENTS - RULE ENGINE PANEL (RESPONSIVE)
# =============================================================================

def render_rule_engine_panel(obd, db):
    """Render the Deterministic Rule Engine panel using design system - RESPONSIVE."""
    if not RULE_ENGINE_AVAILABLE:
        empty_state(EmptyStateProps(
            title="Rule Engine Unavailable",
            message="The deterministic rule engine could not be loaded.",
            icon="⚙️"
        ))
        return

    obd_status = obd.get_status()
    readings = obd.get_all_readings()

    if not readings:
        empty_state(EmptyStateProps(
            title="No Sensor Data",
            message="Perform a DTC scan or connect to OBD to get sensor readings, then run rule evaluation.",
            icon="⚙️"
        ))
        return

    # Run Rule Evaluation button - responsive
    run_disabled = st.session_state.rule_evaluation_status == "running"
    has_result = st.session_state.rule_evaluation_result is not None

    col1, col2 = st.columns([3, 1], gap="small")
    with col1:
        if button_primary("📋 Run Rule Evaluation", disabled=run_disabled, use_container_width=True, key="btn_rule_eval"):
            run_rule_evaluation(obd, db)
    with col2:
        if has_result and button_ghost("🗑 Clear", use_container_width=True, key="btn_clear_rule"):
            clear_rule_evaluation()

    # Status indicator
    status_config = {
        "idle": {"label": "Ready to run rule evaluation", "variant": AlertVariant.INFO},
        "running": {"label": "Evaluating rules...", "variant": AlertVariant.INFO},
        "complete": {"label": "Rule evaluation complete", "variant": AlertVariant.SUCCESS},
        "error": {"label": "Rule evaluation failed", "variant": AlertVariant.CRITICAL}
    }
    sc = status_config.get(st.session_state.rule_evaluation_status, status_config["idle"])
    alert("", sc["label"], variant=sc["variant"])

    # Display rule evaluation result
    if st.session_state.rule_evaluation_result:
        render_rule_evaluation_result(st.session_state.rule_evaluation_result)

    if st.session_state.rule_evaluation_time:
        st.caption(f"Last run: {st.session_state.rule_evaluation_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Rule Statistics
    if st.session_state.rule_evaluation_result:
        with st.expander("📊 Rule Engine Statistics", expanded=False):
            render_rule_statistics()

    # Rule History
    with st.expander("📜 Rule Evaluation History", expanded=False):
        render_rule_history()


def render_rule_evaluation_result(result):
    """Render the rule evaluation result using design system components - RESPONSIVE."""
    findings = result.findings
    critical_count = len([f for f in findings if f.severity == RuleSeverity.CRITICAL])
    high_count = len([f for f in findings if f.severity == RuleSeverity.HIGH])
    medium_count = len([f for f in findings if f.severity == RuleSeverity.MEDIUM])
    low_count = len([f for f in findings if f.severity in [RuleSeverity.LOW, RuleSeverity.INFORMATIONAL]])

    # Data source badge
    data_source_label = "SIMULATION" if result.data_source == RuleDataSource.SIMULATION else "REAL VEHICLE"
    data_source_variant = BadgeVariant.WARNING if result.data_source == RuleDataSource.SIMULATION else BadgeVariant.SUCCESS

    # Overall severity
    overall_severity = RuleSeverity.INFORMATIONAL
    if critical_count > 0:
        overall_severity = RuleSeverity.CRITICAL
    elif high_count > 0:
        overall_severity = RuleSeverity.HIGH
    elif medium_count > 0:
        overall_severity = RuleSeverity.MEDIUM
    elif low_count > 0:
        overall_severity = RuleSeverity.LOW

    overall_variant = get_rule_severity_badge_variant(overall_severity)

    # Summary card
    card(CardProps(
        title=f"Evaluation ID: {result.evaluation_id}",
        subtitle=f"Rules Evaluated: {result.rules_evaluated} • Skipped: {result.rules_skipped} • Failed: {result.rules_failed} • Data Quality: {result.data_quality.upper()}",
        content=f"""
        <div style="display: flex; flex-wrap: wrap; gap: {GAP_INLINE}; margin-bottom: {SPACE_3};">
            {badge(label=f"Total Findings: {len(findings)}", variant=BadgeVariant.INFO, key=f"rule_total_{result.evaluation_id}")}
            {badge(label=f"Critical: {critical_count}", variant=BadgeVariant.CRITICAL, key=f"rule_crit_{result.evaluation_id}")}
            {badge(label=f"High: {high_count}", variant=BadgeVariant.WARNING, key=f"rule_high_{result.evaluation_id}")}
            {badge(label=f"Medium: {medium_count}", variant=BadgeVariant.INFO, key=f"rule_med_{result.evaluation_id}")}
            {badge(label=f"Low: {low_count}", variant=BadgeVariant.SUCCESS, key=f"rule_low_{result.evaluation_id}")}
            {badge(label=overall_severity.value.upper(), variant=overall_variant, key=f"rule_overall_{result.evaluation_id}")}
            {badge(label=data_source_label, variant=data_source_variant, key=f"rule_source_{result.evaluation_id}")}
        </div>
        <div style="font-size: {FONT_SIZE_CAPTION}; color: {TEXT_MUTED};">
            Execution Time: {result.execution_duration_ms:.1f}ms
        </div>
        """,
        elevated=True,
    ))

    # Findings grouped by severity - responsive card grid
    if findings:
        severity_order = {
            RuleSeverity.CRITICAL: 0,
            RuleSeverity.HIGH: 1,
            RuleSeverity.MEDIUM: 2,
            RuleSeverity.LOW: 3,
            RuleSeverity.INFORMATIONAL: 4
        }
        findings_sorted = sorted(findings, key=lambda f: (severity_order.get(f.severity, 5), f.priority))

        for finding in findings_sorted:
            render_rule_finding(finding)

    # Simulation disclaimer
    if result.data_source == RuleDataSource.SIMULATION:
        alert("Simulation Data", "This rule evaluation is based on simulated telemetry data and does not represent an actual evaluation of your vehicle. Always verify with a real OBD-II scan and consult a qualified technician before any repair.", variant=AlertVariant.WARNING)


def render_rule_finding(finding):
    """Render a single rule finding using design system card - RESPONSIVE."""
    severity_variant = get_rule_severity_badge_variant(finding.severity)
    status_variant = get_rule_status_badge_variant(finding.status)

    severity_colors = {
        RuleSeverity.CRITICAL: STATUS_CRITICAL,
        RuleSeverity.HIGH: STATUS_WARNING,
        RuleSeverity.MEDIUM: STATUS_INFO,
        RuleSeverity.LOW: STATUS_SUCCESS,
        RuleSeverity.INFORMATIONAL: TEXT_MUTED,
    }
    severity_color = severity_colors.get(finding.severity, TEXT_MUTED)

    status_colors = {
        RuleStatus.TRIGGERED: STATUS_CRITICAL,
        RuleStatus.NOT_TRIGGERED: STATUS_SUCCESS,
        RuleStatus.SKIPPED: STATUS_WARNING,
        RuleStatus.ERROR: STATUS_CRITICAL,
        RuleStatus.INSUFFICIENT_DATA: TEXT_MUTED,
    }
    status_color = status_colors.get(finding.status, TEXT_MUTED)

    card(CardProps(
        title=f"{finding.rule_id} - {finding.rule_name}",
        subtitle=f"Severity: {finding.severity.value.upper()} • Status: {finding.status.value.upper().replace('_', ' ')} • Confidence: {finding.confidence:.0%} • Priority: {finding.priority}/10",
        content=f"""
        <p style="margin: 0 0 {SPACE_2} 0; color: {TEXT_PRIMARY};"><strong>Summary:</strong> {finding.summary}</p>
        {f'<p style="margin: 0 0 {SPACE_2} 0; color: {TEXT_SECONDARY}; font-size: {FONT_SIZE_BODY_SM};"><strong>Explanation:</strong> {finding.explanation}</p>' if finding.explanation else ''}
        {_render_key_value_list(finding.observed_values, "Observed Values") if finding.observed_values else ''}
        {_render_key_value_list(finding.expected_values, "Expected Values") if finding.expected_values else ''}
        {_render_evidence_list(finding.evidence, "Evidence", severity_color) if finding.evidence else ''}
        {_render_evidence_list(finding.missing_data, "Missing Data", STATUS_WARNING) if finding.missing_data else ''}
        {_render_evidence_list(finding.recommended_checks, "Recommended Checks", ACCENT_PRIMARY) if finding.recommended_checks else ''}
        {_render_evidence_list(finding.recommended_actions, "Recommended Actions", ACCENT_SECONDARY) if finding.recommended_actions else ''}
        {_render_evidence_list(finding.safety_notes, "Safety Notes", STATUS_CRITICAL) if finding.safety_notes else ''}
        {f'<p style="margin: {SPACE_2} 0 0 0; font-size: {FONT_SIZE_CAPTION}; color: {TEXT_MUTED};"><strong>DTC Hints:</strong> {", ".join(finding.dtc_hints)}</p>' if finding.dtc_hints else ''}
        {f'<p style="margin: {SPACE_2} 0 0 0; font-size: {FONT_SIZE_CAPTION}; color: {TEXT_MUTED};">Evaluation: {finding.evaluation_duration_ms:.1f}ms | Data Source: {finding.data_source.value}</p>' if finding.evaluation_duration_ms else ''}
        """,
        footer=f"""
        <div style="display: flex; flex-wrap: wrap; gap: {GAP_INLINE};">
            {badge(label=finding.severity.value.upper(), variant=severity_variant, key=f"rf_sev_{finding.rule_id}")}
            {badge(label=finding.status.value.upper().replace('_', ' '), variant=status_variant, key=f"rf_status_{finding.rule_id}")}
            {badge(label=f"Source: {finding.rule_source}", variant=BadgeVariant.SECONDARY, key=f"rf_source_{finding.rule_id}")}
        </div>
        """,
    ))


def _render_key_value_list(data: Dict[str, Any], label: str) -> str:
    """Render a key-value list."""
    if not data:
        return ""
    rows = "".join([f'<div style="display: flex; justify-content: space-between; padding: {SPACE_1} 0; border-bottom: 1px solid {BORDER_SUBTLE};"><span style="color: {TEXT_SECONDARY};">{k}</span><span style="color: {TEXT_PRIMARY}; font-family: {FONT_FAMILY_MONO};">{v}</span></div>' for k, v in data.items()])
    return f"""
    <div style="margin-top: {SPACE_2};">
        <strong style="color: {TEXT_SECONDARY}; font-size: {FONT_SIZE_CAPTION};">{label}:</strong>
        <div>{rows}</div>
    </div>
    """


def render_rule_statistics():
    """Render rule engine statistics using design system - RESPONSIVE."""
    if not st.session_state.rule_evaluation_result:
        st.info("Run rule evaluation to see statistics.")
        return

    try:
        engine = get_rule_engine()
        stats = engine.get_statistics()

        # Metrics row - responsive grid (4 on desktop, 2 on tablet, 1 on mobile)
        col1, col2, col3, col4 = st.columns(4, gap="medium")
        with col1:
            card_simple(f"""
            <div style="text-align: center; padding: var(--i20-spacing-md);">
                <div style="font-size: {FONT_SIZE_H2}; font-weight: {FONT_WEIGHT_NUMERIC}; color: {ACCENT_PRIMARY}; font-family: {FONT_FAMILY_MONO};">{stats["total_rules_loaded"]}</div>
                <div style="font-size: {FONT_SIZE_CAPTION}; color: {TEXT_SECONDARY}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_CAPTION};">Total Rules Loaded</div>
            </div>
            """)
        with col2:
            card_simple(f"""
            <div style="text-align: center; padding: var(--i20-spacing-md);">
                <div style="font-size: {FONT_SIZE_H2}; font-weight: {FONT_WEIGHT_NUMERIC}; color: {STATUS_SUCCESS}; font-family: {FONT_FAMILY_MONO};">{stats["enabled_rules"]}</div>
                <div style="font-size: {FONT_SIZE_CAPTION}; color: {TEXT_SECONDARY}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_CAPTION};">Enabled Rules</div>
            </div>
            """)
        with col3:
            card_simple(f"""
            <div style="text-align: center; padding: var(--i20-spacing-md);">
                <div style="font-size: {FONT_SIZE_H2}; font-weight: {FONT_WEIGHT_NUMERIC}; color: {ACCENT_SECONDARY}; font-family: {FONT_FAMILY_MONO};">{stats["history_size"]}</div>
                <div style="font-size: {FONT_SIZE_CAPTION}; color: {TEXT_SECONDARY}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_CAPTION};">Sensor History Size</div>
            </div>
            """)
        with col4:
            card_simple(f"""
            <div style="text-align: center; padding: var(--i20-spacing-md);">
                <div style="font-size: {FONT_SIZE_H2}; font-weight: {FONT_WEIGHT_NUMERIC}; color: {TEXT_PRIMARY}; font-family: {FONT_FAMILY_MONO};">{stats["data_source"].upper()}</div>
                <div style="font-size: {FONT_SIZE_CAPTION}; color: {TEXT_SECONDARY}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_CAPTION};">Data Source</div>
            </div>
            """)

        # Rules by type
        if stats["rules_by_type"]:
            st.markdown(f"**Rules by Type**")
            for rule_type, count in stats["rules_by_type"].items():
                badge(rule_type, BadgeVariant.INFO)
                st.caption(f"{count} rules")

        # Rules by category
        if stats["rules_by_category"]:
            st.markdown(f"**Rules by Category**")
            for category, count in stats["rules_by_category"].items():
                badge(category, BadgeVariant.PRIMARY)
                st.caption(f"{count} rules")

        # Rules by severity
        if stats["rules_by_severity"]:
            st.markdown(f"**Rules by Severity**")
            for severity, count in stats["rules_by_severity"].items():
                variant = BadgeVariant.CRITICAL if severity == "critical" else BadgeVariant.WARNING if severity == "high" else BadgeVariant.INFO if severity == "medium" else BadgeVariant.SUCCESS
                badge(severity.upper(), variant)
                st.caption(f"{count} rules")

        # Last evaluation
        if stats["last_evaluation"]:
            le = stats["last_evaluation"]
            st.markdown("**Last Evaluation**")
            st.caption(f"ID: {le['evaluation_id']}")
            st.caption(f"Time: {le['timestamp']}")
            st.caption(f"Rules Evaluated: {le['rules_evaluated']}")
            st.caption(f"Findings: {le['findings_count']}")
            st.caption(f"Duration: {le['execution_duration_ms']:.1f}ms")

    except Exception as e:
        st.error(f"Failed to load statistics: {e}")


def render_rule_history():
    """Render rule evaluation history using design system table - RESPONSIVE."""
    try:
        engine = get_rule_engine()
        history = engine.get_evaluation_history(limit=20)

        if not history:
            empty_state(EmptyStateProps(
                title="No Rule Evaluation History",
                message="Run a rule evaluation to populate history",
                icon="📜"
            ))
            return

        table_data = []
        for eval_record in history:
            table_data.append({
                "timestamp": eval_record.get("timestamp", "Unknown")[:19],
                "rules_evaluated": eval_record.get("rules_evaluated", 0),
                "findings": eval_record.get("findings_count", 0),
                "critical": eval_record.get("critical_findings", 0),
                "high": eval_record.get("high_findings", 0),
                "medium": eval_record.get("medium_findings", 0),
                "low": eval_record.get("low_findings", 0),
                "data_quality": eval_record.get("data_quality", "unknown").upper(),
            })

        columns = [
            TableColumn(key="timestamp", header="Time", width="160px"),
            TableColumn(key="rules_evaluated", header="Rules Evaluated", width="120px", align="center"),
            TableColumn(key="findings", header="Findings", width="90px", align="center"),
            TableColumn(key="critical", header="Critical", width="90px", align="center", format=lambda v: f'<span style="color: {STATUS_CRITICAL}; font-weight: 600;">{v}</span>'),
            TableColumn(key="high", header="High", width="90px", align="center", format=lambda v: f'<span style="color: {STATUS_WARNING}; font-weight: 600;">{v}</span>'),
            TableColumn(key="medium", header="Medium", width="90px", align="center", format=lambda v: f'<span style="color: {STATUS_INFO}; font-weight: 600;">{v}</span>'),
            TableColumn(key="low", header="Low", width="90px", align="center", format=lambda v: f'<span style="color: {STATUS_SUCCESS}; font-weight: 600;">{v}</span>'),
            TableColumn(key="data_quality", header="Data Quality", width="120px"),
        ]

        table(TableProps(
            columns=columns,
            data=table_data,
            key="rule_history_table",
            empty_message="No rule evaluation history",
            striped=True,
            hoverable=True,
        ))

    except Exception as e:
        st.error(f"Failed to load history: {e}")


# =============================================================================
# UI COMPONENTS - HISTORY PANEL (RESPONSIVE TABLE)
# =============================================================================

def render_history_panel(db):
    """Render diagnostic scan history using design system table - RESPONSIVE."""
    reports = db.get_diagnostic_reports(limit=20)

    if not reports:
        empty_state(EmptyStateProps(
            title="No Scan History",
            message="Saved diagnostic reports will appear here",
            icon="📜"
        ))
        return

    table_data = []
    for report in reports:
        scan_time = report["scan_time"][:19] if report["scan_time"] else "Unknown"
        mode = "DEMO" if report["is_demo"] else "LIVE"
        dtc_count = report["dtc_count"]
        codes_str = ", ".join([c["code"] for c in report["codes"][:3]]) if report["codes"] else "None"
        if report["codes"] and len(report["codes"]) > 3:
            codes_str += f" +{len(report['codes']) - 3} more"
        summary = report["summary"][:60] + ("..." if len(report["summary"]) > 60 else "")

        table_data.append({
            "scan_time": scan_time,
            "mode": mode,
            "dtc_count": dtc_count,
            "codes": codes_str,
            "summary": summary,
            "is_demo": report["is_demo"],
        })

    columns = [
        TableColumn(key="scan_time", header="Date/Time", width="160px"),
        TableColumn(key="mode", header="Mode", width="100px", format=lambda v, row: badge(label="DEMO" if row["is_demo"] else "LIVE", variant=BadgeVariant.WARNING if row["is_demo"] else BadgeVariant.SUCCESS, key=f"hist_mode_{row['scan_time']}")),
        TableColumn(key="dtc_count", header="DTCs Found", width="100px", align="center"),
        TableColumn(key="codes", header="Codes", format=lambda v: f'<code style="font-family: {FONT_FAMILY_MONO}; font-size: {FONT_SIZE_BODY_SM};">{v}</code>'),
        TableColumn(key="summary", header="Summary", format=lambda v: f'<span style="color: {TEXT_SECONDARY};">{v}</span>'),
    ]

    table(TableProps(
        columns=columns,
        data=table_data,
        key="diagnostic_history_table",
        empty_message="No diagnostic history",
        striped=True,
        hoverable=True,
    ))


# =============================================================================
# MAIN RENDER FUNCTION - RESPONSIVE GRID LAYOUT
# =============================================================================

def render_diagnostics():
    """Render the complete diagnostics page using the design system - FULLY RESPONSIVE."""
    init_diagnostics_session_state()

    obd = get_obd_service()
    db = get_database()

    # Get status for header
    status = obd.get_status()
    mode = status["mode"]
    conn_state = status["connection_state"]

    # Determine status badge
    if conn_state == "connected" and mode == "simulation":
        badge_class = "status-simulation"
        badge_text = "● SIMULATION MODE"
    elif conn_state == "connected":
        badge_class = "status-connected"
        badge_text = "● CONNECTED"
    elif conn_state == "error":
        badge_class = "status-error"
        badge_text = "● CONNECTION ERROR"
    else:
        badge_class = "status-disconnected"
        badge_text = "● DISCONNECTED"

    # Header using design system styling
    st.markdown(f"""
    <div style="
        background: linear-gradient(90deg, {SURFACE_PRIMARY} 0%, {SURFACE_SECONDARY} 100%);
        border: 1px solid {BORDER_DEFAULT};
        border-radius: {RADIUS_LG};
        padding: {SPACE_5} {SPACE_6};
        margin-bottom: {SPACE_6};
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: var(--i20-gap-field);
    ">
        <div>
            <h1 style="margin: 0; font-size: {FONT_SIZE_H1}; font-weight: {FONT_WEIGHT_H1}; color: {TEXT_PRIMARY};">Diagnostics</h1>
            <p style="margin: {SPACE_1} 0 0 0; font-size: {FONT_SIZE_BODY}; color: {TEXT_SECONDARY};">DTC Scanning · Code Analysis · AI Diagnosis · Rule Engine</p>
        </div>
        <div style="
            display: inline-flex;
            align-items: center;
            gap: {GAP_INLINE};
            padding: {SPACE_2} {SPACE_4};
            border-radius: {RADIUS_PILL};
            font-size: {FONT_SIZE_LABEL};
            font-weight: {FONT_WEIGHT_LABEL};
            text-transform: uppercase;
            letter-spacing: {LETTER_SPACING_LABEL};
            background: {ACCENT_PRIMARY}1a;
            color: {ACCENT_PRIMARY};
            border: 1px solid {ACCENT_PRIMARY};
        ">{badge_text}</div>
    </div>
    """, unsafe_allow_html=True)

    # Demo mode warning
    if mode == "simulation":
        alert("Demo Mode Active", "DTCs shown are simulated for demonstration only. They do not represent actual vehicle faults. Connect a real OBD-II adapter for live diagnostics.", variant=AlertVariant.WARNING)

    # Limitations info box
    alert("Scope Notice", "This module reads DTCs only. It does <strong>not</strong> clear codes, execute ECU commands, or perform actuator tests. For repairs, consult a qualified technician with proper diagnostic equipment.", variant=AlertVariant.INFO)

    # Main content - RESPONSIVE GRID LAYOUT
    # Uses auto-fit grid: stacks on mobile, 2-col on tablet, 3-col on desktop
    st.markdown(f"""
    <div class="i20-diagnostics-grid" style="
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
        gap: var(--i20-gap-section);
    ">
        <div class="i20-diagnostics-col-scan">
            {_render_diagnostics_col_scan_html(obd)}
        </div>
        <div class="i20-diagnostics-col-detail">
            {_render_diagnostics_col_detail_html()}
        </div>
        <div class="i20-diagnostics-col-ai">
            {_render_diagnostics_col_ai_html(obd, db)}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Render actual Streamlit components inside the grid structure
    _render_diagnostics_streamlit_components(obd, db)

    # History panel (full width)
    st.markdown(f"<div style='margin-top: {SPACE_6};'></div>", unsafe_allow_html=True)
    section_header("Scan History", icon="📜", level=2)
    render_history_panel(db)


def _render_diagnostics_col_scan_html(obd) -> str:
    """Render scan column as HTML for grid layout."""
    return """
    <div class="i20-panel-group">
        <h2 class="i20-h3" style="margin: 0 0 var(--i20-gap-field) 0; display: flex; align-items: center; gap: var(--i20-gap-inline);">
            <span>🔍</span> DTC Scanner
        </h2>
        <div class="i20-scan-panel-placeholder"></div>
    </div>
    """


def _render_diagnostics_col_detail_html() -> str:
    """Render detail column as HTML for grid layout."""
    return """
    <div class="i20-panel-group">
        <h2 class="i20-h3" style="margin: 0 0 var(--i20-gap-field) 0; display: flex; align-items: center; gap: var(--i20-gap-inline);">
            <span>🔍</span> Code Details
        </h2>
        <div class="i20-detail-panel-placeholder"></div>

        <h2 class="i20-h3" style="margin: var(--i20-gap-section) 0 var(--i20-gap-field) 0; display: flex; align-items: center; gap: var(--i20-gap-inline);">
            <span>📄</span> Generate Report
        </h2>
        <div class="i20-report-panel-placeholder"></div>
    </div>
    """


def _render_diagnostics_col_ai_html(obd, db) -> str:
    """Render AI/Rule column as HTML for grid layout."""
    return """
    <div class="i20-panel-group">
        <h2 class="i20-h3" style="margin: 0 0 var(--i20-gap-field) 0; display: flex; align-items: center; gap: var(--i20-gap-inline);">
            <span>🤖</span> AI Diagnosis
        </h2>
        <div class="i20-ai-panel-placeholder"></div>

        <h2 class="i20-h3" style="margin: var(--i20-gap-section) 0 var(--i20-gap-field) 0; display: flex; align-items: center; gap: var(--i20-gap-inline);">
            <span>⚙️</span> Rule Engine
        </h2>
        <div class="i20-rule-panel-placeholder"></div>
    </div>
    """


def _render_diagnostics_streamlit_components(obd, db):
    """Render the actual interactive Streamlit components."""
    # This uses a hybrid approach: CSS grid for layout, Streamlit for interactivity
    # We render the components in a way that respects the responsive grid

    # Column 1: Scan + DTC List
    # Column 2: Detail + Report
    # Column 3: AI + Rule Engine

    # Use Streamlit columns as a fallback for interactive elements
    # The CSS grid handles the visual layout
    pass


# Actually render the components using Streamlit columns for interactivity
# but with responsive CSS classes
def render_diagnostics():
    """Render the complete diagnostics page using the design system - FULLY RESPONSIVE."""
    init_diagnostics_session_state()

    obd = get_obd_service()
    db = get_database()

    # Get status for header
    status = obd.get_status()
    mode = status["mode"]
    conn_state = status["connection_state"]

    # Determine status badge
    if conn_state == "connected" and mode == "simulation":
        badge_text = "● SIMULATION MODE"
    elif conn_state == "connected":
        badge_text = "● CONNECTED"
    elif conn_state == "error":
        badge_text = "● CONNECTION ERROR"
    else:
        badge_text = "● DISCONNECTED"

    # Header using design system styling
    st.markdown(f"""
    <div style="
        background: linear-gradient(90deg, {SURFACE_PRIMARY} 0%, {SURFACE_SECONDARY} 100%);
        border: 1px solid {BORDER_DEFAULT};
        border-radius: {RADIUS_LG};
        padding: {SPACE_5} {SPACE_6};
        margin-bottom: {SPACE_6};
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: var(--i20-gap-field);
    ">
        <div>
            <h1 style="margin: 0; font-size: {FONT_SIZE_H1}; font-weight: {FONT_WEIGHT_H1}; color: {TEXT_PRIMARY};">Diagnostics</h1>
            <p style="margin: {SPACE_1} 0 0 0; font-size: {FONT_SIZE_BODY}; color: {TEXT_SECONDARY};">DTC Scanning · Code Analysis · AI Diagnosis · Rule Engine</p>
        </div>
        <div style="
            display: inline-flex;
            align-items: center;
            gap: {GAP_INLINE};
            padding: {SPACE_2} {SPACE_4};
            border-radius: {RADIUS_PILL};
            font-size: {FONT_SIZE_LABEL};
            font-weight: {FONT_WEIGHT_LABEL};
            text-transform: uppercase;
            letter-spacing: {LETTER_SPACING_LABEL};
            background: {ACCENT_PRIMARY}1a;
            color: {ACCENT_PRIMARY};
            border: 1px solid {ACCENT_PRIMARY};
        ">{badge_text}</div>
    </div>
    """, unsafe_allow_html=True)

    # Demo mode warning
    if mode == "simulation":
        alert("Demo Mode Active", "DTCs shown are simulated for demonstration only. They do not represent actual vehicle faults. Connect a real OBD-II adapter for live diagnostics.", variant=AlertVariant.WARNING)

    # Limitations info box
    alert("Scope Notice", "This module reads DTCs only. It does <strong>not</strong> clear codes, execute ECU commands, or perform actuator tests. For repairs, consult a qualified technician with proper diagnostic equipment.", variant=AlertVariant.INFO)

    # Main content - RESPONSIVE: Use CSS Grid via HTML wrapper, then Streamlit columns for interactivity
    # We use a 3-column layout that stacks on mobile via CSS
    st.markdown("""
    <div class="i20-diagnostics-main" style="
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
        gap: var(--i20-gap-section);
    ">
    """, unsafe_allow_html=True)

    # Column 1: Scan Panel + DTC List
    st.markdown('<div class="i20-diagnostics-col">', unsafe_allow_html=True)
    section_header("DTC Scanner", icon="🔍", level=3)
    render_scan_panel(obd)

    st.markdown(f"<div style='margin-top: {SPACE_6};'></div>", unsafe_allow_html=True)
    section_header("DTC Details", icon="📋", level=3)
    render_dtc_list()
    st.markdown('</div>', unsafe_allow_html=True)

    # Column 2: DTC Detail + Report
    st.markdown('<div class="i20-diagnostics-col">', unsafe_allow_html=True)
    section_header("Code Details", icon="🔍", level=3)
    render_dtc_detail()

    st.markdown(f"<div style='margin-top: {SPACE_6};'></div>", unsafe_allow_html=True)
    section_header("Generate Report", icon="📄", level=3)
    render_report_panel(obd, db)
    st.markdown('</div>', unsafe_allow_html=True)

    # Column 3: AI Diagnosis + Rule Engine
    st.markdown('<div class="i20-diagnostics-col">', unsafe_allow_html=True)
    section_header("AI Diagnosis", icon="🤖", level=3)
    render_ai_diagnosis_panel(obd, db)

    st.markdown(f"<div style='margin-top: {SPACE_6};'></div>", unsafe_allow_html=True)
    if RULE_ENGINE_AVAILABLE:
        section_header("Rule Engine", icon="⚙️", level=3)
        render_rule_engine_panel(obd, db)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # History panel (full width)
    st.markdown(f"<div style='margin-top: {SPACE_6};'></div>", unsafe_allow_html=True)
    section_header("Scan History", icon="📜", level=2)
    render_history_panel(db)


# Export the main function
__all__ = ["render_diagnostics", "DiagnosticCode", "get_demo_dtcs"]
"""
i20 AI Garage - Reports Module

Streamlit UI for generating and viewing professional reports.
Integrates with the report generation engine to provide a complete
reporting workflow with HTML preview and PDF export.

Redesigned using Phase 6 Stage 3 Design System.
"""

import streamlit as st
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import base64
import io

from services.report_models import (
    ReportType,
    ReportFormat,
    DataSource,
)
from services.report_generator import ReportGenerator

# Design System Imports
from components.ui import (
    # Styles
    inject_global_css,
    initialize_layout,
    # Layout
    page_header,
    section_header,
    card_container,
    grid_container,
    responsive_container,
    AUTO_FIT_CARD_CSS,
    AUTO_FIT_METRIC_CSS,
    CHART_GRID_CSS,
    # Components
    ButtonVariant,
    ButtonSize,
    button_primary,
    button_secondary,
    button_ghost,
    button_danger,
    BadgeVariant,
    badge,
    AlertVariant,
    alert,
    CardProps,
    card,
    card_simple,
    FormFieldProps,
    text_input,
    selectbox,
    EmptyStateProps,
    empty_state,
    skeleton_card,
    spinner,
    # Tokens
    ACCENT_PRIMARY,
    STATUS_SUCCESS,
    STATUS_WARNING,
    STATUS_CRITICAL,
    STATUS_INFO,
    STATUS_NEUTRAL,
    DIAG_CRITICAL,
    DIAG_MAJOR,
    DIAG_MINOR,
    DIAG_INFO,
    DATASOURCE_REAL,
    DATASOURCE_SIMULATION,
    DATASOURCE_AI,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    TEXT_ON_ACCENT,
    SURFACE_PRIMARY,
    SURFACE_SECONDARY,
    SURFACE_INTERACTIVE,
    BORDER_DEFAULT,
    BORDER_SUBTLE,
    BORDER_FOCUS,
    SPACE_1, SPACE_2, SPACE_3, SPACE_4, SPACE_5, SPACE_6,
    GAP_INLINE, GAP_FIELD, GAP_CARD_GRID, GAP_SECTION,
    RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_PILL,
    SHADOW_SM, SHADOW_MD, SHADOW_FOCUS,
    FONT_SIZE_LABEL, FONT_SIZE_BODY, FONT_SIZE_BODY_SM, FONT_SIZE_CAPTION,
    FONT_SIZE_H1, FONT_SIZE_H2, FONT_SIZE_H3,
    BUTTON_FONT_WEIGHT,
    TRANSITION_FAST, TRANSITION_NORMAL,
)


# =============================================================================
# REPORT PAGE CONFIGURATION
# =============================================================================

REPORT_TYPES = [
    {
        "id": ReportType.DIAGNOSTIC,
        "title": "Comprehensive Diagnostic Report",
        "description": "Full diagnostic analysis including DTCs, AI diagnosis, rule engine findings, telemetry, and recommendations",
        "icon": "🔍",
        "requires_session": True,
        "requires_diagnosis": True,
        "color": ACCENT_PRIMARY,
    },
    {
        "id": ReportType.VEHICLE_HEALTH,
        "title": "Vehicle Health Report",
        "description": "Overall vehicle health assessment with component status, maintenance history, and safety observations",
        "icon": "🏥",
        "requires_session": False,
        "requires_diagnosis": False,
        "color": STATUS_SUCCESS,
    },
    {
        "id": ReportType.PERFORMANCE,
        "title": "Performance Report",
        "description": "Driving session performance metrics, sensor statistics, and time-series data analysis",
        "icon": "📊",
        "requires_session": True,
        "requires_diagnosis": False,
        "color": STATUS_INFO,
    },
    {
        "id": ReportType.MAINTENANCE,
        "title": "Maintenance Report",
        "description": "Complete maintenance history, upcoming/overdue items, cost summaries, and manufacturer intervals",
        "icon": "🔧",
        "requires_session": False,
        "requires_diagnosis": False,
        "color": STATUS_WARNING,
    },
]

FORMAT_OPTIONS = [
    {"id": ReportFormat.HTML, "label": "HTML (Interactive)", "description": "View in browser with interactive charts and styling"},
    {"id": ReportFormat.PDF, "label": "PDF (Print-Ready)", "description": "Professional PDF for printing and archiving"},
]


def _get_datasource_badge(source: Optional[str]) -> str:
    """Get badge HTML for data source."""
    if not source:
        return badge("UNKNOWN", variant=BadgeVariant.NEUTRAL)
    source_lower = source.lower()
    if source_lower == "real":
        return badge("REAL DATA", variant=BadgeVariant.SUCCESS)
    elif source_lower == "simulation":
        return badge("SIMULATION", variant=BadgeVariant.WARNING)
    elif source_lower == "ai":
        return badge("AI", variant=BadgeVariant.INFO)
    return badge(source.upper(), variant=BadgeVariant.NEUTRAL)


def _get_severity_badge(severity: str) -> str:
    """Get badge HTML for severity level."""
    sev_lower = severity.lower()
    if sev_lower in ("critical", "high"):
        return badge(severity.upper(), variant=BadgeVariant.CRITICAL)
    elif sev_lower in ("major", "medium"):
        return badge(severity.upper(), variant=BadgeVariant.WARNING)
    elif sev_lower in ("minor", "low"):
        return badge(severity.upper(), variant=BadgeVariant.INFO)
    elif sev_lower in ("info", "informational"):
        return badge(severity.upper(), variant=BadgeVariant.INFO)
    return badge(severity.upper(), variant=BadgeVariant.NEUTRAL)


def _get_status_badge(status: str) -> str:
    """Get badge HTML for component status."""
    status_lower = status.lower().replace(" ", "_")
    if status_lower in ("normal", "healthy", "ok", "pass"):
        return badge(status.replace("_", " ").title(), variant=BadgeVariant.SUCCESS)
    elif status_lower in ("attention_recommended", "warning", "attention"):
        return badge(status.replace("_", " ").title(), variant=BadgeVariant.WARNING)
    elif status_lower in ("critical_finding", "critical", "fail"):
        return badge(status.replace("_", " ").title(), variant=BadgeVariant.CRITICAL)
    elif status_lower in ("insufficient_data", "unknown"):
        return badge(status.replace("_", " ").title(), variant=BadgeVariant.NEUTRAL)
    return badge(status.replace("_", " ").title(), variant=BadgeVariant.NEUTRAL)


def render_reports_page():
    """Main entry point for the Reports page."""
    st.set_page_config(
        page_title="Reports - i20 AI Garage",
        page_icon="📋",
        layout="wide",
    )

    # Initialize Design System
    initialize_layout()

    # Initialize session state
    if "report_generator" not in st.session_state:
        st.session_state.report_generator = ReportGenerator()
    if "generated_report" not in st.session_state:
        st.session_state.generated_report = None
    if "report_html" not in st.session_state:
        st.session_state.report_html = None
    if "report_pdf" not in st.session_state:
        st.session_state.report_pdf = None
    if "batch_results" not in st.session_state:
        st.session_state.batch_results = None
    if "report_config" not in st.session_state:
        st.session_state.report_config = {}

    generator = st.session_state.report_generator

    # Page Header using Design System
    page_header(
        title="Professional Reports",
        subtitle="Generate comprehensive, professional automotive reports for your Hyundai i20. Choose from four report types with interactive HTML preview and print-ready PDF export.",
        icon="📋",
    )

    # Sidebar for report configuration
    with st.sidebar:
        render_report_config_sidebar(generator)

    # Main content area - 3 tabs
    tab1, tab2, tab3 = st.tabs(["📝 Generate Report", "👁️ Preview", "💾 Download"])

    with tab1:
        render_generate_tab(generator)

    with tab2:
        render_preview_tab()

    with tab3:
        render_download_tab()


def render_report_config_sidebar(generator: ReportGenerator):
    """Render sidebar configuration for report generation using Design System components."""
    # Report Type Selection
    section_header("Report Type", "Select the type of report to generate")

    report_type = selectbox(
        "Select Report Type",
        options=[rt["id"] for rt in REPORT_TYPES],
        format_func=lambda x: next(rt["title"] for rt in REPORT_TYPES if rt["id"] == x),
        index=0,
        key="report_type_select",
        label="Report Type",
    )

    # Show description and icon
    rt_info = next(rt for rt in REPORT_TYPES if rt["id"] == report_type)
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: {GAP_INLINE}; padding: {SPACE_3}; background: {SURFACE_SECONDARY}; border-radius: {RADIUS_MD}; border: 1px solid {BORDER_SUBTLE}; margin-bottom: {SPACE_4};">
        <span style="font-size: 2rem;">{rt_info['icon']}</span>
        <div>
            <div style="font-weight: {BUTTON_FONT_WEIGHT}; color: {TEXT_PRIMARY};">{rt_info['title']}</div>
            <div style="font-size: {FONT_SIZE_CAPTION}; color: {TEXT_MUTED};">{rt_info['description']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Format Selection
    section_header("Output Format", "Choose the output format for the report")

    format_type = st.radio(
        "Select Format",
        options=[fo["id"] for fo in FORMAT_OPTIONS],
        format_func=lambda x: next(fo["label"] for fo in FORMAT_OPTIONS if fo["id"] == x),
        index=0,
        key="format_type_select",
    )

    # Data Source Options
    section_header("Data Source", "Configure session and diagnosis data sources")
    rt_info = next(rt for rt in REPORT_TYPES if rt["id"] == report_type)

    selected_session = None
    selected_diagnosis = None

    if rt_info["requires_session"]:
        sessions = generator.get_available_sessions()
        if sessions:
            session_options = ["Use Simulation Data"] + [
                f"{s['session_name']} ({s['session_id'][:8]}) - {s['scenario']}"
                for s in sessions
            ]
            session_idx = st.selectbox(
                "OBD Session",
                options=range(len(session_options)),
                format_func=lambda i: session_options[i],
                key="session_select",
            )
            selected_session = None if session_idx == 0 else sessions[session_idx - 1]["session_id"]
            session_badge = "REAL DATA" if selected_session else "SIMULATION"
            badge_variant = BadgeVariant.SUCCESS if selected_session else BadgeVariant.WARNING
            st.markdown(f"Selected: {badge(session_badge, variant=badge_variant)}", unsafe_allow_html=True)
        else:
            alert("No OBD sessions found. Using simulation data.", variant=AlertVariant.WARNING)
            selected_session = None

        if rt_info["requires_diagnosis"]:
            diagnoses = generator.get_available_diagnoses()
            if diagnoses:
                diagnosis_options = ["Latest/None"] + [
                    f"{d['diagnosis_id'][:8]} - {d['severity']} ({d['confidence']:.0%})"
                    for d in diagnoses
                ]
                diag_idx = st.selectbox(
                    "AI Diagnosis",
                    options=range(len(diagnosis_options)),
                    format_func=lambda i: diagnosis_options[i],
                    key="diagnosis_select",
                )
                selected_diagnosis = None if diag_idx == 0 else diagnoses[diag_idx - 1]["diagnosis_id"]
            else:
                alert("No AI diagnoses found.", variant=AlertVariant.WARNING)
                selected_diagnosis = None
        else:
            selected_diagnosis = None
    else:
        selected_session = None
        selected_diagnosis = None
        alert("This report type uses current vehicle data and does not require a specific session.", variant=AlertVariant.INFO)

    # Vehicle Info Override (Advanced)
    with st.expander("🔧 Vehicle Info (Advanced)", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            vehicle_make = text_input("Make", value="Hyundai", key="vehicle_make", label="Make")
            vehicle_model = text_input("Model", value="i20", key="vehicle_model", label="Model")
            vehicle_year = st.number_input("Year", value=2023, min_value=2000, max_value=2030, key="vehicle_year")
            vehicle_variant = text_input("Variant", value="Asta", key="vehicle_variant", label="Variant")
        with col2:
            vehicle_engine = text_input("Engine", value="1.2L Kappa Petrol", key="vehicle_engine", label="Engine")
            vehicle_transmission = selectbox(
                "Transmission",
                options=["Manual", "Automatic", "CVT"],
                index=0,
                key="vehicle_transmission",
                label="Transmission",
            )
            vehicle_fuel = selectbox(
                "Fuel Type",
                options=["Petrol", "Diesel", "CNG", "Electric"],
                index=0,
                key="vehicle_fuel",
                label="Fuel Type",
            )
            vehicle_odometer = st.number_input("Odometer (km)", value=0, min_value=0, key="vehicle_odometer")
        vehicle_vin = text_input("VIN (optional)", value="", key="vehicle_vin", label="VIN")

    # Store config in session state
    st.session_state.report_config = {
        "report_type": report_type,
        "format_type": format_type,
        "session_id": selected_session,
        "diagnosis_id": selected_diagnosis,
        "vehicle_override": {
            "make": vehicle_make,
            "model": vehicle_model,
            "year": vehicle_year,
            "variant": vehicle_variant,
            "engine": vehicle_engine,
            "transmission": vehicle_transmission,
            "fuel_type": vehicle_fuel,
            "odometer_km": vehicle_odometer if vehicle_odometer > 0 else None,
            "vin": vehicle_vin if vehicle_vin else None,
        },
    }


def render_generate_tab(generator: ReportGenerator):
    """Render the report generation tab using Design System with B1.13 live region."""
    # Live region for report generation progress announcements (B1.13)
    report_live_region_id = "report-gen-live"
    st.markdown(f'<div id="{report_live_region_id}" class="i20-live-region i20-visually-hidden" aria-live="polite" aria-atomic="true" aria-label="Report generation status"></div>', unsafe_allow_html=True)

    section_header("Generate Report", "Configure and generate your professional report")

    config = st.session_state.get("report_config", {})
    report_type = config.get("report_type")
    format_type = config.get("format_type")
    session_id = config.get("session_id")
    diagnosis_id = config.get("diagnosis_id")
    vehicle_override = config.get("vehicle_override", {})

    if not report_type:
        alert("Please select a report type from the sidebar.", variant=AlertVariant.WARNING)
        return

    # Show summary of what will be generated
    rt_info = next(rt for rt in REPORT_TYPES if rt["id"] == report_type)
    fo_info = next(fo for fo in FORMAT_OPTIONS if fo["id"] == format_type)

    # Summary card
    st.markdown(f"""
    <div class="i20-card" style="padding: {SPACE_4}; margin-bottom: {SPACE_4}; background: {SURFACE_PRIMARY}; border: 1px solid {BORDER_DEFAULT}; border-radius: {RADIUS_MD};">
        <div style="display: flex; align-items: center; gap: {GAP_INLINE}; margin-bottom: {SPACE_3};">
            <span style="font-size: 2rem;">{rt_info['icon']}</span>
            <div>
                <div style="font-size: {FONT_SIZE_H3}; font-weight: {BUTTON_FONT_WEIGHT}; color: {TEXT_PRIMARY};">{rt_info['title']}</div>
                <div style="font-size: {FONT_SIZE_BODY_SM}; color: {TEXT_SECONDARY};">{fo_info['label']}</div>
            </div>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: {GAP_FIELD};">
            <div>
                <div style="font-size: {FONT_SIZE_LABEL}; font-weight: {BUTTON_FONT_WEIGHT}; color: {TEXT_MUTED}; text-transform: uppercase; letter-spacing: 0.05em;">Session</div>
                <div style="font-size: {FONT_SIZE_BODY}; color: {TEXT_PRIMARY};">{session_id[:8] + '...' if session_id else 'Simulation'}</div>
            </div>
            <div>
                <div style="font-size: {FONT_SIZE_LABEL}; font-weight: {BUTTON_FONT_WEIGHT}; color: {TEXT_MUTED}; text-transform: uppercase; letter-spacing: 0.05em;">Diagnosis</div>
                <div style="font-size: {FONT_SIZE_BODY}; color: {TEXT_PRIMARY};">{diagnosis_id[:8] + '...' if diagnosis_id else 'Simulation'}</div>
            </div>
            <div>
                <div style="font-size: {FONT_SIZE_LABEL}; font-weight: {BUTTON_FONT_WEIGHT}; color: {TEXT_MUTED}; text-transform: uppercase; letter-spacing: 0.05em;">Vehicle</div>
                <div style="font-size: {FONT_SIZE_BODY}; color: {TEXT_PRIMARY};">{vehicle_override.get('year', '2023')} {vehicle_override.get('make', 'Hyundai')} {vehicle_override.get('model', 'i20')} {vehicle_override.get('variant', 'Asta')}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Generate button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if button_primary(
            f"🚀 Generate {rt_info['title']}",
            key="generate_report_btn",
            use_container_width=True,
        ):
            generate_report_action(generator, report_type, format_type, session_id, diagnosis_id, vehicle_override, report_live_region_id)

    # Batch generation
    st.divider()
    section_header("Batch Generation", "Generate all four report types at once")

    if button_secondary(
        "📦 Generate All Reports",
        key="generate_all_reports_btn",
        use_container_width=True,
    ):
        generate_all_reports_action(generator, format_type, vehicle_override, report_live_region_id)


def generate_report_action(
    generator: ReportGenerator,
    report_type: ReportType,
    format_type: ReportFormat,
    session_id: Optional[str],
    diagnosis_id: Optional[str],
    vehicle_override: Dict[str, Any],
    live_region_id: str = "report-gen-live",
):
    """Execute report generation with B1.13 live region announcements."""
    # Announce generation start
    announce_script = f'''
    <script>
    (function() {{
        const region = document.getElementById('{live_region_id}');
        if (region) {{
            region.textContent = 'Generating {report_type.value.replace("_", " ").title()} report...';
        }}
    }})();
    </script>
    '''
    st.markdown(announce_script, unsafe_allow_html=True)

    with spinner(f"Generating {report_type.value.replace('_', ' ').title()} Report..."):
        try:
            result = generator.generate_report(
                report_type=report_type,
                format_type=format_type,
                session_id=session_id,
                diagnosis_id=diagnosis_id,
                vehicle_override=vehicle_override,
            )

            if format_type == ReportFormat.HTML:
                st.session_state.report_html = result
                st.session_state.report_pdf = None
            else:
                st.session_state.report_pdf = result
                st.session_state.report_html = None

            st.session_state.generated_report = {
                "type": report_type,
                "format": format_type,
                "timestamp": datetime.now(),
                "result": result,
            }

            alert(f"✅ Report generated successfully!", variant=AlertVariant.SUCCESS)
            st.balloons()

            # Announce completion
            announce_script = f'''
            <script>
            (function() {{
                const region = document.getElementById('{live_region_id}');
                if (region) {{
                    region.textContent = '{report_type.value.replace("_", " ").title()} report generated successfully';
                }}
            }})();
            </script>
            '''
            st.markdown(announce_script, unsafe_allow_html=True)

        except Exception as e:
            alert(f"❌ Error generating report: {str(e)}", variant=AlertVariant.CRITICAL)
            import traceback
            st.code(traceback.format_exc())

            # Announce error
            announce_script = f'''
            <script>
            (function() {{
                const region = document.getElementById('{live_region_id}');
                if (region) {{
                    region.textContent = 'Report generation failed';
                }}
            }})();
            </script>
            '''
            st.markdown(announce_script, unsafe_allow_html=True)


def generate_all_reports_action(
    generator: ReportGenerator,
    format_type: ReportFormat,
    vehicle_override: Dict[str, Any],
    live_region_id: str = "report-gen-live",
):
    """Generate all report types with B1.13 live region announcements."""
    # Announce generation start
    announce_script = f'''
    <script>
    (function() {{
        const region = document.getElementById('{live_region_id}');
        if (region) {{
            region.textContent = 'Generating all reports...';
        }}
    }})();
    </script>
    '''
    st.markdown(announce_script, unsafe_allow_html=True)

    with spinner("Generating all reports..."):
        try:
            results = generator.generate_all_reports(
                format_type=format_type,
                vehicle_override=vehicle_override,
            )

            st.session_state.batch_results = results
            alert(f"✅ All {len(results)} reports generated successfully!", variant=AlertVariant.SUCCESS)
            st.balloons()

            # Announce completion
            announce_script = f'''
            <script>
            (function() {{
                const region = document.getElementById('{live_region_id}');
                if (region) {{
                    region.textContent = 'All {len(results)} reports generated successfully';
                }}
            }})();
            </script>
            '''
            st.markdown(announce_script, unsafe_allow_html=True)

            # Display results
            for rtype, result in results.items():
                rt_info = next(rt for rt in REPORT_TYPES if rt["id"] == rtype)
                if format_type == ReportFormat.HTML:
                    if isinstance(result, str):
                        st.markdown(f"{rt_info['icon']} **{rt_info['title']}** - HTML generated ({len(result):,} chars)")
                else:
                    if isinstance(result, bytes):
                        st.markdown(f"{rt_info['icon']} **{rt_info['title']}** - PDF generated ({len(result):,} bytes)")

        except Exception as e:
            alert(f"❌ Error generating reports: {str(e)}", variant=AlertVariant.CRITICAL)
            import traceback
            st.code(traceback.format_exc())

            # Announce error
            announce_script = f'''
            <script>
            (function() {{
                const region = document.getElementById('{live_region_id}');
                if (region) {{
                    region.textContent = 'Batch report generation failed';
                }}
            }})();
            </script>
            '''
            st.markdown(announce_script, unsafe_allow_html=True)


def render_preview_tab():
    """Render the HTML preview tab using Design System."""
    section_header("Report Preview", "Preview your generated report before downloading")

    if st.session_state.report_html:
        section_header("HTML Preview", level=3)
        alert("This is a preview of the generated HTML report. Interactive elements may not work in the iframe.", variant=AlertVariant.INFO)

        # Create a download link for the HTML
        html_content = st.session_state.report_html
        b64 = base64.b64encode(html_content.encode()).decode()
        href = f'<a href="data:text/html;base64,{b64}" download="report.html" target="_blank" style="display: inline-block; margin-bottom: {SPACE_3}; padding: {SPACE_2} {SPACE_4}; background: {ACCENT_PRIMARY}; color: {TEXT_ON_ACCENT}; border-radius: {RADIUS_MD}; text-decoration: none; font-weight: {BUTTON_FONT_WEIGHT};">📥 Open Full HTML in New Tab</a>'
        st.markdown(href, unsafe_allow_html=True)

        # Preview in iframe (responsive height)
        # Use CSS to make iframe responsive - minimum 500px, max 90vh
        st.markdown(f"""
        <style>
        .i20-report-iframe {{
            width: 100%;
            min-height: 500px;
            max-height: 90vh;
            height: 800px;
            border: 1px solid {BORDER_DEFAULT};
            border-radius: {RADIUS_MD};
            background: {SURFACE_PRIMARY};
        }}
        @media (max-width: 767px) {{
            .i20-report-iframe {{
                min-height: 400px;
                max-height: 80vh;
            }}
        }}
        </style>
        """, unsafe_allow_html=True)
        st.components.v1.html(html_content, height=800, scrolling=True)

    elif st.session_state.report_pdf:
        section_header("PDF Report Generated", level=3)
        alert("PDF preview is not available in-browser. Use the Download tab to save and open the PDF.", variant=AlertVariant.INFO)

        # Show PDF info
        pdf_bytes = st.session_state.report_pdf
        st.markdown(f"""
        <div class="i20-card" style="padding: {SPACE_4}; background: {SURFACE_PRIMARY}; border: 1px solid {BORDER_DEFAULT}; border-radius: {RADIUS_MD};">
            <div style="font-size: {FONT_SIZE_LABEL}; font-weight: {BUTTON_FONT_WEIGHT}; color: {TEXT_MUTED}; text-transform: uppercase;">PDF Size</div>
            <div style="font-size: {FONT_SIZE_BODY}; color: {TEXT_PRIMARY};">{len(pdf_bytes):,} bytes ({len(pdf_bytes)/1024:.1f} KB)</div>
        </div>
        """, unsafe_allow_html=True)

    elif st.session_state.get("batch_results"):
        section_header("Batch Generation Results", level=3)
        results = st.session_state.batch_results
        # Use responsive grid for batch results
        st.markdown(f'<div style="{AUTO_FIT_CARD_CSS}">', unsafe_allow_html=True)
        for rtype, result in results.items():
            rt_info = next(rt for rt in REPORT_TYPES if rt["id"] == rtype)
            if isinstance(result, str):
                content = f"""
                <div style="font-weight: {BUTTON_FONT_WEIGHT}; color: {TEXT_PRIMARY}; margin-bottom: {SPACE_2};">{rt_info['icon']} {rt_info['title']}</div>
                <div style="font-size: {FONT_SIZE_BODY_SM}; color: {TEXT_SECONDARY}; margin-bottom: {SPACE_2};">HTML: {len(result):,} characters</div>
                """
                b64 = base64.b64encode(result.encode()).decode()
                href = f'<a href="data:text/html;base64,{b64}" download="{rtype.value}_report.html" target="_blank" style="display: inline-block; padding: {SPACE_1} {SPACE_3}; background: {ACCENT_PRIMARY}; color: {TEXT_ON_ACCENT}; border-radius: {RADIUS_SM}; text-decoration: none; font-size: {FONT_SIZE_BODY_SM}; font-weight: {BUTTON_FONT_WEIGHT};">Open in New Tab</a>'
                content += href
            elif isinstance(result, bytes):
                content = f"""
                <div style="font-weight: {BUTTON_FONT_WEIGHT}; color: {TEXT_PRIMARY}; margin-bottom: {SPACE_2};">{rt_info['icon']} {rt_info['title']}</div>
                <div style="font-size: {FONT_SIZE_BODY_SM}; color: {TEXT_SECONDARY};">PDF: {len(result):,} bytes ({len(result)/1024:.1f} KB)</div>
                """
            card_simple(content=content, elevated=True, padding="md")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        empty_state(
            icon="📋",
            title="No Report Generated",
            description="Generate a report from the **Generate Report** tab to see a preview here.",
            action_label="Go to Generate",
            action_key="preview_goto_generate",
        )


def render_download_tab():
    """Render the download tab using Design System."""
    section_header("Download Reports", "Download your generated reports in HTML or PDF format")

    if st.session_state.report_html:
        section_header("Current Report (HTML)", level=3)
        html_content = st.session_state.report_html
        report_info = st.session_state.generated_report

        filename = f"{report_info['type'].value}_report_{report_info['timestamp'].strftime('%Y%m%d_%H%M%S')}.html"

        # Report metadata card using design system card_simple
        card_simple(
            title="Report Metadata",
            content=f"""
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: {GAP_FIELD};">
                <div>
                    <div style="font-size: {FONT_SIZE_LABEL}; font-weight: {BUTTON_FONT_WEIGHT}; color: {TEXT_MUTED}; text-transform: uppercase;">Report Type</div>
                    <div style="font-size: {FONT_SIZE_BODY}; color: {TEXT_PRIMARY};">{report_info['type'].value.replace('_', ' ').title()}</div>
                </div>
                <div>
                    <div style="font-size: {FONT_SIZE_LABEL}; font-weight: {BUTTON_FONT_WEIGHT}; color: {TEXT_MUTED}; text-transform: uppercase;">Format</div>
                    <div style="font-size: {FONT_SIZE_BODY}; color: {TEXT_PRIMARY};">HTML</div>
                </div>
                <div>
                    <div style="font-size: {FONT_SIZE_LABEL}; font-weight: {BUTTON_FONT_WEIGHT}; color: {TEXT_MUTED}; text-transform: uppercase;">Generated</div>
                    <div style="font-size: {FONT_SIZE_BODY}; color: {TEXT_PRIMARY};">{report_info['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</div>
                </div>
                <div>
                    <div style="font-size: {FONT_SIZE_LABEL}; font-weight: {BUTTON_FONT_WEIGHT}; color: {TEXT_MUTED}; text-transform: uppercase;">Size</div>
                    <div style="font-size: {FONT_SIZE_BODY}; color: {TEXT_PRIMARY};">{len(html_content):,} chars ({len(html_content)/1024:.1f} KB)</div>
                </div>
            </div>
            """,
            footer="",
            elevated=False,
            bordered=True,
            padding="md",
        )

        # Download button
        st.download_button(
            label="📥 Download HTML Report",
            data=html_content,
            file_name=filename,
            mime="text/html",
            use_container_width=True,
        )

        # Also offer PDF conversion
        st.markdown(f"<div style='margin-top: {SPACE_4};'></div>", unsafe_allow_html=True)
        if button_secondary(
            "🔄 Also Generate PDF Version",
            key="generate_pdf_version_btn",
            use_container_width=True,
        ):
            generate_pdf_version(report_info)

    elif st.session_state.report_pdf:
        section_header("Current Report (PDF)", level=3)
        pdf_bytes = st.session_state.report_pdf
        report_info = st.session_state.generated_report

        filename = f"{report_info['type'].value}_report_{report_info['timestamp'].strftime('%Y%m%d_%H%M%S')}.pdf"

        # Report metadata card using design system card_simple
        card_simple(
            title="Report Metadata",
            content=f"""
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: {GAP_FIELD};">
                <div>
                    <div style="font-size: {FONT_SIZE_LABEL}; font-weight: {BUTTON_FONT_WEIGHT}; color: {TEXT_MUTED}; text-transform: uppercase;">Report Type</div>
                    <div style="font-size: {FONT_SIZE_BODY}; color: {TEXT_PRIMARY};">{report_info['type'].value.replace('_', ' ').title()}</div>
                </div>
                <div>
                    <div style="font-size: {FONT_SIZE_LABEL}; font-weight: {BUTTON_FONT_WEIGHT}; color: {TEXT_MUTED}; text-transform: uppercase;">Format</div>
                    <div style="font-size: {FONT_SIZE_BODY}; color: {TEXT_PRIMARY};">PDF</div>
                </div>
                <div>
                    <div style="font-size: {FONT_SIZE_LABEL}; font-weight: {BUTTON_FONT_WEIGHT}; color: {TEXT_MUTED}; text-transform: uppercase;">Generated</div>
                    <div style="font-size: {FONT_SIZE_BODY}; color: {TEXT_PRIMARY};">{report_info['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</div>
                </div>
                <div>
                    <div style="font-size: {FONT_SIZE_LABEL}; font-weight: {BUTTON_FONT_WEIGHT}; color: {TEXT_MUTED}; text-transform: uppercase;">Size</div>
                    <div style="font-size: {FONT_SIZE_BODY}; color: {TEXT_PRIMARY};">{len(pdf_bytes):,} bytes ({len(pdf_bytes)/1024:.1f} KB)</div>
                </div>
            </div>
            """,
            footer="",
            elevated=False,
            bordered=True,
            padding="md",
        )

        st.download_button(
            label="📥 Download PDF Report",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            use_container_width=True,
        )

    elif st.session_state.get("batch_results"):
        section_header("Batch Generated Reports", level=3)
        results = st.session_state.batch_results

        # Use responsive grid for batch download buttons
        st.markdown(f'<div style="{AUTO_FIT_METRIC_CSS}">', unsafe_allow_html=True)
        for rtype, result in results.items():
            rt_info = next(rt for rt in REPORT_TYPES if rt["id"] == rtype)
            if isinstance(result, str):
                filename = f"{rtype.value}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                st.markdown(f"**{rt_info['icon']} {rt_info['title']}**")
                st.download_button(
                    label="📥 Download HTML",
                    data=result,
                    file_name=filename,
                    mime="text/html",
                    key=f"dl_html_{rtype.value}",
                    use_container_width=True,
                )
            elif isinstance(result, bytes):
                filename = f"{rtype.value}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                st.markdown(f"**{rt_info['icon']} {rt_info['title']}**")
                st.download_button(
                    label="📥 Download PDF",
                    data=result,
                    file_name=filename,
                    mime="application/pdf",
                    key=f"dl_pdf_{rtype.value}",
                    use_container_width=True,
                )
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        empty_state(
            icon="💾",
            title="No Reports to Download",
            description="Generate a report from the **Generate Report** tab to enable downloads.",
            action_label="Go to Generate",
            action_key="download_goto_generate",
        )

    # Saved reports section
    st.divider()
    render_saved_reports_section()


def generate_pdf_version(report_info: Dict[str, Any]):
    """Generate PDF version of an already generated HTML report."""
    generator = ReportGenerator()
    config = st.session_state.get("report_config", {})

    with spinner("Generating PDF version..."):
        try:
            result = generator.generate_report(
                report_type=report_info["type"],
                format_type=ReportFormat.PDF,
                session_id=config.get("session_id"),
                diagnosis_id=config.get("diagnosis_id"),
                vehicle_override=config.get("vehicle_override", {}),
            )

            if isinstance(result, bytes):
                st.session_state.report_pdf = result
                alert("✅ PDF generated! Refresh to see download option.", variant=AlertVariant.SUCCESS)
                st.rerun()
            elif isinstance(result, Path):
                pdf_bytes = result.read_bytes()
                st.session_state.report_pdf = pdf_bytes
                alert("✅ PDF generated! Refresh to see download option.", variant=AlertVariant.SUCCESS)
                st.rerun()

        except Exception as e:
            alert(f"❌ Error generating PDF: {str(e)}", variant=AlertVariant.CRITICAL)


def render_saved_reports_section():
    """Render section for managing saved reports using Design System."""
    section_header("Saved Reports", "Previously generated reports stored in the reports/ directory")

    reports_dir = Path("reports")
    if reports_dir.exists():
        html_files = sorted(reports_dir.glob("*.html"), key=lambda f: f.stat().st_mtime, reverse=True)
        pdf_files = sorted(reports_dir.glob("*.pdf"), key=lambda f: f.stat().st_mtime, reverse=True)

        if html_files or pdf_files:
            # Use tabs for HTML and PDF reports instead of columns for better mobile UX
            html_tab, pdf_tab = st.tabs(["📄 HTML Reports", "📄 PDF Reports"])

            with html_tab:
                if html_files:
                    # Responsive grid for HTML reports
                    st.markdown(f'<div style="{AUTO_FIT_CARD_CSS}">', unsafe_allow_html=True)
                    for f in html_files[:10]:
                        stat = f.stat()
                        size_kb = stat.st_size / 1024
                        mtime = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
                        with open(f, "rb") as fp:
                            file_data = fp.read()
                        content = f"""
                        <div style="display: flex; align-items: center; gap: {GAP_INLINE}; margin-bottom: {SPACE_3};">
                            <span style="font-size: 1.5rem;">📄</span>
                            <div style="flex: 1;">
                                <div style="font-weight: {BUTTON_FONT_WEIGHT}; color: {TEXT_PRIMARY};">{f.name}</div>
                                <div style="font-size: {FONT_SIZE_CAPTION}; color: {TEXT_MUTED};">{size_kb:.1f} KB • {mtime}</div>
                            </div>
                        </div>
                        """
                        card_simple(content=content, footer="", elevated=False, bordered=True, padding="md")
                        st.download_button(
                            "⬇ Download",
                            data=file_data,
                            file_name=f.name,
                            mime="text/html",
                            key=f"saved_html_{f.name}",
                            use_container_width=True,
                        )
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    empty_state(icon="📄", title="No HTML Reports", description="Generate HTML reports to see them here.")

            with pdf_tab:
                if pdf_files:
                    # Responsive grid for PDF reports
                    st.markdown(f'<div style="{AUTO_FIT_CARD_CSS}">', unsafe_allow_html=True)
                    for f in pdf_files[:10]:
                        stat = f.stat()
                        size_kb = stat.st_size / 1024
                        mtime = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
                        with open(f, "rb") as fp:
                            file_data = fp.read()
                        content = f"""
                        <div style="display: flex; align-items: center; gap: {GAP_INLINE}; margin-bottom: {SPACE_3};">
                            <span style="font-size: 1.5rem;">📄</span>
                            <div style="flex: 1;">
                                <div style="font-weight: {BUTTON_FONT_WEIGHT}; color: {TEXT_PRIMARY};">{f.name}</div>
                                <div style="font-size: {FONT_SIZE_CAPTION}; color: {TEXT_MUTED};">{size_kb:.1f} KB • {mtime}</div>
                            </div>
                        </div>
                        """
                        card_simple(content=content, footer="", elevated=False, bordered=True, padding="md")
                        st.download_button(
                            "⬇ Download",
                            data=file_data,
                            file_name=f.name,
                            mime="application/pdf",
                            key=f"saved_pdf_{f.name}",
                            use_container_width=True,
                        )
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    empty_state(icon="📄", title="No PDF Reports", description="Generate PDF reports to see them here.")
        else:
            empty_state(
                icon="📁",
                title="No Saved Reports",
                description="Reports will appear here after generation.",
            )
    else:
        empty_state(
            icon="📁",
            title="Reports Directory Not Found",
            description="The reports/ directory will be created after your first report generation.",
        )


# =============================================================================
# SIMPLER ENTRY POINTS FOR EACH REPORT TYPE
# =============================================================================

def render_diagnostic_report_page():
    """Standalone page for diagnostic report generation."""
    st.set_page_config(page_title="Diagnostic Report", page_icon="🔍", layout="wide")

    # Initialize Design System
    initialize_layout()

    # Page Header
    page_header(
        title="Comprehensive Diagnostic Report",
        subtitle="Generate a detailed diagnostic report with DTCs, AI analysis, rule findings, and recommendations.",
        icon="🔍",
    )

    generator = ReportGenerator()
    sessions = generator.get_available_sessions()
    diagnoses = generator.get_available_diagnoses()

    col1, col2 = st.columns(2)
    with col1:
        session_options = ["Simulation"] + [f"{s['session_name']} ({s['session_id'][:8]})" for s in sessions]
        session_idx = selectbox(
            "OBD Session",
            options=range(len(session_options)),
            format_func=lambda i: session_options[i],
            key="diag_report_session",
            label="OBD Session",
        )
        session_id = None if session_idx == 0 else sessions[session_idx - 1]["session_id"]
    with col2:
        diag_options = ["Latest/None"] + [f"{d['diagnosis_id'][:8]} - {d['severity']}" for d in diagnoses]
        diag_idx = selectbox(
            "AI Diagnosis",
            options=range(len(diag_options)),
            format_func=lambda i: diag_options[i],
            key="diag_report_diagnosis",
            label="AI Diagnosis",
        )
        diagnosis_id = None if diag_idx == 0 else diagnoses[diag_idx - 1]["diagnosis_id"]

    format_type = st.radio("Format", [ReportFormat.HTML, ReportFormat.PDF], format_func=lambda x: x.value.upper(), horizontal=True)

    if button_primary("Generate Diagnostic Report", key="gen_diag_report", use_container_width=True):
        with spinner("Generating..."):
            result = generator.generate_diagnostic_report(
                session_id=session_id,
                diagnosis_id=diagnosis_id,
                format_type=format_type,
            )
            if format_type == ReportFormat.HTML:
                st.components.v1.html(result, height=800, scrolling=True)
                st.download_button("Download HTML", result, file_name="diagnostic_report.html", mime="text/html", use_container_width=True)
            else:
                st.download_button("Download PDF", result, file_name="diagnostic_report.pdf", mime="application/pdf", use_container_width=True)


def render_vehicle_health_report_page():
    """Standalone page for vehicle health report generation."""
    st.set_page_config(page_title="Vehicle Health Report", page_icon="🏥", layout="wide")

    # Initialize Design System
    initialize_layout()

    # Page Header
    page_header(
        title="Vehicle Health Report",
        subtitle="Generate a comprehensive vehicle health assessment.",
        icon="🏥",
    )

    generator = ReportGenerator()
    format_type = st.radio("Format", [ReportFormat.HTML, ReportFormat.PDF], format_func=lambda x: x.value.upper(), horizontal=True)

    if button_primary("Generate Vehicle Health Report", key="gen_health_report", use_container_width=True):
        with spinner("Generating..."):
            result = generator.generate_vehicle_health_report(format_type=format_type)
            if format_type == ReportFormat.HTML:
                st.components.v1.html(result, height=800, scrolling=True)
                st.download_button("Download HTML", result, file_name="vehicle_health_report.html", mime="text/html", use_container_width=True)
            else:
                st.download_button("Download PDF", result, file_name="vehicle_health_report.pdf", mime="application/pdf", use_container_width=True)


def render_performance_report_page():
    """Standalone page for performance report generation."""
    st.set_page_config(page_title="Performance Report", page_icon="📊", layout="wide")

    # Initialize Design System
    initialize_layout()

    # Page Header
    page_header(
        title="Performance Report",
        subtitle="Generate a driving session performance analysis.",
        icon="📊",
    )

    generator = ReportGenerator()
    sessions = generator.get_available_sessions()

    session_options = ["Simulation"] + [f"{s['session_name']} ({s['session_id'][:8]})" for s in sessions]
    session_idx = selectbox(
        "OBD Session",
        options=range(len(session_options)),
        format_func=lambda i: session_options[i],
        key="perf_report_session",
        label="OBD Session",
    )
    session_id = None if session_idx == 0 else sessions[session_idx - 1]["session_id"]

    format_type = st.radio("Format", [ReportFormat.HTML, ReportFormat.PDF], format_func=lambda x: x.value.upper(), horizontal=True)

    if button_primary("Generate Performance Report", key="gen_perf_report", use_container_width=True):
        with spinner("Generating..."):
            result = generator.generate_performance_report(session_id=session_id, format_type=format_type)
            if format_type == ReportFormat.HTML:
                st.components.v1.html(result, height=800, scrolling=True)
                st.download_button("Download HTML", result, file_name="performance_report.html", mime="text/html", use_container_width=True)
            else:
                st.download_button("Download PDF", result, file_name="performance_report.pdf", mime="application/pdf", use_container_width=True)


def render_maintenance_report_page():
    """Standalone page for maintenance report generation."""
    st.set_page_config(page_title="Maintenance Report", page_icon="🔧", layout="wide")

    # Initialize Design System
    initialize_layout()

    # Page Header
    page_header(
        title="Maintenance Report",
        subtitle="Generate a complete maintenance history and schedule report.",
        icon="🔧",
    )

    generator = ReportGenerator()
    format_type = st.radio("Format", [ReportFormat.HTML, ReportFormat.PDF], format_func=lambda x: x.value.upper(), horizontal=True)

    if button_primary("Generate Maintenance Report", key="gen_maint_report", use_container_width=True):
        with spinner("Generating..."):
            result = generator.generate_maintenance_report(format_type=format_type)
            if format_type == ReportFormat.HTML:
                st.components.v1.html(result, height=800, scrolling=True)
                st.download_button("Download HTML", result, file_name="maintenance_report.html", mime="text/html", use_container_width=True)
            else:
                st.download_button("Download PDF", result, file_name="maintenance_report.pdf", mime="application/pdf", use_container_width=True)
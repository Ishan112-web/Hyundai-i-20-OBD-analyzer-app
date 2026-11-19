"""
i20 AI Garage - Performance Module (Stage 5.4 Redesign)

Professional performance analytics with telemetry charts, session statistics,
session recording, comparison, and export capabilities.

Fully redesigned using Stage 3 Design System:
- components.ui.tokens for all styling
- components.charts_v2 for all charting
- components.ui.components for all UI primitives
- components.ui.layout for page structure
- components.shell for global shell integration

FULLY RESPONSIVE: mobile-first fluid grid, auto-fit charts, responsive tables.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional
import time

from config import ENGINE_SPECS
from services import get_database, get_obd_service
from services.database import DatabaseService

# Design System Imports
from components.ui.tokens import (
    # Colors
    STATUS_SUCCESS, STATUS_WARNING, STATUS_CRITICAL, STATUS_INFO,
    ACCENT_PRIMARY, ACCENT_SECONDARY,
    SERIES_1, SERIES_2, SERIES_3, SERIES_4, SERIES_5,
    CHART_GOOD, CHART_WARNING, CHART_SERIOUS, CHART_CRITICAL,
    DATASOURCE_REAL, DATASOURCE_SIMULATION,
    DIAG_CRITICAL, DIAG_MAJOR, DIAG_MINOR, DIAG_INFO,
    # Typography
    FONT_SIZE_H1, FONT_SIZE_H2, FONT_SIZE_H3, FONT_SIZE_H4,
    FONT_SIZE_BODY, FONT_SIZE_LABEL, FONT_SIZE_CAPTION,
    FONT_FAMILY_MONO, FONT_WEIGHT_NUMERIC, FONT_WEIGHT_LABEL,
    LETTER_SPACING_LABEL,
    # Spacing
    SPACE_1, SPACE_2, SPACE_3, SPACE_4, SPACE_5, SPACE_6,
    GAP_INLINE, GAP_FIELD, GAP_CARD, GAP_SECTION,
    # Radius
    RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_PILL,
    # Shadows
    SHADOW_SM, SHADOW_MD, SHADOW_LG,
)

# Series palette for comparison charts
SERIES_PALETTE = [SERIES_1, SERIES_2, SERIES_3, SERIES_4, SERIES_5]

from components.ui.components import (
    button_primary, button_secondary, button_ghost, button_danger,
    badge, BadgeVariant,
    alert, AlertVariant,
    card_simple, CardProps,
    empty_state, EmptyStateProps,
    table, TableProps, TableColumn,
    spinner, skeleton, skeleton_card,
    selectbox,
)
from components.ui.layout import section_header

from components.charts_v2 import (
    create_line_chart, LineChartConfig, LineSeries,
    create_bar_chart, BarChartConfig, BarSeries,
    create_comparison_chart, ComparisonConfig, ComparisonSeries,
    create_gauge, GaugeConfig,
    create_sparkline, SparklineConfig,
    create_status_indicator,
)

from components.ui.layout import (
    page_header,
    responsive_grid_css,
    auto_fit_grid_css,
    metric_row_columns,
    chart_columns,
    responsive_container,
    AUTO_FIT_CARD_CSS,
    AUTO_FIT_METRIC_CSS,
    CHART_GRID_CSS,
    grid_container,
)


def render_performance():
    """Render the complete performance analytics page using design system - FULLY RESPONSIVE."""
    db = get_database()
    obd = get_obd_service()

    # Initialize session state
    _init_session_state()

    # Page header using design system
    _render_page_header(obd)

    # Persistent disclaimer
    _render_disclaimer()

    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Live Telemetry",
        "📈 Session Statistics",
        "💾 Sessions",
        "⚖️ Compare Sessions"
    ])

    with tab1:
        _render_live_telemetry_tab()

    with tab2:
        _render_session_statistics_tab(db)

    with tab3:
        _render_sessions_tab(db)

    with tab4:
        _render_compare_sessions_tab(db)

    # Auto-update telemetry history when simulation is running
    if st.session_state.get("sim_running", False):
        _update_telemetry_history(obd, db)


def _init_session_state():
    """Initialize performance-specific session state variables (preserved exactly)."""
    defaults = {
        "sim_running": False,
        "sim_scenario": "idle",
        "telemetry_history": [],
        "session_id": None,
        "last_update": time.time(),
        "selected_session_ids": [],
        "compare_sessions": None,
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


def _render_page_header(obd):
    """Render page header using design system page_header component."""
    status = obd.get_status()
    mode = status["mode"]
    conn_state = status["connection_state"]

    # Determine connection status badge
    if conn_state == "connected" and mode == "simulation":
        conn_badge = badge("SIMULATION MODE", BadgeVariant.WARNING)
    elif conn_state == "connected":
        conn_badge = badge("CONNECTED", BadgeVariant.SUCCESS)
    elif conn_state == "error":
        conn_badge = badge("CONNECTION ERROR", BadgeVariant.CRITICAL)
    else:
        conn_badge = badge("DISCONNECTED", BadgeVariant.NEUTRAL)

    # Simulation warning badge
    sim_badge = ""
    if mode == "simulation":
        sim_badge = badge("Simulation Active", BadgeVariant.WARNING)

    # Recording indicator
    recording_badge = ""
    if st.session_state.get("sim_running") and st.session_state.get("session_id"):
        recording_badge = badge(
            f"● RECORDING Session #{st.session_state.session_id}",
            BadgeVariant.INFO
        )

    # Build actions for header
    actions_html = f"""
    <div style="display: flex; gap: {GAP_INLINE}; align-items: center; flex-wrap: wrap;">
        {conn_badge}
        {sim_badge}
        {recording_badge}
    </div>
    """

    page_header(
        title="Performance Analytics",
        subtitle="Real-time telemetry, session recording, and comparative analysis",
        actions=actions_html
    )

    # Simulation mode warning (alert component)
    if mode == "simulation":
        alert(
            "All displayed values are software-generated for demonstration purposes only. "
            "They do not represent actual vehicle sensor readings. Connect a real OBD-II adapter for live data.",
            AlertVariant.WARNING,
            title="⚠ Simulation Mode Active"
        )


def _render_disclaimer():
    """Render persistent disclaimer at bottom of page."""
    alert(
        "This application displays SIMULATED vehicle data for demonstration purposes. "
        "• No horsepower or torque estimation is performed "
        "• No acceleration time claims are made "
        "• All metrics are derived from OBD-II PID readings only "
        "• For real vehicle data, connect an ELM327 adapter and select \"Real OBD\" mode "
        "• CSV exports include `is_simulated` column for data provenance",
        AlertVariant.WARNING,
        title="⚠ Important Disclaimer",
        dismissible=False
    )


# ============================================================================
# TAB 1: LIVE TELEMETRY - RESPONSIVE CHART GRID
# ============================================================================

def _render_live_telemetry_tab():
    """Render Live Telemetry tab with 6 charts using responsive grid."""
    section_header("Live Telemetry", icon="📊", level=3)
    history = st.session_state.telemetry_history

    # Recording controls panel
    section_header("Recording Controls", icon="⏺️", level=4)
    _render_recording_controls_panel()

    if len(history) < 2:
        empty_state(EmptyStateProps(
            icon="📊",
            title="No Live Data",
            description="Start a recording or simulation to see real-time telemetry charts.",
            action_label="Go to Sessions Tab",
            action_key="goto_sessions"
        ))
        return

    # Convert history to DataFrame
    df = pd.DataFrame(history)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Render 6 charts in responsive grid using design system CHART_GRID_CSS
    st.markdown(CHART_GRID_CSS, unsafe_allow_html=True)
    st.markdown('<div class="i20-grid-responsive i20-grid-chart">', unsafe_allow_html=True)

    # RPM Chart
    _render_rpm_chart(df)

    # Speed Chart
    _render_speed_chart(df)

    # Coolant Chart
    _render_coolant_chart(df)

    # Engine Load Chart
    _render_engine_load_chart(df)

    # Throttle Chart
    _render_throttle_chart(df)

    # Fuel Trim Chart
    _render_fuel_trim_chart(df)

    st.markdown('</div>', unsafe_allow_html=True)


def _render_recording_controls_panel():
    """Render recording controls using design system buttons and alert - RESPONSIVE."""
    card_simple(
        title="Session Recording Controls",
        content="",
        footer=""
    )
    # Responsive button row - stacks on mobile
    col1, col2, col3, col4 = st.columns([1, 1, 1, 2], gap="small")

    with col1:
        if button_primary("▶ Start Recording", key="live_start_recording",
                          disabled=st.session_state.sim_running, use_container_width=True):
            _start_recording(get_database())

    with col2:
        if button_secondary("■ Stop Recording", key="live_stop_recording",
                            disabled=not st.session_state.sim_running, use_container_width=True):
            _stop_recording()

    with col3:
        if button_secondary("💾 Save Session", key="live_save_session",
                            disabled=not st.session_state.session_id or st.session_state.sim_running,
                            use_container_width=True):
            _save_session(get_database())

    with col4:
        if st.session_state.sim_running and st.session_state.session_id:
            alert(
                f"● RECORDING Session #{st.session_state.session_id} — "
                f"{_format_recording_duration()}",
                AlertVariant.INFO,
                dismissible=False
            )

    st.markdown(f"<div style='margin-bottom: {GAP_CARD};'></div>", unsafe_allow_html=True)


def _format_recording_duration() -> str:
    """Format recording duration from last_update."""
    elapsed = time.time() - st.session_state.last_update
    if elapsed < 60:
        return f"{elapsed:.0f}s"
    elif elapsed < 3600:
        mins = int(elapsed // 60)
        secs = int(elapsed % 60)
        return f"{mins}m {secs}s"
    else:
        hours = int(elapsed // 3600)
        mins = int((elapsed % 3600) // 60)
        return f"{hours}h {mins}m"


def _render_rpm_chart(df: pd.DataFrame):
    """Render RPM chart using create_line_chart - RESPONSIVE."""
    if 'rpm' not in df.columns:
        return

    config = LineChartConfig(
        title="Engine RPM",
        x_axis="Time",
        y_axis="RPM",
        series=[
            LineSeries(
                name="RPM",
                x=df['timestamp'].tolist(),
                y=df['rpm'].tolist(),
                color=SERIES_1,
            ),
        ],
        reference_lines=[
            {"value": ENGINE_SPECS.get('redline_rpm', 6500), "color": CHART_CRITICAL,
             "dash": "dash", "label": f"Redline ({ENGINE_SPECS.get('redline_rpm', 6500)} RPM)"}
        ],
        height=300,
        show_legend=False,
        margin=dict(l=50, r=20, t=40, b=40),
    )
    fig = create_line_chart(config)

    card_simple(
        title="🔄 Engine RPM History",
        content="",
        footer=""
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)


def _render_speed_chart(df: pd.DataFrame):
    """Render Speed chart using create_line_chart - RESPONSIVE."""
    if 'speed_kmh' not in df.columns:
        return

    config = LineChartConfig(
        title="Vehicle Speed",
        x_axis="Time",
        y_axis="km/h",
        series=[
            LineSeries(
                name="Speed",
                x=df['timestamp'].tolist(),
                y=df['speed_kmh'].tolist(),
                color=SERIES_2,
            ),
        ],
        height=300,
        show_legend=False,
        margin=dict(l=50, r=20, t=40, b=40),
    )
    fig = create_line_chart(config)

    card_simple(
        title="🚗 Vehicle Speed History",
        content="",
        footer=""
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)


def _render_coolant_chart(df: pd.DataFrame):
    """Render Coolant Temperature chart using create_line_chart with reference bands - RESPONSIVE."""
    if 'coolant_temp_c' not in df.columns:
        return

    config = LineChartConfig(
        title="Coolant Temperature",
        x_axis="Time",
        y_axis="°C",
        series=[
            LineSeries(
                name="Coolant Temp",
                x=df['timestamp'].tolist(),
                y=df['coolant_temp_c'].tolist(),
                color=SERIES_3,
            ),
        ],
        reference_lines=[
            {"value": 85, "color": CHART_GOOD, "dash": "dot", "label": "Normal Min (85°C)"},
            {"value": 95, "color": CHART_GOOD, "dash": "dot", "label": "Normal Max (95°C)"},
            {"value": 105, "color": CHART_WARNING, "dash": "dash", "label": "Warning (105°C)"},
            {"value": 125, "color": CHART_CRITICAL, "dash": "dash", "label": "Critical (125°C)"},
        ],
        height=300,
        show_legend=False,
        margin=dict(l=50, r=20, t=40, b=40),
    )
    fig = create_line_chart(config)

    card_simple(
        title="🌡️ Coolant Temperature History",
        content="",
        footer=""
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)


def _render_engine_load_chart(df: pd.DataFrame):
    """Render Engine Load chart using create_line_chart - RESPONSIVE."""
    if 'engine_load_pct' not in df.columns:
        return

    config = LineChartConfig(
        title="Engine Load",
        x_axis="Time",
        y_axis="%",
        series=[
            LineSeries(
                name="Engine Load",
                x=df['timestamp'].tolist(),
                y=df['engine_load_pct'].tolist(),
                color=SERIES_4,
            ),
        ],
        height=300,
        show_legend=False,
        margin=dict(l=50, r=20, t=40, b=40),
    )
    fig = create_line_chart(config)

    card_simple(
        title="⚙️ Engine Load History",
        content="",
        footer=""
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)


def _render_throttle_chart(df: pd.DataFrame):
    """Render Throttle Position chart using create_line_chart - RESPONSIVE."""
    if 'throttle_pos_pct' not in df.columns:
        return

    config = LineChartConfig(
        title="Throttle Position",
        x_axis="Time",
        y_axis="%",
        series=[
            LineSeries(
                name="Throttle",
                x=df['timestamp'].tolist(),
                y=df['throttle_pos_pct'].tolist(),
                color=SERIES_5,
            ),
        ],
        height=300,
        show_legend=False,
        margin=dict(l=50, r=20, t=40, b=40),
    )
    fig = create_line_chart(config)

    card_simple(
        title="🎯 Throttle Position History",
        content="",
        footer=""
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)


def _render_fuel_trim_chart(df: pd.DataFrame):
    """Render Fuel Trim chart (STFT/LTFT) using create_line_chart multi-series - RESPONSIVE."""
    has_stft = 'stft_b1_pct' in df.columns
    has_ltft = 'ltft_b1_pct' in df.columns

    if not has_stft and not has_ltft:
        return

    series = []
    if has_stft:
        series.append(LineSeries(
            name="STFT Bank 1",
            x=df['timestamp'].tolist(),
            y=df['stft_b1_pct'].tolist(),
            color=SERIES_1,
        ))
    if has_ltft:
        series.append(LineSeries(
            name="LTFT Bank 1",
            x=df['timestamp'].tolist(),
            y=df['ltft_b1_pct'].tolist(),
            color=SERIES_2,
        ))

    config = LineChartConfig(
        title="Fuel Trim (STFT / LTFT)",
        x_axis="Time",
        y_axis="%",
        series=series,
        reference_lines=[
            {"value": 0, "color": STATUS_INFO, "dash": "dot", "label": "Zero"},
            {"value": 10, "color": CHART_GOOD, "dash": "dot", "label": "+10%"},
            {"value": -10, "color": CHART_GOOD, "dash": "dot", "label": "-10%"},
            {"value": 20, "color": CHART_WARNING, "dash": "dash", "label": "+20%"},
            {"value": -20, "color": CHART_WARNING, "dash": "dash", "label": "-20%"},
            {"value": 30, "color": CHART_CRITICAL, "dash": "dash", "label": "+30%"},
            {"value": -30, "color": CHART_CRITICAL, "dash": "dash", "label": "-30%"},
        ],
        height=300,
        show_legend=True,
        legend_position="top",
        margin=dict(l=50, r=20, t=40, b=40),
    )
    fig = create_line_chart(config)

    card_simple(
        title="⛽ Fuel Trim History (STFT / LTFT)",
        content="",
        footer=""
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================================
# TAB 2: SESSION STATISTICS - RESPONSIVE METRIC GRID
# ============================================================================

def _render_session_statistics_tab(db: DatabaseService):
    """Render Session Statistics tab using design system - RESPONSIVE."""
    section_header("Session Statistics", icon="📈", level=3)
    # Check for active session
    active_session = db.get_active_session()

    if st.session_state.get("session_id"):
        session = db.get_telemetry_sessions(limit=100)
        session = next((s for s in session if s["id"] == st.session_state.session_id), None)
    elif active_session:
        session = active_session
    else:
        session = None

    if not session:
        empty_state(EmptyStateProps(
            icon="📈",
            title="No Active Session",
            description="Start and save a session from the Sessions tab to view statistics.",
        ))
        return

    # Calculate additional stats from records
    records = db.get_session_records(session["id"])
    if not records:
        empty_state(EmptyStateProps(
            icon="📈",
            title="No Data in Session",
            description="Session exists but contains no telemetry records.",
        ))
        return

    df = pd.DataFrame(records)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Calculate statistics
    stats = _calculate_session_stats(df, session)

    # Session selector
    section_header("Session Selector", icon="🔄", level=4)
    _render_session_selector(db, session)

    # Key metric cards with sparklines - RESPONSIVE using AUTO_FIT_METRIC_CSS
    section_header("Key Metrics", icon="📊", level=4)
    st.markdown(AUTO_FIT_METRIC_CSS, unsafe_allow_html=True)
    st.markdown('<div class="i20-grid-auto-fit-metric">', unsafe_allow_html=True)
    _render_metric_cards_with_sparklines(stats, df)
    st.markdown('</div>', unsafe_allow_html=True)

    # Detailed statistics table - RESPONSIVE (horizontal scroll on mobile)
    section_header("Detailed Statistics", icon="📋", level=4)
    _render_detailed_stats_table(stats, df)

    # Time distribution histograms - RESPONSIVE chart grid
    section_header("Time Distribution", icon="📊", level=4)
    st.markdown(CHART_GRID_CSS, unsafe_allow_html=True)
    st.markdown('<div class="i20-grid-responsive i20-grid-chart">', unsafe_allow_html=True)
    _render_time_distribution_charts(df)
    st.markdown('</div>', unsafe_allow_html=True)


def _render_session_selector(db: DatabaseService, current_session: Dict):
    """Render session selector dropdown."""
    sessions = db.get_telemetry_sessions(limit=100)
    if len(sessions) <= 1:
        return

    options = {}
    for s in sessions:
        label = f"#{s['id']} - {s.get('session_name', 'Unnamed')} ({s.get('scenario', 'unknown')})"
        options[label] = s['id']

    # Find current selection
    current_label = next((k for k, v in options.items() if v == current_session["id"]), list(options.keys())[0])

    selected = selectbox(
        "Active Session",
        options=list(options.keys()),
        index=list(options.keys()).index(current_label),
        key="stats_session_selector"
    )

    if options[selected] != current_session["id"]:
        st.session_state.session_id = options[selected]
        st.rerun()


def _render_metric_cards_with_sparklines(stats: Dict[str, Any], df: pd.DataFrame):
    """Render 4 key metric cards with sparklines using responsive grid."""
    # Prepare sparkline data
    rpm_sparkline = df['rpm'].tolist() if 'rpm' in df.columns else []
    speed_sparkline = df['speed_kmh'].tolist() if 'speed_kmh' in df.columns else []
    load_sparkline = df['engine_load_pct'].tolist() if 'engine_load_pct' in df.columns else []
    throttle_sparkline = df['throttle_pos_pct'].tolist() if 'throttle_pos_pct' in df.columns else []

    cards = [
        {
            "icon": "⬆",
            "label": "Peak RPM",
            "value": f"{stats.get('peak_rpm', 0):,.0f}",
            "detail": "Maximum recorded",
            "sparkline_data": rpm_sparkline,
            "sparkline_color": SERIES_1,
        },
        {
            "icon": "🏁",
            "label": "Max Speed",
            "value": f"{stats.get('max_speed', 0):.1f} km/h",
            "detail": "Peak velocity",
            "sparkline_data": speed_sparkline,
            "sparkline_color": SERIES_2,
        },
        {
            "icon": "📊",
            "label": "Avg Speed",
            "value": f"{stats.get('avg_speed', 0):.1f} km/h",
            "detail": "While moving",
            "sparkline_data": load_sparkline,
            "sparkline_color": SERIES_3,
        },
        {
            "icon": "⏱",
            "label": "Duration",
            "value": stats.get('duration_formatted', 'N/A'),
            "detail": "Session length",
            "sparkline_data": throttle_sparkline,
            "sparkline_color": SERIES_4,
        },
    ]

    for card in cards:
        _render_metric_card(card)


def _render_metric_card(card: Dict[str, Any]):
    """Render a single metric card with sparkline - RESPONSIVE."""
    # Create sparkline if data available
    sparkline_html = ""
    if card["sparkline_data"] and len(card["sparkline_data"]) > 1:
        spark_config = SparklineConfig(
            data=card["sparkline_data"],
            color=card["sparkline_color"],
            height=40,
            show_area=True,
            area_opacity=0.15,
        )
        spark_fig = create_sparkline(spark_config)
        sparkline_html = spark_fig.to_html(
            include_plotlyjs=False,
            div_id=f"sparkline-{card['label'].replace(' ', '-')}",
            config={'displayModeBar': False, 'staticPlot': True}
        )

    card_html = f"""
    <div class="i20-metric-card" style="
        background: var(--i20-color-bg-card);
        border: 1px solid var(--i20-color-border);
        border-radius: var(--i20-radius-lg);
        padding: var(--i20-spacing-lg);
        box-shadow: var(--i20-shadow-md);
        min-height: 180px;
        display: flex;
        flex-direction: column;
    ">
        <div style="font-size: 1.5rem; margin-bottom: var(--i20-spacing-sm);">{card['icon']}</div>
        <div style="
            font-size: var(--i20-font-size-h2);
            font-weight: var(--i20-font-weight-numeric);
            font-family: var(--i20-font-family-mono);
            color: var(--i20-color-text-primary);
            margin-bottom: var(--i20-spacing-xs);
        ">{card['value']}</div>
        <div style="
            font-size: var(--i20-font-size-label);
            font-weight: var(--i20-font-weight-label);
            letter-spacing: var(--i20-letter-spacing-label);
            color: var(--i20-color-text-secondary);
            text-transform: uppercase;
            margin-bottom: var(--i20-spacing-xs);
        ">{card['label']}</div>
        <div style="
            font-size: var(--i20-font-size-caption);
            color: var(--i20-color-text-secondary);
            margin-bottom: var(--i20-spacing-md);
        ">{card['detail']}</div>
        <div style="margin-top: auto;">
            {sparkline_html}
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def _render_detailed_stats_table(stats: Dict[str, Any], df: pd.DataFrame):
    """Render detailed statistics using design system table component - RESPONSIVE."""
    detail_rows = [
        ("Session ID", str(stats.get("session_id", "N/A"))),
        ("Session Name", stats.get("session_name", "N/A")),
        ("Scenario", stats.get("scenario", "N/A").title()),
        ("Start Time", stats.get("start_time", "N/A")[:19] if stats.get("start_time") else "N/A"),
        ("End Time", stats.get("end_time", "N/A")[:19] if stats.get("end_time") else "N/A"),
        ("Duration", stats.get("duration_formatted", "N/A")),
        ("Total Records", f"{stats.get('total_records', 0):,}"),
        ("Data Span", f"{stats.get('data_span_seconds', 0):.0f}s"),
        ("", ""),  # Separator
        ("Peak RPM", f"{stats.get('peak_rpm', 0):,.0f}"),
        ("Average RPM", f"{stats.get('avg_rpm', 0):.0f}"),
        ("Time at Idle (<1000 RPM)", f"{stats.get('time_at_idle', 0):.1f}%"),
        ("Time at High RPM (>4000)", f"{stats.get('time_at_high_rpm', 0):.1f}%"),
        ("", ""),
        ("Maximum Speed", f"{stats.get('max_speed', 0):.1f} km/h"),
        ("Average Speed (moving)", f"{stats.get('avg_speed', 0):.1f} km/h"),
        ("Estimated Distance", f"{stats.get('distance_km', 0):.2f} km"),
        ("", ""),
        ("Max Coolant Temp", f"{stats.get('max_coolant_temp', 0):.1f} °C"),
        ("Max Engine Load", f"{stats.get('max_engine_load', 0):.1f}%"),
        ("Average Engine Load", f"{stats.get('avg_load', 0):.1f}%"),
        ("", ""),
        ("Average Throttle", f"{stats.get('avg_throttle', 0):.1f}%"),
        ("Time at WOT (>90%)", f"{stats.get('time_wot', 0):.1f}%"),
    ]

    # Add fuel trim stats if available
    if 'avg_stft' in stats:
        detail_rows.extend([
            ("", ""),
            ("Avg STFT Bank 1", f"{stats.get('avg_stft', 0):.1f}%"),
            ("STFT Range", f"{stats.get('min_stft', 0):.1f}% to {stats.get('max_stft', 0):.1f}%"),
            ("Avg LTFT Bank 1", f"{stats.get('avg_ltft', 0):.1f}%"),
            ("LTFT Range", f"{stats.get('min_ltft', 0):.1f}% to {stats.get('max_ltft', 0):.1f}%"),
        ])

    # Build table data
    table_data = []
    for label, value in detail_rows:
        if label == "":
            continue  # Skip separators in table
        table_data.append({"Metric": label, "Value": value, "Unit": ""})

    columns = [
        TableColumn(key="Metric", header="Metric", width="280px"),
        TableColumn(key="Value", header="Value", width="180px", align="right", format="mono"),
        TableColumn(key="Unit", header="Unit", width="80px"),
    ]

    card_simple(
        title="Detailed Statistics",
        content="",
        footer=""
    )
    table(TableProps(
        columns=columns,
        data=table_data,
        striped=True,
        hoverable=True,
        compact=True,
    ))
    st.markdown('</div>', unsafe_allow_html=True)


def _render_time_distribution_charts(df: pd.DataFrame):
    """Render RPM and Speed distribution histograms using create_bar_chart - RESPONSIVE."""
    if 'rpm' not in df.columns and 'speed_kmh' not in df.columns:
        return

    # RPM Distribution
    if 'rpm' in df.columns:
        _render_histogram_card(
            title="RPM Distribution",
            data=df['rpm'],
            bins=30,
            color=SERIES_1,
            x_title="RPM",
            y_title="Count",
        )

    # Speed Distribution
    if 'speed_kmh' in df.columns:
        _render_histogram_card(
            title="Speed Distribution",
            data=df['speed_kmh'],
            bins=30,
            color=SERIES_2,
            x_title="km/h",
            y_title="Count",
        )


def _render_histogram_card(title: str, data: pd.Series, bins: int, color: str,
                           x_title: str, y_title: str):
    """Render a histogram card using create_bar_chart - RESPONSIVE."""
    # Compute histogram
    hist, bin_edges = np.histogram(data.dropna(), bins=bins)
    bin_centers = [(bin_edges[i] + bin_edges[i+1]) / 2 for i in range(len(bin_edges) - 1)]
    bin_labels = [f"{b:.0f}" for b in bin_centers]

    config = BarChartConfig(
        title=title,
        x_axis=x_title,
        y_axis=y_title,
        series=[
            BarSeries(name="Count", data=hist.tolist(), color=color),
        ],
        categories=bin_labels,
        height=300,
        show_legend=False,
        bargap=0.1,
    )
    fig = create_bar_chart(config)

    card_simple(
        title=f"📊 {title}",
        content="",
        footer=""
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================================
# TAB 3: SESSIONS - RESPONSIVE TABLE
# ============================================================================

def _render_sessions_tab(db: DatabaseService):
    """Render Sessions tab with recording controls and session table - RESPONSIVE."""
    section_header("Sessions", icon="💾", level=3)
    # Recording controls panel
    section_header("Recording Controls", icon="⏺️", level=4)
    _render_session_recording_panel(db)

    # Sessions list
    sessions = db.get_telemetry_sessions(limit=50)

    if not sessions:
        empty_state(EmptyStateProps(
            icon="💾",
            title="No Sessions Recorded",
            description="Start a recording session to capture telemetry data for analysis.",
            action_label="▶ Start Recording",
            action_key="goto_recording"
        ))
        return

    # Bulk actions bar
    if st.session_state.selected_session_ids:
        section_header("Bulk Actions", icon="⚡", level=4)
        _render_bulk_actions_bar()

    # Session table - RESPONSIVE
    section_header("Saved Sessions", icon="📋", level=4)
    _render_sessions_table(db, sessions)


def _render_session_recording_panel(db: DatabaseService):
    """Render session recording controls panel - RESPONSIVE."""
    obd = get_obd_service()
    status = obd.get_status()

    card_simple(
        title="Session Recording Controls",
        content="",
        footer=""
    )

    # Session name and scenario inputs - responsive
    col_name, col_scenario = st.columns([2, 1], gap="medium")
    with col_name:
        session_name = st.text_input(
            "Session Name",
            placeholder="My Session",
            key="session_name_input",
            label_visibility="collapsed"
        )
    with col_scenario:
        scenario = selectbox(
            "Scenario",
            options=["idle", "city", "highway", "acceleration", "custom"],
            index=["idle", "city", "highway", "acceleration", "custom"].index(
                st.session_state.get("sim_scenario", "idle")
            ),
            key="session_scenario_selector"
        )
        st.session_state.sim_scenario = scenario

    st.markdown(f"<div style='margin-top: {GAP_FIELD};'></div>", unsafe_allow_html=True)

    # Control buttons - responsive row (stacks on mobile via use_container_width)
    col1, col2, col3, col4 = st.columns([1, 1, 1, 2], gap="small")

    with col1:
        if button_primary("▶ Start Recording", key="sess_start_recording",
                          disabled=st.session_state.sim_running, use_container_width=True):
            _start_recording(db, session_name or f"{scenario.title()} - {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    with col2:
        if button_secondary("■ Stop Recording", key="sess_stop_recording",
                            disabled=not st.session_state.sim_running, use_container_width=True):
            _stop_recording()

    with col3:
        if button_secondary("💾 Save Session", key="sess_save_session",
                            disabled=not st.session_state.session_id or st.session_state.sim_running,
                            use_container_width=True):
            _save_session(db)

    with col4:
        if st.session_state.sim_running and st.session_state.session_id:
            alert(
                f"● RECORDING Session #{st.session_state.session_id} — {_format_recording_duration()}",
                AlertVariant.INFO,
                dismissible=False
            )

    # Simulation mode warning
    if status["mode"] == "simulation" or status["simulation_running"]:
        st.markdown(f"<div style='margin-top: {GAP_FIELD};'></div>", unsafe_allow_html=True)
        alert(
            "Data is simulated, not from real vehicle. Connect an ELM327 adapter for live data.",
            AlertVariant.WARNING,
            title="⚠ Simulation Mode Active"
        )

    st.markdown('</div>', unsafe_allow_html=True)


def _render_bulk_actions_bar():
    """Render bulk actions bar when sessions are selected - RESPONSIVE."""
    count = len(st.session_state.selected_session_ids)
    st.markdown(f"""
    <div class="i20-bulk-actions" style="
        display: flex; flex-wrap: wrap; align-items: center; gap: var(--i20-gap-inline);
        padding: var(--i20-spacing-md) var(--i20-spacing-lg);
        background: var(--i20-color-bg-secondary);
        border: 1px solid var(--i20-color-border);
        border-radius: var(--i20-radius-md);
        margin-bottom: var(--i20-gap-card);
    ">
        <span style="font-size: var(--i20-font-size-label); font-weight: var(--i20-font-weight-label); color: var(--i20-color-text-secondary);">
            {count} selected
        </span>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3, gap="small")
    with col1:
        if button_ghost("📊 Compare Selected", key="bulk_compare", use_container_width=True):
            st.session_state.compare_sessions = st.session_state.selected_session_ids.copy()
            st.rerun()
    with col2:
        if button_ghost("📥 Export All CSV", key="bulk_export", use_container_width=True):
            _export_multiple_sessions_csv(db=get_database(), session_ids=st.session_state.selected_session_ids)
    with col3:
        if button_danger("🗑 Delete Selected", key="bulk_delete", use_container_width=True):
            _bulk_delete_sessions()


def _bulk_delete_sessions():
    """Delete all selected sessions."""
    db = get_database()
    for sid in st.session_state.selected_session_ids:
        _delete_session(db, sid)
    st.session_state.selected_session_ids = []
    st.rerun()


def _render_sessions_table(db: DatabaseService, sessions: List[Dict]):
    """Render sessions table using design system table component - RESPONSIVE."""
    # Prepare table data
    table_data = []
    for session in sessions:
        session_id = session["id"]
        is_selected = session_id in st.session_state.selected_session_ids

        duration = session.get("duration_seconds")
        dur_str = _format_duration(duration) if duration else "In progress"

        start_time = session.get("start_time", "")
        date_str = start_time[:16].replace("T", " ") if start_time else "N/A"

        scenario = session.get("scenario", "unknown").title()

        record_count = _get_record_count(db, session_id)

        table_data.append({
            "select": is_selected,
            "id": session_id,
            "name": session.get('session_name', 'Unnamed'),
            "scenario": scenario,
            "date": date_str,
            "duration": dur_str,
            "peak_rpm": session.get('peak_rpm', 0),
            "max_speed": session.get('max_speed', 0),
            "avg_speed": session.get('avg_speed', 0),
            "records": record_count,
            "session_id": session_id,  # for actions
        })

    # Responsive table columns - use more flexible widths
    columns = [
        TableColumn(key="select", header="☐", width="50px", align="center"),
        TableColumn(key="id", header="ID", width="70px", align="right", format="mono", prefix="#"),
        TableColumn(key="name", header="Name", width="200px"),
        TableColumn(key="scenario", header="Scenario", width="120px", badge=True),
        TableColumn(key="date", header="Date/Time", width="160px"),
        TableColumn(key="duration", header="Duration", width="100px", align="right"),
        TableColumn(key="peak_rpm", header="Peak RPM", width="100px", align="right", format="numeric"),
        TableColumn(key="max_speed", header="Max Speed", width="110px", align="right", format="numeric", suffix=" km/h"),
        TableColumn(key="avg_speed", header="Avg Speed", width="110px", align="right", format="numeric", suffix=" km/h"),
        TableColumn(key="records", header="Records", width="90px", align="right", format="numeric"),
        TableColumn(key="actions", header="Actions", width="140px"),
    ]

    card_simple(
        title="Saved Sessions",
        content="",
        footer=""
    )

    # Render interactive table with responsive behavior
    _render_interactive_session_table(table_data, columns, db)

    st.markdown('</div>', unsafe_allow_html=True)


def _render_interactive_session_table(table_data: List[Dict], columns: List[TableColumn], db: DatabaseService):
    """Render interactive session table with checkboxes and action buttons - RESPONSIVE."""
    # Use the table component with custom rendering for actions
    for i, row in enumerate(table_data):
        session_id = row["session_id"]
        is_selected = session_id in st.session_state.selected_session_ids

        # Responsive row using columns
        col_select, col_id, col_name, col_scenario, col_date, col_dur, col_rpm, col_max_spd, col_avg_spd, col_rec, col_actions = st.columns(
            [0.5, 0.7, 2.2, 1.2, 1.6, 1.0, 1.0, 1.1, 1.1, 0.9, 1.4],
            gap="small"
        )

        with col_select:
            new_selected = st.checkbox("", key=f"select_session_{session_id}", value=is_selected, label_visibility="collapsed")
            if new_selected != is_selected:
                if new_selected:
                    if session_id not in st.session_state.selected_session_ids:
                        st.session_state.selected_session_ids.append(session_id)
                else:
                    if session_id in st.session_state.selected_session_ids:
                        st.session_state.selected_session_ids.remove(session_id)
                st.rerun()

        with col_id:
            st.markdown(f"<code style='font-size: var(--i20-font-size-body);'>#{session_id}</code>", unsafe_allow_html=True)

        with col_name:
            st.markdown(f"<span style='font-size: var(--i20-font-size-body);'>{row['name']}</span>", unsafe_allow_html=True)

        with col_scenario:
            badge(row['scenario'], BadgeVariant.NEUTRAL)

        with col_date:
            st.markdown(f"<span style='font-size: var(--i20-font-size-body); font-family: var(--i20-font-family-mono);'>{row['date']}</span>", unsafe_allow_html=True)

        with col_dur:
            st.markdown(f"<span style='font-size: var(--i20-font-size-body); font-family: var(--i20-font-family-mono); text-align: right;'>{row['duration']}</span>", unsafe_allow_html=True)

        with col_rpm:
            st.markdown(f"<span style='font-size: var(--i20-font-size-body); font-family: var(--i20-font-family-mono); text-align: right;'>{row['peak_rpm']:,.0f}</span>", unsafe_allow_html=True)

        with col_max_spd:
            st.markdown(f"<span style='font-size: var(--i20-font-size-body); font-family: var(--i20-font-family-mono); text-align: right;'>{row['max_speed']:.1f}</span>", unsafe_allow_html=True)

        with col_avg_spd:
            st.markdown(f"<span style='font-size: var(--i20-font-size-body); font-family: var(--i20-font-family-mono); text-align: right;'>{row['avg_speed']:.1f}</span>", unsafe_allow_html=True)

        with col_rec:
            st.markdown(f"<span style='font-size: var(--i20-font-size-body); font-family: var(--i20-font-family-mono); text-align: right;'>{row['records']:,}</span>", unsafe_allow_html=True)

        with col_actions:
            _render_session_action_buttons(db, session_id)


def _render_session_action_buttons(db: DatabaseService, session_id: int):
    """Render action buttons for a session row - RESPONSIVE."""
    col_view, col_export, col_delete = st.columns(3, gap="small")
    with col_view:
        if st.button("👁", key=f"view_{session_id}", help="View details", use_container_width=True):
            _view_session_details(db, session_id)
    with col_export:
        _export_session_csv(db, session_id)
    with col_delete:
        if st.button("🗑", key=f"delete_{session_id}", help="Delete session", use_container_width=True):
            _delete_session(db, session_id)


def _view_session_details(db: DatabaseService, session_id: int):
    """Show session details in an expander."""
    session = next((s for s in db.get_telemetry_sessions(limit=100) if s["id"] == session_id), None)
    if not session:
        st.error("Session not found")
        return

    records = db.get_session_records(session_id)
    if not records:
        st.warning("No records in this session")
        return

    df = pd.DataFrame(records)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    with st.expander(f"Session #{session_id} Details", expanded=True):
        st.markdown(f"**Name:** {session.get('session_name', 'Unnamed')}")
        st.markdown(f"**Scenario:** {session.get('scenario', 'unknown').title()}")
        st.markdown(f"**Date:** {session.get('start_time', 'N/A')[:19]}")
        st.markdown(f"**Duration:** {_format_duration(session.get('duration_seconds', 0)) if session.get('duration_seconds') else 'In progress'}")
        st.markdown(f"**Records:** {len(records):,}")

        # Quick stats
        stats = _calculate_session_stats(df, session)

        col1, col2, col3, col4 = st.columns(4, gap="medium")
        with col1:
            st.metric("Peak RPM", f"{stats.get('peak_rpm', 0):,.0f}")
        with col2:
            st.metric("Max Speed", f"{stats.get('max_speed', 0):.1f} km/h")
        with col3:
            st.metric("Avg Speed", f"{stats.get('avg_speed', 0):.1f} km/h")
        with col4:
            st.metric("Max Coolant", f"{stats.get('max_coolant_temp', 0):.1f} °C")


# ============================================================================
# TAB 4: COMPARE SESSIONS - RESPONSIVE GRID
# ============================================================================

def _render_compare_sessions_tab(db: DatabaseService):
    """Render Compare Sessions tab - RESPONSIVE."""
    section_header("Compare Sessions", icon="⚖️", level=3)
    card_simple(
        title="Session Comparison",
        content="",
        footer=""
    )

    if not st.session_state.get("compare_sessions"):
        section_header("Select Sessions to Compare", icon="🔍", level=4)
        _render_comparison_selector(db)
    else:
        section_header("Comparison Results", icon="📊", level=4)
        _render_session_comparison(db, st.session_state.compare_sessions)

        # Clear comparison button
        if button_ghost("✖ Clear Comparison", key="clear_comparison", use_container_width=True):
            st.session_state.compare_sessions = []
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def _render_comparison_selector(db: DatabaseService):
    """Render session selector for comparison - RESPONSIVE."""
    sessions = db.get_telemetry_sessions(limit=20)

    if not sessions:
        empty_state(EmptyStateProps(
            icon="⚖️",
            title="No Sessions Available",
            description="Create sessions in the Sessions tab first, then return here to compare.",
        ))
        return

    # Instruction
    alert(
        "Select 2 or more sessions to compare. You can also use the Sessions tab to select multiple sessions "
        "with checkboxes and click \"Compare Selected\".",
        AlertVariant.INFO,
        title="📊 Select Sessions to Compare"
    )

    # Manual selector (up to 5 sessions) - responsive columns
    st.markdown("**Manual Selection:**")

    session_options = {}
    for s in sessions:
        label = f"#{s['id']} - {s.get('session_name', 'Unnamed')} ({s.get('scenario', 'unknown')})"
        session_options[label] = s['id']

    # 5 selectboxes in responsive columns
    cols = st.columns(5, gap="small")
    selected_ids = []

    for i, col in enumerate(cols):
        with col:
            options_list = ["(none)"] + list(session_options.keys())
            # Filter out already selected
            available = [o for o in options_list if o == "(none)" or session_options.get(o) not in selected_ids]
            selected = st.selectbox(
                f"Session {i+1}",
                options=available,
                index=0,
                key=f"compare_selector_{i}"
            )
            if selected != "(none)":
                selected_ids.append(session_options[selected])

    # Compare button
    st.markdown(f"<div style='margin-top: {GAP_FIELD};'></div>", unsafe_allow_html=True)
    if button_primary("⚖️ Compare Selected", key="manual_compare",
                      disabled=len(selected_ids) < 2, use_container_width=True):
        st.session_state.compare_sessions = selected_ids
        st.rerun()


def _render_session_comparison(db: DatabaseService, session_ids: List[int]):
    """Render comparison charts and summary table for selected sessions - RESPONSIVE."""
    # Load data for all sessions
    session_data = {}
    for sid in session_ids:
        records = db.get_session_records(sid)
        if records:
            df = pd.DataFrame(records)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            # Normalize time to start at 0
            if len(df) > 0:
                start_time = df['timestamp'].min()
                df['elapsed_seconds'] = (df['timestamp'] - start_time).dt.total_seconds()
            session_data[sid] = df

    if not session_data:
        alert("No data available for selected sessions", AlertVariant.WARNING)
        return

    # Get session info
    sessions = db.get_telemetry_sessions(limit=100)
    session_info = {s["id"]: s for s in sessions if s["id"] in session_ids}

    # Session badges - responsive
    st.markdown("**Comparing:**")
    badge_cols = st.columns(min(len(session_ids), 5), gap="small")
    for i, sid in enumerate(session_ids):
        with badge_cols[i]:
            info = session_info.get(sid, {})
            name = info.get('session_name', f'Session #{sid}')
            scenario = info.get('scenario', 'unknown')
            badge(f"{name} ({scenario})", BadgeVariant.NEUTRAL)

    st.markdown(f"<div style='margin-top: {GAP_CARD};'></div>", unsafe_allow_html=True)

    # Comparison charts using create_comparison_chart - RESPONSIVE GRID
    section_header("Overlay Comparison", level=4)

    metrics = [
        ('rpm', 'RPM', SERIES_1),
        ('speed_kmh', 'Speed (km/h)', SERIES_2),
        ('coolant_temp_c', 'Coolant Temp (°C)', SERIES_3),
        ('engine_load_pct', 'Engine Load (%)', SERIES_4),
        ('throttle_pos_pct', 'Throttle (%)', SERIES_5),
    ]

    # Render in responsive grid (2 columns desktop, 1 mobile)
    st.markdown(CHART_GRID_CSS, unsafe_allow_html=True)
    st.markdown('<div class="i20-grid-responsive i20-grid-chart">', unsafe_allow_html=True)

    for idx, (col_name, title, color) in enumerate(metrics):
        _render_comparison_chart_card(
            title=title,
            session_data=session_data,
            session_info=session_info,
            metric_col=col_name,
            color=color,
        )

    st.markdown('</div>', unsafe_allow_html=True)

    # Summary comparison table
    _render_comparison_summary_table(session_data, session_info)


def _render_comparison_chart_card(title: str, session_data: Dict, session_info: Dict,
                                   metric_col: str, color: str):
    """Render a single comparison chart card - RESPONSIVE."""
    # Build comparison series
    comparison_series = []
    for i, (sid, df) in enumerate(session_data.items()):
        if metric_col in df.columns:
            info = session_info.get(sid, {})
            name = info.get('session_name', f'Session #{sid}')
            scenario = info.get('scenario', 'unknown')

            comparison_series.append(ComparisonSeries(
                name=f"{name} ({scenario})",
                x=df['elapsed_seconds'].tolist(),
                y=df[metric_col].tolist(),
                color=SERIES_PALETTE[i % len(SERIES_PALETTE)],
            ))

    if not comparison_series:
        return

    config = ComparisonConfig(
        title=title,
        x_axis="Elapsed Time (s)",
        y_axis=title.split("(")[-1].replace(")", "") if "(" in title else title,
        series=comparison_series,
        normalize_x=True,  # Already normalized to elapsed seconds
        height=300,
        show_legend=True,
        legend_position="top",
    )
    fig = create_comparison_chart(config)

    card_simple(
        title=f"📈 {title}",
        content="",
        footer=""
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)


def _render_comparison_summary_table(session_data: Dict, session_info: Dict):
    """Render comparison summary table using design system table - RESPONSIVE."""
    comparison_data = []
    for sid, df in session_data.items():
        info = session_info.get(sid, {})
        stats = _calculate_session_stats(df, info)

        comparison_data.append({
            "Session": f"#{sid} - {info.get('session_name', 'Unnamed')}",
            "Scenario": info.get('scenario', 'unknown').title(),
            "Duration": stats.get('duration_formatted', 'N/A'),
            "Peak RPM": f"{stats.get('peak_rpm', 0):,.0f}",
            "Avg RPM": f"{stats.get('avg_rpm', 0):.0f}",
            "Max Speed": f"{stats.get('max_speed', 0):.1f} km/h",
            "Avg Speed": f"{stats.get('avg_speed', 0):.1f} km/h",
            "Distance": f"{stats.get('distance_km', 0):.2f} km",
            "Max Coolant": f"{stats.get('max_coolant_temp', 0):.1f} °C",
            "Max Load": f"{stats.get('max_engine_load', 0):.1f}%",
            "Avg Load": f"{stats.get('avg_load', 0):.1f}%",
            "Records": f"{stats.get('total_records', 0):,}",
            "Data Source": info.get('scenario', 'unknown').upper(),
        })

    # Transpose for better display (metrics as rows, sessions as columns)
    if comparison_data:
        metrics_order = [
            "Duration", "Peak RPM", "Avg RPM", "Max Speed", "Avg Speed",
            "Distance", "Max Coolant", "Max Load", "Avg Load", "Records", "Data Source"
        ]

        transposed = []
        for metric in metrics_order:
            row = {"Metric": metric}
            for i, data in enumerate(comparison_data):
                session_key = f"Session {i+1}"
                if metric in data:
                    row[session_key] = data[metric]
                else:
                    row[session_key] = "N/A"
            transposed.append(row)

        # Dynamic columns based on number of sessions
        session_columns = [f"Session {i+1}" for i in range(len(comparison_data))]
        columns = [TableColumn(key="Metric", header="Metric", width="180px")]
        for sc in session_columns:
            columns.append(TableColumn(key=sc, header=sc, width="160px", align="right"))

        card_simple(
            title="Statistics Comparison",
            content="",
            footer=""
        )
        table(TableProps(
            columns=columns,
            data=transposed,
            striped=True,
            hoverable=True,
            compact=True,
        ))
        st.markdown('</div>', unsafe_allow_html=True)


# ============================================================================
# SESSION WORKFLOW FUNCTIONS (Preserved from original)
# ============================================================================

def _start_recording(db: DatabaseService, session_name: Optional[str] = None):
    """Start a new recording session."""
    obd = get_obd_service()
    status = obd.get_status()

    scenario = st.session_state.get("sim_scenario", status.get("current_scenario", "idle"))

    # Create database session
    if not session_name:
        session_name = f"{scenario.title()} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    session_id = db.create_telemetry_session(session_name, scenario)

    # Start OBD simulation if not already running
    if not status["simulation_running"]:
        if obd.start_simulation(scenario):
            st.session_state.sim_running = True
            st.session_state.session_id = session_id
            st.session_state.telemetry_history = []
            st.session_state.last_update = time.time()
            st.success(f"Recording started: {scenario}")
            st.rerun()
        else:
            st.error("Failed to start simulation")
    else:
        # Simulation already running, just attach to it
        st.session_state.sim_running = True
        st.session_state.session_id = session_id
        st.session_state.telemetry_history = []
        st.session_state.last_update = time.time()
        st.success(f"Recording attached to running simulation: {scenario}")
        st.rerun()


def _stop_recording():
    """Stop the current recording."""
    obd = get_obd_service()
    obd.stop_simulation()
    st.session_state.sim_running = False
    st.success("Recording stopped")
    st.rerun()


def _save_session(db: DatabaseService):
    """Save the current session."""
    session_id = st.session_state.session_id
    if session_id:
        notes = f"Scenario: {st.session_state.sim_scenario}"
        if db.end_telemetry_session(session_id, notes):
            st.success(f"Session #{session_id} saved successfully")
            st.session_state.session_id = None
            st.rerun()
        else:
            st.error("Failed to save session")
    else:
        st.warning("No active session to save")


def _update_telemetry_history(obd, db):
    """Update telemetry history from OBD readings."""
    readings = obd.get_all_readings()

    if readings:
        data_point = {"timestamp": datetime.now().isoformat()}
        for key, reading in readings.items():
            data_point[key] = reading.value

        st.session_state.telemetry_history.append(data_point)

        # Keep only last 300 points (5 minutes at 1Hz)
        if len(st.session_state.telemetry_history) > 300:
            st.session_state.telemetry_history = st.session_state.telemetry_history[-300:]

        # Save to database
        if st.session_state.get("session_id"):
            db.add_telemetry_record(st.session_state.session_id, data_point)

        st.session_state.last_update = time.time()


# ============================================================================
# UTILITY FUNCTIONS (Preserved from original)
# ============================================================================

def _calculate_session_stats(df: pd.DataFrame, session: Dict) -> Dict[str, Any]:
    """Calculate comprehensive session statistics (preserved logic)."""
    stats = {
        "session_id": session["id"],
        "session_name": session.get("session_name", "Unnamed Session"),
        "scenario": session.get("scenario", "unknown"),
        "start_time": session.get("start_time"),
        "end_time": session.get("end_time"),
        "duration_seconds": session.get("duration_seconds"),
        "peak_rpm": session.get("peak_rpm"),
        "max_speed": session.get("max_speed"),
        "avg_speed": session.get("avg_speed"),
        "max_coolant_temp": session.get("max_coolant_temp"),
        "max_engine_load": session.get("max_engine_load"),
    }

    # Calculate from dataframe if not in session
    if stats["peak_rpm"] is None and 'rpm' in df.columns:
        stats["peak_rpm"] = df['rpm'].max()
    if stats["max_speed"] is None and 'speed_kmh' in df.columns:
        stats["max_speed"] = df['speed_kmh'].max()
    if stats["avg_speed"] is None and 'speed_kmh' in df.columns:
        moving_speeds = df[df['speed_kmh'] > 0]['speed_kmh']
        stats["avg_speed"] = moving_speeds.mean() if len(moving_speeds) > 0 else 0
    if stats["max_coolant_temp"] is None and 'coolant_temp_c' in df.columns:
        stats["max_coolant_temp"] = df['coolant_temp_c'].max()
    if stats["max_engine_load"] is None and 'engine_load_pct' in df.columns:
        stats["max_engine_load"] = df['engine_load_pct'].max()

    # Additional calculations
    if stats["duration_seconds"]:
        stats["duration_formatted"] = _format_duration(stats["duration_seconds"])
    else:
        if len(df) > 1:
            start = df['timestamp'].min()
            end = df['timestamp'].max()
            stats["duration_seconds"] = (end - start).total_seconds()
            stats["duration_formatted"] = _format_duration(stats["duration_seconds"])

    # Distance estimation (rough - speed * time)
    if 'speed_kmh' in df.columns and len(df) > 1:
        time_hours = np.arange(len(df)) / 3600.0  # Assuming 1Hz
        stats["distance_km"] = np.trapz(df['speed_kmh'].fillna(0), time_hours)
    else:
        stats["distance_km"] = 0

    # RPM statistics
    if 'rpm' in df.columns:
        stats["avg_rpm"] = df['rpm'].mean()
        stats["time_at_idle"] = len(df[df['rpm'] < 1000]) / len(df) * 100
        stats["time_at_high_rpm"] = len(df[df['rpm'] > 4000]) / len(df) * 100

    # Throttle statistics
    if 'throttle_pos_pct' in df.columns:
        stats["avg_throttle"] = df['throttle_pos_pct'].mean()
        stats["time_wot"] = len(df[df['throttle_pos_pct'] > 90]) / len(df) * 100

    # Engine load statistics
    if 'engine_load_pct' in df.columns:
        stats["avg_load"] = df['engine_load_pct'].mean()

    # Fuel trim statistics
    if 'stft_b1_pct' in df.columns:
        stats["avg_stft"] = df['stft_b1_pct'].mean()
        stats["max_stft"] = df['stft_b1_pct'].max()
        stats["min_stft"] = df['stft_b1_pct'].min()
    if 'ltft_b1_pct' in df.columns:
        stats["avg_ltft"] = df['ltft_b1_pct'].mean()
        stats["max_ltft"] = df['ltft_b1_pct'].max()
        stats["min_ltft"] = df['ltft_b1_pct'].min()

    # Data quality
    stats["total_records"] = len(df)
    stats["data_span_seconds"] = (df['timestamp'].max() - df['timestamp'].min()).total_seconds() if len(df) > 1 else 0

    return stats


def _format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"


def _get_record_count(db: DatabaseService, session_id: int) -> int:
    """Get number of records in a session."""
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM telemetry_records WHERE session_id = ?", (session_id,))
        return cursor.fetchone()[0]


def _export_session_csv(db: DatabaseService, session_id: int):
    """Export a single session as CSV download."""
    records = db.get_session_records(session_id)
    if not records:
        st.warning("No data to export")
        return

    df = pd.DataFrame(records)

    export_cols = {
        'timestamp': 'timestamp',
        'rpm': 'rpm',
        'speed_kmh': 'speed_kmh',
        'coolant_temp_c': 'coolant_temp_c',
        'throttle_pos_pct': 'throttle_pos_pct',
        'engine_load_pct': 'engine_load_pct',
        'intake_pressure_kpa': 'intake_pressure_kpa',
        'stft_b1_pct': 'stft_b1_pct',
        'ltft_b1_pct': 'ltft_b1_pct',
        'voltage_v': 'voltage_v',
        'maf_g_s': 'maf_g_s',
        'map_kpa': 'map_kpa',
        'is_simulated': 'is_simulated'
    }

    export_df = df[list(export_cols.keys())].rename(columns=export_cols)

    csv = export_df.to_csv(index=False)
    session_name = "session"
    session_info = next((s for s in db.get_telemetry_sessions(limit=100) if s["id"] == session_id), None)
    if session_info:
        session_name = session_info.get('session_name', 'session').replace(' ', '_')

    st.download_button(
        label="📥",
        data=csv,
        file_name=f"i20_performance_{session_name}_{session_id}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        key=f"download_{session_id}",
        help="Download CSV",
        use_container_width=True
    )


def _export_multiple_sessions_csv(db: DatabaseService, session_ids: List[int]):
    """Export multiple sessions as combined CSV."""
    all_records = []
    for sid in session_ids:
        records = db.get_session_records(sid)
        for r in records:
            r['session_id'] = sid
        all_records.extend(records)

    if not all_records:
        st.warning("No data to export")
        return

    df = pd.DataFrame(all_records)

    export_cols = {
        'session_id': 'session_id',
        'timestamp': 'timestamp',
        'rpm': 'rpm',
        'speed_kmh': 'speed_kmh',
        'coolant_temp_c': 'coolant_temp_c',
        'throttle_pos_pct': 'throttle_pos_pct',
        'engine_load_pct': 'engine_load_pct',
        'intake_pressure_kpa': 'intake_pressure_kpa',
        'stft_b1_pct': 'stft_b1_pct',
        'ltft_b1_pct': 'ltft_b1_pct',
        'voltage_v': 'voltage_v',
        'maf_g_s': 'maf_g_s',
        'map_kpa': 'map_kpa',
        'is_simulated': 'is_simulated'
    }

    export_df = df[list(export_cols.keys())].rename(columns=export_cols)

    csv = export_df.to_csv(index=False)

    st.download_button(
        label="📥 Download Combined CSV",
        data=csv,
        file_name=f"i20_performance_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        key="download_multiple",
        use_container_width=True
    )
    st.success(f"Exported {len(session_ids)} sessions ({len(all_records)} records)")


def _delete_session(db: DatabaseService, session_id: int):
    """Delete a session and its records."""
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM telemetry_records WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM telemetry_sessions WHERE id = ?", (session_id,))
        conn.commit()
    st.success(f"Session #{session_id} deleted")
    st.rerun()


# Export the main function
__all__ = ["render_performance"]
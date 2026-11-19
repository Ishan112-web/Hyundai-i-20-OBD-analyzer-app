"""
i20 AI Garage - Dashboard Module (Stage 5 Redesign)

Main dashboard with real-time gauges, telemetry cards, live charts, and simulation controls.
Uses Stage 3 design system: tokens, charts_v2, UI components, and global shell.
Fully responsive: mobile-first fluid grid, auto-fit gauges, stacked controls on mobile.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional

from config import (
    SIMULATION_SCENARIOS, ENGINE_SPECS, VEHICLE_INFO
)
from services import get_obd_service, get_database
from services.obd_service import SensorReading

from components.charts_v2 import (
    create_gauge, create_sparkline, create_line_chart,
    SERIES_PALETTE, I20_TEMPLATE
)
from components.ui.components import (
    card_simple, badge, button_primary, button_secondary, button_ghost,
    alert, empty_state, spinner, BadgeVariant
)
from components.ui.tokens import (
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    STATUS_SUCCESS, STATUS_WARNING, STATUS_CRITICAL, STATUS_INFO,
    ACCENT_PRIMARY, ACCENT_SECONDARY,
    SPACE_4, SPACE_5, SPACE_6, SPACE_8,
    RADIUS_MD, RADIUS_LG,
    SHADOW_SM, SHADOW_MD,
    FONT_SIZE_LABEL, FONT_SIZE_BODY, FONT_SIZE_H3,
    FONT_WEIGHT_LABEL, FONT_WEIGHT_H3, FONT_WEIGHT_H4,
)
from components.ui.layout import (
    AUTO_FIT_CARD_CSS, AUTO_FIT_METRIC_CSS,
    grid_container, responsive_container,
    section_header as layout_section_header,
)


# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

def _init_dashboard_state():
    """Initialize dashboard-specific session state keys."""
    if "sim_running" not in st.session_state:
        st.session_state.sim_running = False
    if "sim_scenario" not in st.session_state:
        st.session_state.sim_scenario = "idle"
    if "telemetry_history" not in st.session_state:
        st.session_state.telemetry_history = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "last_update" not in st.session_state:
        st.session_state.last_update = 0


# =============================================================================
# MAIN RENDER FUNCTION
# =============================================================================

def render_dashboard():
    """Render the main dashboard page."""
    _init_dashboard_state()

    obd = get_obd_service()
    db = get_database()

    # Get current OBD status and readings
    status = obd.get_status()
    readings = obd.get_all_readings()

    # Page header with vehicle info and connection status
    _render_page_header(status)

    # Show simulation mode alert
    if status["mode"] == "simulation":
        alert(
            title="Simulation Mode Active",
            message="All displayed values are software-generated for demonstration purposes only. They do not represent actual vehicle sensor readings. Connect a real OBD-II adapter for live data.",
            variant="warning",
        )

    # Main content: responsive two-column layout (stacks on mobile)
    _render_main_content(readings, obd, db, status)


def _render_main_content(readings: Dict[str, SensorReading], obd, db, status: Dict[str, Any]):
    """Render main dashboard content with responsive layout."""
    # Use responsive container for max-width constraint
    st.markdown('<div class="i20-responsive-container">', unsafe_allow_html=True)

    # Responsive grid: gauges+charts (main) | telemetry+controls (sidebar)
    # On mobile these stack vertically; on desktop they sit side by side
    st.markdown(f"""
    <div class="i20-dashboard-grid" style="
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
        gap: var(--i20-gap-page);
    ">
        <div class="i20-dashboard-main">
            {_render_main_column_html(readings, obd)}
        </div>
        <div class="i20-dashboard-sidebar">
            {_render_sidebar_column_html(readings, obd, db, status)}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def _render_main_column_html(readings: Dict[str, SensorReading], obd) -> str:
    """Render main column content as HTML string for grid layout."""
    html_parts = []

    # Primary gauges row - Live Telemetry
    html_parts.append(f"""
    <div style="margin-bottom: var(--i20-gap-section);">
        <h2 class="i20-h3" style="margin: 0 0 var(--i20-gap-field) 0; display: flex; align-items: center; gap: var(--i20-gap-inline);">
            <span>📊</span> Live Telemetry
        </h2>
    </div>
    """)

    # Render 4 gauges in responsive auto-fit grid
    gauge_html = _render_gauge_grid_html(readings, obd)
    html_parts.append(gauge_html)

    # Live multi-series chart
    chart_html = _render_live_charts_html()
    html_parts.append(chart_html)

    return "".join(html_parts)


def _render_sidebar_column_html(readings: Dict[str, SensorReading], obd, db, status: Dict[str, Any]) -> str:
    """Render sidebar column content as HTML string for grid layout."""
    html_parts = []

    # Telemetry cards with sparklines
    telemetry_html = _render_telemetry_cards_html(readings, obd)
    html_parts.append(telemetry_html)

    # Simulation controls - Quick Actions
    html_parts.append(f"""
    <div style="margin-bottom: var(--i20-gap-section);">
        <h2 class="i20-h3" style="margin: 0 0 var(--i20-gap-field) 0; display: flex; align-items: center; gap: var(--i20-gap-inline);">
            <span>⚙️</span> Quick Actions
        </h2>
    </div>
    """)

    controls_html = _render_simulation_controls_html(obd, db, status)
    html_parts.append(controls_html)

    # Status panel - System Status
    html_parts.append(f"""
    <div style="margin-bottom: var(--i20-gap-section);">
        <h2 class="i20-h3" style="margin: 0 0 var(--i20-gap-field) 0; display: flex; align-items: center; gap: var(--i20-gap-inline);">
            <span>🖥️</span> System Status
        </h2>
    </div>
    """)

    status_html = _render_status_panel_html(status)
    html_parts.append(status_html)

    return "".join(html_parts)


# =============================================================================
# PAGE HEADER
# =============================================================================

def _render_page_header(status: Dict[str, Any]):
    """Render the dashboard page header with vehicle info and connection status."""
    mode = status["mode"]
    conn_state = status["connection_state"]

    # Determine connection badge variant
    if conn_state == "connected" and mode == "simulation":
        badge_variant = BadgeVariant.WARNING
        badge_label = "SIMULATION MODE"
    elif conn_state == "connected":
        badge_variant = BadgeVariant.SUCCESS
        badge_label = "CONNECTED"
    elif conn_state == "error":
        badge_variant = BadgeVariant.CRITICAL
        badge_label = "CONNECTION ERROR"
    else:
        badge_variant = BadgeVariant.NEUTRAL
        badge_label = "DISCONNECTED"

    # Render header using columns for layout
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown(f"""
        <div style="
            background: var(--i20-color-bg-card);
            border: 1px solid var(--i20-color-border);
            border-radius: var(--i20-radius-lg);
            padding: var(--i20-spacing-lg) var(--i20-spacing-xl);
            margin-bottom: var(--i20-gap-page);
        ">
            <h1 style="
                margin: 0;
                font-size: var(--i20-font-size-xl);
                font-weight: var(--i20-font-weight-semibold);
                color: var(--i20-color-text-primary);
            ">{VEHICLE_INFO['make']} {VEHICLE_INFO['model']} ({VEHICLE_INFO['year']})</h1>
            <p style="
                margin: var(--i20-spacing-xs) 0 0 0;
                font-size: var(--i20-font-size-sm);
                color: var(--i20-color-text-secondary);
            ">{VEHICLE_INFO['engine']} · {VEHICLE_INFO['transmission']} · {VEHICLE_INFO['fuel_type']}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("<div style='height: 100%; display: flex; align-items: center; justify-content: flex-end;'>", unsafe_allow_html=True)
        badge(label=badge_label, variant=badge_variant)
        st.markdown("</div>", unsafe_allow_html=True)


# =============================================================================
# PRIMARY GAUGES - RESPONSIVE AUTO-FIT GRID
# =============================================================================

def _render_primary_gauges(readings: Dict[str, SensorReading], obd):
    """Render the 4 primary gauges: RPM, Speed, Coolant Temp, Engine Load."""
    # Extract values with defaults
    rpm_val = readings.get("rpm", SensorReading("", "", 0, "")).value
    speed_val = readings.get("speed_kmh", SensorReading("", "", 0, "")).value
    coolant_val = readings.get("coolant_temp_c", SensorReading("", "", 0, "")).value
    load_val = readings.get("engine_load_pct", SensorReading("", "", 0, "")).value

    # Get gauge statuses for threshold coloring
    rpm_status = obd.get_gauge_status("rpm", rpm_val)
    speed_status = obd.get_gauge_status("speed", speed_val)
    coolant_status = obd.get_gauge_status("coolant_temp", coolant_val)
    load_status = obd.get_gauge_status("engine_load", load_val)

    # Gauge configurations
    gauges = [
        {
            "key": "rpm",
            "value": rpm_val,
            "max_val": 7000,
            "title": "RPM",
            "unit": "RPM",
            "thresholds": [3000, 5000, 6500],
            "status": rpm_status,
        },
        {
            "key": "speed",
            "value": speed_val,
            "max_val": 160,
            "title": "SPEED",
            "unit": "km/h",
            "thresholds": [60, 100, 140],
            "status": speed_status,
        },
        {
            "key": "coolant",
            "value": coolant_val,
            "max_val": 130,
            "min_val": -20,
            "title": "COOLANT",
            "unit": "°C",
            "thresholds": [95, 105, 115],
            "status": coolant_status,
        },
        {
            "key": "load",
            "value": load_val,
            "max_val": 100,
            "title": "ENGINE LOAD",
            "unit": "%",
            "thresholds": [50, 80, 100],
            "status": load_status,
        },
    ]

    # Render using responsive auto-fit grid via HTML
    st.markdown(_render_gauge_grid_html(readings, obd), unsafe_allow_html=True)


def _render_gauge_grid_html(readings: Dict[str, SensorReading], obd) -> str:
    """Render gauge grid as HTML for responsive layout."""
    # Extract values with defaults
    rpm_val = readings.get("rpm", SensorReading("", "", 0, "")).value
    speed_val = readings.get("speed_kmh", SensorReading("", "", 0, "")).value
    coolant_val = readings.get("coolant_temp_c", SensorReading("", "", 0, "")).value
    load_val = readings.get("engine_load_pct", SensorReading("", "", 0, "")).value

    rpm_status = obd.get_gauge_status("rpm", rpm_val)
    speed_status = obd.get_gauge_status("speed", speed_val)
    coolant_status = obd.get_gauge_status("coolant_temp", coolant_val)
    load_status = obd.get_gauge_status("engine_load", load_val)

    gauges = [
        {
            "key": "rpm",
            "value": rpm_val,
            "max_val": 7000,
            "title": "RPM",
            "unit": "RPM",
            "thresholds": [3000, 5000, 6500],
            "status": rpm_status,
        },
        {
            "key": "speed",
            "value": speed_val,
            "max_val": 160,
            "title": "SPEED",
            "unit": "km/h",
            "thresholds": [60, 100, 140],
            "status": speed_status,
        },
        {
            "key": "coolant",
            "value": coolant_val,
            "max_val": 130,
            "min_val": -20,
            "title": "COOLANT",
            "unit": "°C",
            "thresholds": [95, 105, 115],
            "status": coolant_status,
        },
        {
            "key": "load",
            "value": load_val,
            "max_val": 100,
            "title": "ENGINE LOAD",
            "unit": "%",
            "thresholds": [50, 80, 100],
            "status": load_status,
        },
    ]

    gauge_items = []
    for config in gauges:
        gauge_html = _render_single_gauge_html(config)
        gauge_items.append(gauge_html)

    # Use responsive auto-fit grid for gauges (min 280px per gauge)
    return grid_container(gauge_items, grid_type="gauge")


def _render_single_gauge_html(config: Dict[str, Any]) -> str:
    """Render a single gauge as HTML string."""
    # Map status to gauge color zone
    status_color_map = {
        "green": STATUS_SUCCESS,
        "amber": STATUS_WARNING,
        "red": STATUS_CRITICAL,
        "blue": ACCENT_PRIMARY,
    }
    zone_color = status_color_map.get(config["status"]["color"], ACCENT_PRIMARY)

    # Create gauge using charts_v2 factory
    fig = create_gauge(
        value=config["value"],
        min_value=config.get("min_val", 0),
        max_value=config["max_val"],
        title=config["title"],
        unit=config["unit"],
        thresholds=config["thresholds"],
        zone_colors=[
            STATUS_SUCCESS + "33",  # 20% opacity
            STATUS_WARNING + "33",
            STATUS_CRITICAL + "33",
        ],
        needle_color=zone_color,
        height=200,
    )

    # Render gauge in a card - use HTML container with plotly chart
    # Note: For HTML string, we need to render the chart separately
    # We'll use a placeholder and render actual charts via Streamlit
    # This is a limitation - we'll render gauges via Streamlit columns instead
    return f"""
    <div class="i20-gauge-card" data-gauge-key="{config['key']}" style="
        background: var(--i20-color-bg-card);
        border: 1px solid var(--i20-color-border);
        border-radius: var(--i20-radius-md);
        padding: var(--i20-spacing-md);
        min-height: 240px;
        display: flex;
        flex-direction: column;
    ">
        <div class="i20-gauge-title" style="
            font-size: var(--i20-font-size-label);
            font-weight: var(--i20-font-weight-label);
            text-transform: uppercase;
            letter-spacing: var(--i20-letter-spacing-label);
            color: var(--i20-color-text-secondary);
            margin-bottom: var(--i20-spacing-sm);
            text-align: center;
        ">{config['title']}</div>
        <div class="i20-gauge-chart" style="flex: 1; min-height: 200px;"></div>
    </div>
    """


def _render_gauges_via_streamlit():
    """Render gauges using Streamlit columns (fallback for actual chart rendering)."""
    # This will be called from the main render function
    pass


# =============================================================================
# TELEMETRY CARDS WITH SPARKLINES
# =============================================================================

def _render_telemetry_cards(readings: Dict[str, SensorReading], obd):
    """Render detailed telemetry cards with values and sparklines."""
    st.markdown("""
    <div style="
        background: var(--i20-color-bg-card);
        border: 1px solid var(--i20-color-border);
        border-radius: var(--i20-radius-lg);
        padding: var(--i20-spacing-md);
        margin-bottom: var(--i20-gap-lg);
    ">
        <h3 style="
            margin: 0 0 var(--i20-spacing-md) 0;
            font-size: var(--i20-font-size-sm);
            font-weight: var(--i20-font-weight-semibold);
            color: var(--i20-color-text-secondary);
            text-transform: uppercase;
            letter-spacing: var(--i20-letter-spacing-label);
        ">Detailed Telemetry</h3>
    </div>
    """, unsafe_allow_html=True)

    # Define telemetry items: (key, label, unit, threshold_key, history_key)
    telemetry_items = [
        ("rpm", "Engine RPM", "RPM", "rpm", "rpm"),
        ("speed_kmh", "Vehicle Speed", "km/h", "speed", "speed_kmh"),
        ("coolant_temp_c", "Coolant Temp", "°C", "coolant_temp", "coolant_temp_c"),
        ("throttle_pos_pct", "Throttle Position", "%", "throttle", "throttle_pos_pct"),
        ("engine_load_pct", "Engine Load", "%", "engine_load", "engine_load_pct"),
        ("intake_pressure_kpa", "Intake Pressure", "kPa", None, "intake_pressure_kpa"),
        ("stft_b1_pct", "STFT Bank 1", "%", "fuel_trim", "stft_b1_pct"),
        ("ltft_b1_pct", "LTFT Bank 1", "%", "fuel_trim", "ltft_b1_pct"),
        ("voltage_v", "Battery Voltage", "V", "voltage", "voltage_v"),
        ("maf_g_s", "MAF Rate", "g/s", None, "maf_g_s"),
    ]

    # Get history for sparklines
    history = st.session_state.get("telemetry_history", [])
    history_df = pd.DataFrame(history) if history else pd.DataFrame()
    if not history_df.empty and "timestamp" in history_df.columns:
        history_df["timestamp"] = pd.to_datetime(history_df["timestamp"])

    for key, label, unit, threshold_key, history_key in telemetry_items:
        reading = readings.get(key)
        if not reading:
            continue

        value = reading.value

        # Get status color
        if threshold_key:
            status = obd.get_gauge_status(threshold_key, value)
            status_color_map = {
                "green": STATUS_SUCCESS,
                "amber": STATUS_WARNING,
                "red": STATUS_CRITICAL,
                "blue": ACCENT_PRIMARY,
            }
            dot_color = status_color_map.get(status["color"], ACCENT_PRIMARY)
        else:
            dot_color = ACCENT_PRIMARY

        # Get history data for sparkline
        sparkline_data = []
        if not history_df.empty and history_key in history_df.columns:
            sparkline_data = history_df[history_key].dropna().tolist()[-50:]  # Last 50 points

        # Render telemetry card
        _render_telemetry_card(label, value, unit, dot_color, sparkline_data)


def _render_telemetry_cards_html(readings: Dict[str, SensorReading], obd) -> str:
    """Render telemetry cards as HTML for responsive sidebar layout."""
    # This generates the cards HTML - sparklines will be rendered via Streamlit
    # We use a hybrid approach: HTML for structure, Streamlit for charts
    html = """
    <div class="i20-telemetry-cards" style="
        display: flex;
        flex-direction: column;
        gap: var(--i20-spacing-sm);
    ">
    """

    telemetry_items = [
        ("rpm", "Engine RPM", "RPM", "rpm", "rpm"),
        ("speed_kmh", "Vehicle Speed", "km/h", "speed", "speed_kmh"),
        ("coolant_temp_c", "Coolant Temp", "°C", "coolant_temp", "coolant_temp_c"),
        ("throttle_pos_pct", "Throttle Position", "%", "throttle", "throttle_pos_pct"),
        ("engine_load_pct", "Engine Load", "%", "engine_load", "engine_load_pct"),
        ("intake_pressure_kpa", "Intake Pressure", "kPa", None, "intake_pressure_kpa"),
        ("stft_b1_pct", "STFT Bank 1", "%", "fuel_trim", "stft_b1_pct"),
        ("ltft_b1_pct", "LTFT Bank 1", "%", "fuel_trim", "ltft_b1_pct"),
        ("voltage_v", "Battery Voltage", "V", "voltage", "voltage_v"),
        ("maf_g_s", "MAF Rate", "g/s", None, "maf_g_s"),
    ]

    history = st.session_state.get("telemetry_history", [])
    history_df = pd.DataFrame(history) if history else pd.DataFrame()
    if not history_df.empty and "timestamp" in history_df.columns:
        history_df["timestamp"] = pd.to_datetime(history_df["timestamp"])

    for key, label, unit, threshold_key, history_key in telemetry_items:
        reading = readings.get(key)
        if not reading:
            continue

        value = reading.value

        if threshold_key:
            status = obd.get_gauge_status(threshold_key, value)
            status_color_map = {
                "green": STATUS_SUCCESS,
                "amber": STATUS_WARNING,
                "red": STATUS_CRITICAL,
                "blue": ACCENT_PRIMARY,
            }
            dot_color = status_color_map.get(status["color"], ACCENT_PRIMARY)
        else:
            dot_color = ACCENT_PRIMARY

        html += f"""
        <div class="i20-telemetry-card" style="
            background: var(--i20-color-bg-card);
            border: 1px solid var(--i20-color-border);
            border-radius: var(--i20-radius-md);
            padding: var(--i20-spacing-md);
            transition: border-color 0.2s;
        " onmouseover="this.style.borderColor='var(--i20-color-accent-primary)'" onmouseout="this.style.borderColor='var(--i20-color-border)'">
            <div style="
                font-size: var(--i20-font-size-xs);
                font-weight: var(--i20-font-weight-semibold);
                text-transform: uppercase;
                letter-spacing: var(--i20-letter-spacing-label);
                color: var(--i20-color-text-secondary);
                margin-bottom: var(--i20-spacing-xs);
            ">{label}</div>
            <div style="display: flex; align-items: baseline; gap: var(--i20-spacing-xs);">
                <span style="
                    font-size: var(--i20-font-size-lg);
                    font-weight: var(--i20-font-weight-bold);
                    color: var(--i20-color-text-primary);
                    font-variant-numeric: tabular-nums;
                ">{value:.1f}</span>
                <span style="
                    font-size: var(--i20-font-size-xs);
                    color: var(--i20-color-text-secondary);
                ">{unit}</span>
                <span style="
                    display: inline-block;
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background: {dot_color};
                    margin-left: var(--i20-spacing-xs);
                "></span>
            </div>
        </div>
        """

    html += "</div>"
    return html


def _render_telemetry_card(label: str, value: float, unit: str, dot_color: str, sparkline_data: List[float]):
    """Render a single telemetry card with value and optional sparkline."""
    card_html = f"""
    <div style="
        background: var(--i20-color-bg-card);
        border: 1px solid var(--i20-color-border);
        border-radius: var(--i20-radius-md);
        padding: var(--i20-spacing-md);
        margin-bottom: var(--i20-spacing-sm);
        transition: border-color 0.2s;
    " onmouseover="this.style.borderColor='var(--i20-color-accent-primary)'" onmouseout="this.style.borderColor='var(--i20-color-border)'">
        <div style="
            font-size: var(--i20-font-size-xs);
            font-weight: var(--i20-font-weight-semibold);
            text-transform: uppercase;
            letter-spacing: var(--i20-letter-spacing-label);
            color: var(--i20-color-text-secondary);
            margin-bottom: var(--i20-spacing-xs);
        ">{label}</div>
        <div style="display: flex; align-items: baseline; gap: var(--i20-spacing-xs);">
            <span style="
                font-size: var(--i20-font-size-lg);
                font-weight: var(--i20-font-weight-bold);
                color: var(--i20-color-text-primary);
                font-variant-numeric: tabular-nums;
            ">{value:.1f}</span>
            <span style="
                font-size: var(--i20-font-size-xs);
                color: var(--i20-color-text-secondary);
            ">{unit}</span>
            <span style="
                display: inline-block;
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: {dot_color};
                margin-left: var(--i20-spacing-xs);
            "></span>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    # Render sparkline if data available
    if sparkline_data and len(sparkline_data) > 1:
        fig = create_sparkline(
            data=sparkline_data,
            color=dot_color,
            height=40,
            show_area=True,
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


# =============================================================================
# LIVE MULTI-SERIES CHART
# =============================================================================

def _render_live_charts():
    """Render the live multi-series telemetry chart."""
    history = st.session_state.get("telemetry_history", [])

    if len(history) < 2:
        empty_state(
            title="No Telemetry Data",
            message="Start a simulation to see live telemetry charts",
            icon="📈",
        )
        return

    # Convert history to DataFrame
    df = pd.DataFrame(history)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Define series to plot
    series_config = [
        {"column": "rpm", "name": "RPM", "color": SERIES_PALETTE[0], "unit": "RPM"},
        {"column": "speed_kmh", "name": "Speed", "color": SERIES_PALETTE[1], "unit": "km/h"},
        {"column": "coolant_temp_c", "name": "Coolant", "color": SERIES_PALETTE[2], "unit": "°C"},
        {"column": "throttle_pos_pct", "name": "Throttle", "color": SERIES_PALETTE[3], "unit": "%"},
        {"column": "engine_load_pct", "name": "Load", "color": SERIES_PALETTE[4], "unit": "%"},
    ]

    # Filter to only series that exist in data
    available_series = [s for s in series_config if s["column"] in df.columns]

    # Create multi-series line chart
    fig = create_line_chart(
        df=df,
        x="timestamp",
        series=[{"column": s["column"], "name": s["name"], "color": s["color"]} for s in available_series],
        title="Live Telemetry",
        x_title="Time",
        y_title="Value",
        height=400,
        show_legend=True,
    )

    card_simple(
        title="Live Telemetry",
        content_fn=lambda: st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}),
        padding="md",
    )


def _render_live_charts_html() -> str:
    """Render live charts section as HTML for grid layout."""
    history = st.session_state.get("telemetry_history", [])

    if len(history) < 2:
        return f"""
        <div class="i20-chart-container" style="
            background: var(--i20-color-bg-card);
            border: 1px solid var(--i20-color-border);
            border-radius: var(--i20-radius-md);
            padding: var(--i20-spacing-lg);
            text-align: center;
            color: var(--i20-color-text-secondary);
            min-height: 200px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        ">
            <span style="font-size: 3rem;">📈</span>
            <h3 style="margin: var(--i20-spacing-md) 0 var(--i20-spacing-sm) 0;">No Telemetry Data</h3>
            <p style="margin: 0;">Start a simulation to see live telemetry charts</p>
        </div>
        """

    return """
    <div class="i20-chart-container" style="
        background: var(--i20-color-bg-card);
        border: 1px solid var(--i20-color-border);
        border-radius: var(--i20-radius-md);
        padding: var(--i20-spacing-md);
        min-height: 400px;
    ">
        <div class="i20-live-chart" style="width: 100%; height: 400px;"></div>
    </div>
    """


# =============================================================================
# SIMULATION CONTROLS - RESPONSIVE
# =============================================================================

def _render_simulation_controls(obd, db, status: Dict[str, Any]):
    """Render simulation control panel."""
    card_simple(
        title="Simulation Controls",
        content_fn=lambda: _render_simulation_controls_content(obd, db, status),
        padding="lg",
    )


def _render_simulation_controls_html(obd, db, status: Dict[str, Any]) -> str:
    """Render simulation controls as HTML for responsive layout."""
    scenarios = obd.get_available_scenarios()
    scenario_options = {k: v["name"] for k, v in scenarios.items()}
    selected = st.session_state.get("sim_scenario", "idle")

    html = f"""
    <div class="i20-simulation-controls" style="
        background: var(--i20-color-bg-card);
        border: 1px solid var(--i20-color-border);
        border-radius: var(--i20-radius-lg);
        padding: var(--i20-spacing-lg);
    ">
        <div style="margin-bottom: var(--i20-spacing-md);">
            <label style="
                display: block;
                font-size: var(--i20-font-size-label);
                font-weight: var(--i20-font-weight-label);
                color: var(--i20-color-text-secondary);
                margin-bottom: var(--i20-spacing-xs);
                text-transform: uppercase;
                letter-spacing: var(--i20-letter-spacing-label);
            ">Scenario</label>
            <div class="i20-scenario-select" data-selected="{selected}">
    """

    for key, name in scenario_options.items():
        selected_attr = ' selected' if key == selected else ''
        html += f'<option value="{key}"{selected_attr}>{name}</option>'

    html += f"""
            </div>
        </div>
        <div class="i20-scenario-description" style="
            font-size: var(--i20-font-size-sm);
            color: var(--i20-color-text-secondary);
            margin-bottom: var(--i20-spacing-md);
        ">{scenarios[selected]['description']}</div>
        <div class="i20-control-buttons" style="
            display: flex;
            flex-wrap: wrap;
            gap: var(--i20-spacing-sm);
            margin-top: var(--i20-spacing-md);
        ">
            <button class="i20-btn i20-btn-primary" style="flex: 1; min-width: 120px; padding: var(--i20-spacing-sm) var(--i20-spacing-md);" data-action="start" {'disabled' if st.session_state.get('sim_running') else ''}>▶ Start</button>
            <button class="i20-btn i20-btn-secondary" style="flex: 1; min-width: 120px; padding: var(--i20-spacing-sm) var(--i20-spacing-md);" data-action="stop" {'disabled' if not st.session_state.get('sim_running') else ''}>■ Stop</button>
            <button class="i20-btn i20-btn-ghost" style="flex: 1; min-width: 120px; padding: var(--i20-spacing-sm) var(--i20-spacing-md);" data-action="reset">↻ Reset</button>
        </div>
"""

    # Session recording controls
    if st.session_state.get("sim_running") and st.session_state.get("session_id"):
        session_id = st.session_state.session_id
        html += f"""
        <hr style="margin: var(--i20-spacing-md) 0; border-color: var(--i20-color-border);">
        <div style="
            display: flex;
            align-items: center;
            gap: var(--i20-spacing-sm);
            color: var(--i20-color-status-critical);
            font-weight: var(--i20-font-weight-medium);
            font-size: var(--i20-font-size-sm);
        ">
            <span style="
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: var(--i20-color-status-critical);
                animation: pulse 1s infinite;
            "></span>
            <span>Recording Session #{session_id}</span>
        </div>
        <style>
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        </style>
        <button class="i20-btn i20-btn-secondary" style="width: 100%; margin-top: var(--i20-spacing-md); padding: var(--i20-spacing-sm) var(--i20-spacing-md);" data-action="save">💾 Save Session</button>
        """

    html += "</div>"
    return html


def _render_simulation_controls_content(obd, db, status: Dict[str, Any]):
    """Render simulation controls content."""
    # Scenario selector
    scenarios = obd.get_available_scenarios()
    scenario_options = {k: v["name"] for k, v in scenarios.items()}

    selected_scenario = st.selectbox(
        "Scenario",
        options=list(scenario_options.keys()),
        format_func=lambda x: scenario_options[x],
        index=list(scenario_options.keys()).index(st.session_state.sim_scenario) if st.session_state.sim_scenario in scenario_options else 0,
        key="scenario_selector_dashboard",
    )
    st.session_state.sim_scenario = selected_scenario

    # Scenario description
    st.caption(scenarios[selected_scenario]["description"])

    st.markdown("<div style='margin-top: var(--i20-spacing-md);'></div>", unsafe_allow_html=True)

    # Control buttons - responsive: stack on mobile, row on desktop
    col1, col2, col3 = st.columns(3, gap="small")

    with col1:
        if button_primary(
            label="▶ Start",
            disabled=st.session_state.sim_running,
            use_container_width=True,
            key="sim_start_btn",
        ):
            _start_simulation(obd, db)

    with col2:
        if button_secondary(
            label="■ Stop",
            disabled=not st.session_state.sim_running,
            use_container_width=True,
            key="sim_stop_btn",
        ):
            _stop_simulation()

    with col3:
        if button_ghost(
            label="↻ Reset",
            use_container_width=True,
            key="sim_reset_btn",
        ):
            _reset_simulation()

    # Session recording controls
    if st.session_state.sim_running and st.session_state.session_id:
        st.markdown("<hr style='margin: var(--i20-spacing-md) 0; border-color: var(--i20-color-border);'>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="
            display: flex;
            align-items: center;
            gap: var(--i20-spacing-sm);
            color: var(--i20-color-status-critical);
            font-weight: var(--i20-font-weight-medium);
            font-size: var(--i20-font-size-sm);
        ">
            <span style="
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: var(--i20-color-status-critical);
                animation: pulse 1s infinite;
            "></span>
            <span>Recording Session #{st.session_state.session_id}</span>
        </div>
        <style>
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        </style>
        """, unsafe_allow_html=True)

        if button_secondary(
            label="💾 Save Session",
            use_container_width=True,
            key="sim_save_btn",
        ):
            _save_session(db)


def _start_simulation(obd, db):
    """Start simulation and create telemetry session."""
    scenario = st.session_state.sim_scenario

    # Create database session
    session_name = f"{scenario.title()} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    session_id = db.create_telemetry_session(session_name, scenario)

    # Start OBD simulation
    if obd.start_simulation(scenario):
        st.session_state.sim_running = True
        st.session_state.session_id = session_id
        st.session_state.telemetry_history = []
        st.success(f"Simulation started: {scenario}")
        st.rerun()
    else:
        st.error("Failed to start simulation")


def _stop_simulation():
    """Stop simulation."""
    obd = get_obd_service()
    obd.stop_simulation()
    st.session_state.sim_running = False
    st.success("Simulation stopped")
    st.rerun()


def _reset_simulation():
    """Reset simulation and clear history."""
    obd = get_obd_service()
    obd.stop_simulation()
    st.session_state.sim_running = False
    st.session_state.telemetry_history = []
    st.session_state.session_id = None
    st.success("Simulation reset")
    st.rerun()


def _save_session(db):
    """Save current telemetry session."""
    session_id = st.session_state.session_id
    if session_id:
        notes = f"Scenario: {st.session_state.sim_scenario}"
        if db.end_telemetry_session(session_id, notes):
            st.success(f"Session #{session_id} saved successfully")
        else:
            st.error("Failed to save session")
    else:
        st.warning("No active session to save")


# =============================================================================
# STATUS PANEL
# =============================================================================

def _render_status_panel(status: Dict[str, Any]):
    """Render system status information panel."""
    card_simple(
        title="System Status",
        content_fn=lambda: _render_status_panel_content(status),
        padding="lg",
    )


def _render_status_panel_html(status: Dict[str, Any]) -> str:
    """Render status panel as HTML for responsive layout."""
    status_items = [
        ("OBD Mode", status["mode"].upper()),
        ("Connection", status["connection_state"].title()),
        ("Port", status["port"]),
        ("Simulation", "Running" if status["simulation_running"] else "Stopped"),
        ("Scenario", status["current_scenario"].title()),
        ("Supported PIDs", str(status["supported_pids_count"])),
        ("Last Update", status["last_update"][:19] if status["last_update"] else "Never"),
    ]

    html = """
    <div class="i20-status-panel" style="
        background: var(--i20-color-bg-card);
        border: 1px solid var(--i20-color-border);
        border-radius: var(--i20-radius-lg);
        padding: var(--i20-spacing-lg);
    ">
    """

    for label, value in status_items:
        html += f"""
        <div style="
            display: flex;
            justify-content: space-between;
            padding: var(--i20-spacing-xs) 0;
            border-bottom: 1px solid var(--i20-color-border);
        ">
            <span style="
                font-size: var(--i20-font-size-sm);
                color: var(--i20-color-text-secondary);
            ">{label}</span>
            <span style="
                font-size: var(--i20-font-size-sm);
                font-weight: var(--i20-font-weight-semibold);
                color: var(--i20-color-text-primary);
            ">{value}</span>
        </div>
        """

    html += "</div>"
    return html


def _render_status_panel_content(status: Dict[str, Any]):
    """Render status panel content."""
    status_items = [
        ("OBD Mode", status["mode"].upper()),
        ("Connection", status["connection_state"].title()),
        ("Port", status["port"]),
        ("Simulation", "Running" if status["simulation_running"] else "Stopped"),
        ("Scenario", status["current_scenario"].title()),
        ("Supported PIDs", str(status["supported_pids_count"])),
        ("Last Update", status["last_update"][:19] if status["last_update"] else "Never"),
    ]

    for label, value in status_items:
        st.markdown(f"""
        <div style="
            display: flex;
            justify-content: space-between;
            padding: var(--i20-spacing-xs) 0;
            border-bottom: 1px solid var(--i20-color-border);
        ">
            <span style="
                font-size: var(--i20-font-size-sm);
                color: var(--i20-color-text-secondary);
            ">{label}</span>
            <span style="
                font-size: var(--i20-font-size-sm);
                font-weight: var(--i20-font-weight-semibold);
                color: var(--i20-color-text-primary);
            ">{value}</span>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# AUTO-UPDATE TELEMETRY HISTORY (called from main app loop)
# =============================================================================

def update_telemetry_history():
    """Update telemetry history from OBD readings (call from main app loop)."""
    if st.session_state.get("sim_running", False):
        obd = get_obd_service()
        db = get_database()
        readings = obd.get_all_readings()

        if readings:
            # Add timestamp
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


# =============================================================================
# RENDER GAUGES VIA STREAMLIT (for actual chart rendering)
# =============================================================================

def render_gauges_streamlit(readings: Dict[str, SensorReading], obd):
    """Render the 4 primary gauges using Streamlit columns (for actual Plotly rendering)."""
    # Extract values with defaults
    rpm_val = readings.get("rpm", SensorReading("", "", 0, "")).value
    speed_val = readings.get("speed_kmh", SensorReading("", "", 0, "")).value
    coolant_val = readings.get("coolant_temp_c", SensorReading("", "", 0, "")).value
    load_val = readings.get("engine_load_pct", SensorReading("", "", 0, "")).value

    # Get gauge statuses for threshold coloring
    rpm_status = obd.get_gauge_status("rpm", rpm_val)
    speed_status = obd.get_gauge_status("speed", speed_val)
    coolant_status = obd.get_gauge_status("coolant_temp", coolant_val)
    load_status = obd.get_gauge_status("engine_load", load_val)

    # Gauge configurations
    gauges = [
        {
            "key": "rpm",
            "value": rpm_val,
            "max_val": 7000,
            "title": "RPM",
            "unit": "RPM",
            "thresholds": [3000, 5000, 6500],
            "status": rpm_status,
        },
        {
            "key": "speed",
            "value": speed_val,
            "max_val": 160,
            "title": "SPEED",
            "unit": "km/h",
            "thresholds": [60, 100, 140],
            "status": speed_status,
        },
        {
            "key": "coolant",
            "value": coolant_val,
            "max_val": 130,
            "min_val": -20,
            "title": "COOLANT",
            "unit": "°C",
            "thresholds": [95, 105, 115],
            "status": coolant_status,
        },
        {
            "key": "load",
            "value": load_val,
            "max_val": 100,
            "title": "ENGINE LOAD",
            "unit": "%",
            "thresholds": [50, 80, 100],
            "status": load_status,
        },
    ]

    # Use responsive columns - Streamlit doesn't support truly responsive columns
    # but we use 4 columns as base; CSS grid will handle wrapping
    cols = st.columns(4, gap="medium")

    for idx, gauge_config in enumerate(gauges):
        with cols[idx]:
            _render_single_gauge(gauge_config)


def _render_single_gauge(config: Dict[str, Any]):
    """Render a single gauge using charts_v2.create_gauge()."""
    # Map status to gauge color zone
    status_color_map = {
        "green": STATUS_SUCCESS,
        "amber": STATUS_WARNING,
        "red": STATUS_CRITICAL,
        "blue": ACCENT_PRIMARY,
    }
    zone_color = status_color_map.get(config["status"]["color"], ACCENT_PRIMARY)

    # Create gauge using charts_v2 factory
    fig = create_gauge(
        value=config["value"],
        min_value=config.get("min_val", 0),
        max_value=config["max_val"],
        title=config["title"],
        unit=config["unit"],
        thresholds=config["thresholds"],
        zone_colors=[
            STATUS_SUCCESS + "33",  # 20% opacity
            STATUS_WARNING + "33",
            STATUS_CRITICAL + "33",
        ],
        needle_color=zone_color,
        height=200,
    )

    # Render in a card container
    card_simple(
        title="",
        content_fn=lambda: st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}),
        padding="md",
    )


def render_live_chart_streamlit():
    """Render the live multi-series telemetry chart via Streamlit."""
    history = st.session_state.get("telemetry_history", [])

    if len(history) < 2:
        empty_state(
            title="No Telemetry Data",
            message="Start a simulation to see live telemetry charts",
            icon="📈",
        )
        return

    # Convert history to DataFrame
    df = pd.DataFrame(history)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Define series to plot
    series_config = [
        {"column": "rpm", "name": "RPM", "color": SERIES_PALETTE[0], "unit": "RPM"},
        {"column": "speed_kmh", "name": "Speed", "color": SERIES_PALETTE[1], "unit": "km/h"},
        {"column": "coolant_temp_c", "name": "Coolant", "color": SERIES_PALETTE[2], "unit": "°C"},
        {"column": "throttle_pos_pct", "name": "Throttle", "color": SERIES_PALETTE[3], "unit": "%"},
        {"column": "engine_load_pct", "name": "Load", "color": SERIES_PALETTE[4], "unit": "%"},
    ]

    # Filter to only series that exist in data
    available_series = [s for s in series_config if s["column"] in df.columns]

    # Create multi-series line chart
    fig = create_line_chart(
        df=df,
        x="timestamp",
        series=[{"column": s["column"], "name": s["name"], "color": s["color"]} for s in available_series],
        title="Live Telemetry",
        x_title="Time",
        y_title="Value",
        height=400,
        show_legend=True,
    )

    card_simple(
        title="Live Telemetry",
        content_fn=lambda: st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}),
        padding="md",
    )
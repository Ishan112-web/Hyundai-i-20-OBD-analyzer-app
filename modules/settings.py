"""
i20 AI Garage - Settings Module

Comprehensive settings page with LM Studio configuration, AI model selection,
OBD mode settings, simulation parameters, data export, backup, and app info.

Redesigned using Phase 6 Stage 3 Design System - zero custom CSS.
"""

import streamlit as st
import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

from config import (
    LM_STUDIO_BASE_URL,
    LM_STUDIO_MODEL,
    LM_STUDIO_TEMPERATURE,
    LM_STUDIO_TIMEOUT,
    OBD_MODE,
    SIMULATION_INTERVAL,
    TELEMETRY_REFRESH_INTERVAL,
    VEHICLE_INFO,
    ENGINE_SPECS,
    SIMULATION_SCENARIOS,
)
from services import get_database, get_ai_service
from services.ai_service import AIServiceError

# Design System imports
from components.ui import (
    # Layout
    inject_global_css,
    initialize_layout,
    page_header,
    section_header,
    card,
    card_simple,
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
    text_input,
    selectbox,
    empty_state,
    EmptyStateProps,
    spinner,
    # Tokens
    ACCENT_PRIMARY,
    STATUS_SUCCESS,
    STATUS_WARNING,
    STATUS_CRITICAL,
    STATUS_INFO,
    STATUS_NEUTRAL,
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
    FONT_SIZE_LABEL,
    FONT_SIZE_BODY,
    FONT_SIZE_BODY_SM,
    FONT_SIZE_CAPTION,
    FONT_SIZE_H1, FONT_SIZE_H2, FONT_SIZE_H3,
    BUTTON_FONT_WEIGHT,
    RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_PILL,
    SHADOW_SM, SHADOW_MD, SHADOW_FOCUS,
    TRANSITION_FAST, TRANSITION_NORMAL,
    FONT_FAMILY_MONO,
)

logger = logging.getLogger(__name__)


def announce_settings_change(message: str, live_region_id: str = "settings-changes-live") -> None:
    """Announce a settings change to the live region (B1.14)."""
    announce_script = f'''
    <script>
    (function() {{
        const region = document.getElementById('{live_region_id}');
        if (region) {{
            region.textContent = '{message}';
        }}
    }})();
    </script>
    '''
    st.markdown(announce_script, unsafe_allow_html=True)


# Settings keys for database storage
SETTINGS_KEYS = {
    # LM Studio / AI Settings
    "lm_studio_base_url": "LM Studio API endpoint URL",
    "lm_studio_model": "AI model identifier",
    "lm_studio_temperature": "AI response temperature (0.0-2.0)",
    "lm_studio_timeout": "AI request timeout in seconds",
    # OBD Settings
    "obd_mode": "OBD connection mode (simulation/real)",
    "obd_port": "OBD-II serial port",
    "obd_baudrate": "OBD-II baud rate",
    "obd_protocol": "OBD-II protocol",
    # Simulation Settings
    "simulation_interval": "Simulation update interval (seconds)",
    "telemetry_refresh_interval": "Telemetry refresh interval (seconds)",
    # UI Settings
    "theme_mode": "UI theme mode",
    "auto_refresh": "Auto-refresh dashboard data",
}


def render_settings():
    """Render the complete settings page with B1.14 live region for settings confirmations."""
    db = get_database()
    ai_service = get_ai_service()

    # Initialize session state for settings
    _init_settings_state(db)

    # Design System: Global CSS + Layout initialization
    st.markdown(inject_global_css(), unsafe_allow_html=True)
    st.markdown(initialize_layout(), unsafe_allow_html=True)

    # Live region for settings change confirmations (B1.14)
    settings_live_region_id = "settings-changes-live"
    st.markdown(f'<div id="{settings_live_region_id}" class="i20-live-region i20-visually-hidden" aria-live="polite" aria-atomic="true" aria-label="Settings changes"></div>', unsafe_allow_html=True)

    # Page header using Design System
    page_header(
        title="Settings",
        icon="⚙️",
        description="Configure i20 AI Garage preferences, connections, and system settings"
    )

    # Create tabs for different settings categories (preserve exact tab order)
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🤖 AI & LM Studio",
        "🔌 OBD Connection",
        "🎮 Simulation",
        "📊 Data & Export",
        "💾 Backup & Restore",
        "ℹ️ About",
    ])

    with tab1:
        render_ai_settings(db, ai_service)

    with tab2:
        render_obd_settings(db)

    with tab3:
        render_simulation_settings(db)

    with tab4:
        render_data_export_settings(db)

    with tab5:
        render_backup_settings(db)

    with tab6:
        render_about_settings()


def _init_settings_state(db):
    """Initialize session state with current settings from database."""
    defaults = {
        "lm_studio_base_url": LM_STUDIO_BASE_URL,
        "lm_studio_model": LM_STUDIO_MODEL,
        "lm_studio_temperature": LM_STUDIO_TEMPERATURE,
        "lm_studio_timeout": LM_STUDIO_TIMEOUT,
        "obd_mode": OBD_MODE,
        "obd_port": "COM3",
        "obd_baudrate": 38400,
        "obd_protocol": "auto",
        "simulation_interval": SIMULATION_INTERVAL,
        "telemetry_refresh_interval": TELEMETRY_REFRESH_INTERVAL,
        "theme_mode": "dark",
        "auto_refresh": True,
    }

    for key, default in defaults.items():
        if key not in st.session_state:
            # Try to get from database first, then config default
            db_value = db.get_setting(key)
            if db_value is not None:
                # Convert types appropriately
                if key in ["lm_studio_temperature", "simulation_interval", "telemetry_refresh_interval"]:
                    st.session_state[key] = float(db_value)
                elif key in ["lm_studio_timeout", "obd_baudrate"]:
                    st.session_state[key] = int(db_value)
                elif key in ["auto_refresh"]:
                    st.session_state[key] = db_value.lower() == "true"
                else:
                    st.session_state[key] = db_value
            else:
                st.session_state[key] = default


# =============================================================================
# Tab 1: AI & LM Studio Settings
# =============================================================================

def render_ai_settings(db, ai_service):
    """Render AI & LM Studio settings."""
    # Section: LM Studio Connection
    section_header(
        title="LM Studio Connection",
        description="Configure the connection to your local LM Studio server for AI-powered diagnostics.",
        icon="🤖"
    )

    # Connection status check
    col1, col2 = st.columns([3, 1])
    with col1:
        base_url = text_input(
            label="LM Studio Base URL",
            key="lm_studio_base_url_input",
            value=st.session_state.lm_studio_base_url,
            placeholder="http://localhost:1234/v1",
            help="The base URL for your LM Studio OpenAI-compatible API server",
        )
    with col2:
        st.write("")
        st.write("")
        if button_secondary("🔍 Test Connection", key="test_lm_connection", use_container_width=True):
            with spinner("Testing connection..."):
                ai_service.base_url = base_url.rstrip('/')
                connected = ai_service.check_connection()
                if connected:
                    models = ai_service.get_available_models(force_refresh=True)
                    st.session_state.ai_connection_status = "connected"
                    st.session_state.ai_connection_message = f"Connected! Found {len(models)} model(s)"
                else:
                    st.session_state.ai_connection_status = "disconnected"
                    st.session_state.ai_connection_message = "Connection failed. Is LM Studio running?"

    # Display connection status using badge
    if "ai_connection_status" in st.session_state:
        if st.session_state.ai_connection_status == "connected":
            badge(st.session_state.ai_connection_message, variant=BadgeVariant.SUCCESS)
        elif st.session_state.ai_connection_status == "disconnected":
            badge(st.session_state.ai_connection_message, variant=BadgeVariant.CRITICAL)
        elif st.session_state.ai_connection_status == "checking":
            badge(st.session_state.ai_connection_message, variant=BadgeVariant.WARNING)

    # Save URL to session state (preserve existing value on blank input)
    if base_url and base_url != st.session_state.lm_studio_base_url:
        st.session_state.lm_studio_base_url = base_url
        db.set_setting("lm_studio_base_url", base_url, SETTINGS_KEYS["lm_studio_base_url"])
        announce_settings_change("LM Studio base URL updated")

    st.divider()

    # Section: AI Model Selection
    section_header(
        title="AI Model Selection",
        description="Select the model to use for diagnostic assistance. Refresh to discover available models.",
        icon="🧠"
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        # Get available models
        models = ai_service.get_available_models()
        model_options = [m.id for m in models]

        # Ensure current model is in options
        current_model = st.session_state.lm_studio_model
        if current_model not in model_options and current_model:
            model_options.insert(0, current_model)

        if not model_options:
            model_options = [current_model] if current_model else ["No models found"]
            st.caption("⚠️ No models discovered. Start LM Studio and load a model.")

        selected_model = selectbox(
            label="Model",
            key="lm_studio_model_select",
            options=model_options,
            index=model_options.index(current_model) if current_model in model_options else 0,
            help="Select the AI model for diagnostic assistance",
        )
    with col2:
        st.write("")
        st.write("")
        if button_secondary("🔄 Refresh Models", key="refresh_models", use_container_width=True):
            with spinner("Fetching models..."):
                ai_service.get_available_models(force_refresh=True)
                st.rerun()

    if selected_model != st.session_state.lm_studio_model:
        st.session_state.lm_studio_model = selected_model
        db.set_setting("lm_studio_model", selected_model, SETTINGS_KEYS["lm_studio_model"])
        announce_settings_change(f"AI model changed to {selected_model}")

    # Show model info as badges in responsive grid using design system
    if models:
        st.markdown("**Available Models:**")
        # Use auto-fit grid for responsive model badges
        st.markdown(f'<div style="{AUTO_FIT_CARD_CSS}">', unsafe_allow_html=True)
        for model in models:
            is_current = model.id == st.session_state.lm_studio_model
            variant = BadgeVariant.PRIMARY if is_current else BadgeVariant.NEUTRAL
            card_simple(
                content=f'<span style="display: flex; align-items: center; gap: {SPACE_2};">'
                        f'<span style="font-weight: 600;">{model.id}</span>'
                        f'{(" (current)" if is_current else "")}'
                        f'</span>',
                variant="elevated" if is_current else "default"
            )
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # Section: AI Parameters
    section_header(
        title="AI Parameters",
        description="Fine-tune the AI response behavior for diagnostic conversations.",
        icon="⚡"
    )

    col1, col2 = st.columns(2)

    with col1:
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=st.session_state.lm_studio_temperature,
            step=0.1,
            help="Controls randomness: 0 = deterministic, 2 = creative. Lower is better for diagnostics.",
            key="lm_studio_temperature_slider",
        )
        if temperature != st.session_state.lm_studio_temperature:
            st.session_state.lm_studio_temperature = temperature
            db.set_setting("lm_studio_temperature", str(temperature), SETTINGS_KEYS["lm_studio_temperature"])
            announce_settings_change(f"AI temperature set to {temperature}")

    with col2:
        timeout = st.number_input(
            "Request Timeout (seconds)",
            min_value=5,
            max_value=300,
            value=st.session_state.lm_studio_timeout,
            step=5,
            help="Maximum time to wait for AI response",
            key="lm_studio_timeout_input",
        )
        if timeout != st.session_state.lm_studio_timeout:
            st.session_state.lm_studio_timeout = timeout
            db.set_setting("lm_studio_timeout", str(timeout), SETTINGS_KEYS["lm_studio_timeout"])
            announce_settings_change(f"AI request timeout set to {timeout} seconds")

    # Temperature guide using alert component
    alert(
        title="Temperature Guide",
        message="""
**0.0 – 0.3**: Precise, deterministic responses (recommended for diagnostics)
**0.4 – 0.7**: Balanced creativity and accuracy
**0.8 – 1.0**: More creative, varied responses
**1.0 – 2.0**: Highly creative, less predictable
""",
        variant=AlertVariant.INFO,
    )


# =============================================================================
# Tab 2: OBD Connection Settings
# =============================================================================

def render_obd_settings(db):
    """Render OBD Connection settings."""
    # Section: OBD-II Connection Mode
    section_header(
        title="OBD-II Connection Mode",
        description="Choose between simulated data for testing or real OBD-II hardware connection.",
        icon="🔌"
    )

    obd_mode = st.radio(
        "Connection Mode",
        options=["simulation", "real"],
        index=0 if st.session_state.obd_mode == "simulation" else 1,
        format_func=lambda x: "🎮 Simulation Mode" if x == "simulation" else "🔌 Real OBD-II Hardware",
        horizontal=True,
        help="Simulation generates realistic demo data. Real mode requires an ELM327 adapter.",
        key="obd_mode_radio",
    )

    if obd_mode != st.session_state.obd_mode:
        st.session_state.obd_mode = obd_mode
        db.set_setting("obd_mode", obd_mode, SETTINGS_KEYS["obd_mode"])
        announce_settings_change(f"OBD mode changed to {'Simulation' if obd_mode == 'simulation' else 'Real Hardware'}")
        st.rerun()

    # Mode indicator badge
    if st.session_state.obd_mode == "simulation":
        badge("🎮 Simulation Mode Active — Using generated demo data", variant=BadgeVariant.WARNING)
    else:
        badge("🔌 Real OBD-II Hardware Mode — Requires ELM327 adapter", variant=BadgeVariant.INFO)

    st.divider()

    # Real OBD Settings (only shown in real mode)
    if st.session_state.obd_mode == "real":
        section_header(
            title="Hardware Configuration",
            description="Configure your ELM327 or compatible OBD-II adapter connection.",
            icon="🔧"
        )

        col1, col2 = st.columns(2)

        with col1:
            port = text_input(
                label="Serial Port",
                key="obd_port_input",
                value=st.session_state.obd_port,
                placeholder="COM3 (Windows) / /dev/ttyUSB0 (Linux)",
                help="Serial port for your OBD-II adapter",
            )
            if port != st.session_state.obd_port:
                st.session_state.obd_port = port
                db.set_setting("obd_port", port, SETTINGS_KEYS["obd_port"])
                announce_settings_change(f"OBD serial port changed to {port}")

        with col2:
            baudrate = selectbox(
                label="Baud Rate",
                key="obd_baudrate_select",
                options=[9600, 19200, 38400, 57600, 115200],
                index=[9600, 19200, 38400, 57600, 115200].index(st.session_state.obd_baudrate) if st.session_state.obd_baudrate in [9600, 19200, 38400, 57600, 115200] else 2,
                help="Communication speed for OBD-II adapter",
            )
            if baudrate != st.session_state.obd_baudrate:
                st.session_state.obd_baudrate = baudrate
                db.set_setting("obd_baudrate", str(baudrate), SETTINGS_KEYS["obd_baudrate"])
                announce_settings_change(f"OBD baud rate changed to {baudrate}")

        col1, col2 = st.columns(2)
        with col1:
            protocol = selectbox(
                label="Protocol",
                key="obd_protocol_select",
                options=["auto", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A"],
                index=["auto", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A"].index(st.session_state.obd_protocol) if st.session_state.obd_protocol in ["auto", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A"] else 0,
                help="OBD-II protocol (Auto detects automatically)",
            )
            if protocol != st.session_state.obd_protocol:
                st.session_state.obd_protocol = protocol
                db.set_setting("obd_protocol", protocol, SETTINGS_KEYS["obd_protocol"])
                announce_settings_change(f"OBD protocol changed to {protocol}")

        with col2:
            st.write("")
            st.write("")
            if button_secondary("🔍 Test OBD Connection", key="test_obd_connection", use_container_width=True):
                alert(
                    title="OBD Connection Test",
                    message="OBD connection test would be implemented with the OBD service. Use the OBD Connection page for actual hardware connection.",
                    variant=AlertVariant.INFO,
                )
    else:
        # Simulation mode info
        alert(
            title="Simulation Mode Active",
            message="""<strong>⚠️ Simulation Mode Active</strong><br>
All vehicle data is software-generated for demonstration purposes.
Values do not represent actual sensor readings from your vehicle.
Connect an ELM327 adapter and switch to <strong>Real OBD-II Hardware</strong> mode for live data.""",
            variant=AlertVariant.WARNING,
        )


# =============================================================================
# Tab 3: Simulation Settings
# =============================================================================

def render_simulation_settings(db):
    """Render Simulation settings."""
    # Section: Simulation Parameters
    section_header(
        title="Simulation Parameters",
        description="Configure the behavior of the vehicle simulation engine.",
        icon="🎮"
    )

    col1, col2 = st.columns(2)

    with col1:
        sim_interval = st.number_input(
            "Simulation Update Interval (seconds)",
            min_value=0.1,
            max_value=5.0,
            value=st.session_state.simulation_interval,
            step=0.1,
            format="%.1f",
            help="How often the simulation generates new data points",
            key="simulation_interval_input",
        )
        if sim_interval != st.session_state.simulation_interval:
            st.session_state.simulation_interval = sim_interval
            db.set_setting("simulation_interval", str(sim_interval), SETTINGS_KEYS["simulation_interval"])
            announce_settings_change(f"Simulation interval set to {sim_interval} seconds")

    with col2:
        telemetry_interval = st.number_input(
            "Telemetry Refresh Interval (seconds)",
            min_value=0.1,
            max_value=5.0,
            value=st.session_state.telemetry_refresh_interval,
            step=0.1,
            format="%.1f",
            help="How often the dashboard polls for new telemetry data",
            key="telemetry_refresh_interval_input",
        )
        if telemetry_interval != st.session_state.telemetry_refresh_interval:
            st.session_state.telemetry_refresh_interval = telemetry_interval
            db.set_setting("telemetry_refresh_interval", str(telemetry_interval), SETTINGS_KEYS["telemetry_refresh_interval"])
            announce_settings_change(f"Telemetry refresh interval set to {telemetry_interval} seconds")

    st.divider()

    # Section: Available Simulation Scenarios
    section_header(
        title="Available Simulation Scenarios",
        description="Predefined driving scenarios that simulate different vehicle operating conditions.",
        icon="📋"
    )

    for key, scenario in SIMULATION_SCENARIOS.items():
        with st.expander(f"{scenario['name']} — {scenario['description']}"):
            col1, col2 = st.columns(2)
            with col1:
                # Use card_simple for scenario info cards
                card_simple(
                    title="RPM Range",
                    content=f"{scenario['rpm_range'][0]} – {scenario['rpm_range'][1]} RPM",
                    elevated=False
                )
                card_simple(
                    title="Speed Range",
                    content=f"{scenario['speed_range'][0]} – {scenario['speed_range'][1]} km/h",
                    elevated=False
                )
                card_simple(
                    title="Coolant Temp",
                    content=f"{scenario['coolant_temp_range'][0]} – {scenario['coolant_temp_range'][1]} °C",
                    elevated=False
                )
            with col2:
                card_simple(
                    title="Throttle Range",
                    content=f"{scenario['throttle_range'][0]} – {scenario['throttle_range'][1]}%",
                    elevated=False
                )
                card_simple(
                    title="Engine Load",
                    content=f"{scenario['load_range'][0]} – {scenario['load_range'][1]}%",
                    elevated=False
                )

    st.divider()

    # Section: UI Preferences
    section_header(
        title="UI Preferences",
        description="Customize the dashboard appearance and behavior.",
        icon="🎨"
    )

    col1, col2 = st.columns(2)

    with col1:
        theme_mode = selectbox(
            label="Theme",
            key="theme_mode_select",
            options=["dark", "light", "auto"],
            index=["dark", "light", "auto"].index(st.session_state.theme_mode) if st.session_state.theme_mode in ["dark", "light", "auto"] else 0,
            help="UI color theme (dark mode recommended for automotive use; light/auto are placeholders)",
        )
        if theme_mode != st.session_state.theme_mode:
            st.session_state.theme_mode = theme_mode
            db.set_setting("theme_mode", theme_mode, SETTINGS_KEYS["theme_mode"])
            announce_settings_change(f"Theme changed to {theme_mode}")

    with col2:
        auto_refresh = st.checkbox(
            "Auto-refresh Dashboard",
            value=st.session_state.auto_refresh,
            help="Automatically update dashboard telemetry when simulation is running",
            key="auto_refresh_checkbox",
        )
        if auto_refresh != st.session_state.auto_refresh:
            st.session_state.auto_refresh = auto_refresh
            db.set_setting("auto_refresh", str(auto_refresh).lower(), SETTINGS_KEYS["auto_refresh"])
            announce_settings_change(f"Auto-refresh dashboard {'enabled' if auto_refresh else 'disabled'}")

    # Theme limitation notice
    if st.session_state.theme_mode != "dark":
        alert(
            title="Theme Limitation",
            message="Only <strong>dark</strong> theme is fully implemented. Light and auto modes are placeholders and may not render correctly.",
            variant=AlertVariant.WARNING,
        )


# =============================================================================
# Tab 4: Data & Export Settings
# =============================================================================

def render_data_export_settings(db):
    """Render Data Export settings."""
    # Section: Telemetry Sessions Export
    section_header(
        title="Telemetry Sessions",
        description="Export or delete recorded telemetry sessions.",
        icon="📊"
    )

    # Get recent sessions for export
    sessions = db.get_telemetry_sessions(limit=20)

    if sessions:
        for session in sessions[:10]:
            session_id = session['id']
            name = session.get('session_name', f'Session #{session_id}')
            scenario = session.get('scenario', 'unknown')
            start_time = session.get('start_time', 'Unknown')
            duration = session.get('duration_seconds', 0)

            with st.expander(f"{name} — {scenario} — {start_time[:19] if start_time else 'N/A'} ({duration:.0f}s)"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    if button_primary("📥 Export CSV", key=f"export_csv_{session_id}", use_container_width=True):
                        export_session_csv(db, session_id)
                with col2:
                    if button_secondary("📋 Export JSON", key=f"export_json_{session_id}", use_container_width=True):
                        export_session_json(db, session_id)
                with col3:
                    if button_danger("🗑️ Delete", key=f"delete_session_{session_id}", use_container_width=True):
                        if st.session_state.get(f"confirm_delete_{session_id}"):
                            delete_session(db, session_id)
                        else:
                            st.session_state[f"confirm_delete_{session_id}"] = True
                            alert(
                                title="Confirm Deletion",
                                message="Click again to confirm deletion of this session and all its records.",
                                variant=AlertVariant.WARNING,
                            )
                            st.rerun()
    else:
        empty_state(EmptyStateProps(
            title="No Telemetry Sessions",
            description="Start a simulation to record data.",
            icon="📊"
        ))

    st.divider()

    # Section: Diagnostic Reports Export
    section_header(
        title="Diagnostic Reports",
        description="Export diagnostic scan history and DTC codes.",
        icon="🔧"
    )

    reports = db.get_diagnostic_reports(limit=10)
    if reports:
        for report in reports:
            report_id = report['id']
            scan_time = report.get('scan_time', 'Unknown')
            dtc_count = report.get('dtc_count', 0)

            with st.expander(f"Scan #{report_id} — {scan_time[:19] if scan_time else 'N/A'} — {dtc_count} DTC(s)"):
                if button_secondary("📥 Export JSON", key=f"export_diag_{report_id}", use_container_width=True):
                    export_diagnostic_json(db, report_id)
    else:
        empty_state(EmptyStateProps(
            title="No Diagnostic Scans",
            description="Run a diagnostic scan to generate reports.",
            icon="🔧"
        ))

    st.divider()

    # Section: Maintenance Records Export
    section_header(
        title="Maintenance Records",
        description="Export service history and maintenance logs.",
        icon="🔩"
    )

    records = db.get_maintenance_records(limit=10)
    if records:
        if button_primary("📥 Export All Maintenance Records (CSV)", key="export_maintenance_csv", use_container_width=True):
            export_maintenance_csv(db)
    else:
        empty_state(EmptyStateProps(
            title="No Maintenance Records",
            description="Add maintenance records from the Maintenance page.",
            icon="🔩"
        ))

    st.divider()

    # Section: Complete Data Export
    section_header(
        title="Complete Data Export",
        description="Export all application data as a single JSON archive.",
        icon="📦"
    )

    if button_primary("📥 Export Complete Data Archive (JSON)", key="export_all_json", use_container_width=True):
        export_complete_data(db)


# =============================================================================
# Tab 5: Backup & Restore Settings
# =============================================================================

def render_backup_settings(db):
    """Render Backup & Restore settings."""
    # Section: Database Backup
    section_header(
        title="Database Backup",
        description="Create and manage backups of your i20 AI Garage database.",
        icon="💾"
    )

    col1, col2 = st.columns(2)

    with col1:
        if button_primary("💾 Create Backup", key="create_backup", use_container_width=True):
            create_database_backup(db)

    with col2:
        if button_secondary("📂 Open Backup Folder", key="open_backup_folder", use_container_width=True):
            open_backup_folder()

    st.divider()

    # Section: Backup History
    section_header(
        title="Backup History",
        description="Recent database backups stored locally.",
        icon="📋"
    )

    backup_dir = Path("data/backups")
    if backup_dir.exists():
        backups = sorted(backup_dir.glob("i20_garage_backup_*.db"), key=lambda x: x.stat().st_mtime, reverse=True)
        if backups:
            for backup in backups[:10]:
                stat = backup.stat()
                size_mb = stat.st_size / (1024 * 1024)
                mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

                # Use card_simple for each backup entry
                card_simple(
                    title=backup.name,
                    content=f"Size: {size_mb:.2f} MB &nbsp;|&nbsp; Created: {mtime}",
                    elevated=True,
                    footer=f"""
                    <div style="display: flex; gap: {GAP_INLINE};">
                        <span style="flex: 1;"></span>
                        <button style="background: {STATUS_CRITICAL}; color: {TEXT_ON_ACCENT}; border: none; padding: 4px 12px; border-radius: {RADIUS_PILL}; cursor: pointer;"
                            onclick="window.parent.postMessage({{'type': 'streamlit:setComponentValue', 'key': 'restore_{backup.name}', 'value': true}}, '*');">
                            🔄 Restore
                        </button>
                        <button style="background: {STATUS_NEUTRAL}; color: {TEXT_ON_ACCENT}; border: none; padding: 4px 12px; border-radius: {RADIUS_PILL}; cursor: pointer;"
                            onclick="window.parent.postMessage({{'type': 'streamlit:setComponentValue', 'key': 'delete_backup_{backup.name}', 'value': true}}, '*');">
                            🗑️ Delete
                        </button>
                    </div>
                    """,
                    class_name="i20-backup-card"
                )

                # Handle restore/delete via Streamlit buttons - use responsive grid
                st.markdown(f'<div style="{AUTO_FIT_METRIC_CSS}">', unsafe_allow_html=True)
                if button_danger("🔄 Restore", key=f"restore_{backup.name}", use_container_width=True):
                    restore_database_backup(db, backup)
                if button_ghost("🗑️ Delete", key=f"delete_backup_{backup.name}", use_container_width=True):
                    backup.unlink()
                    alert(
                        title="Backup Deleted",
                        message=f"Deleted {backup.name}",
                        variant=AlertVariant.SUCCESS,
                    )
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            empty_state(EmptyStateProps(
                title="No Backups Found",
                description="Click 'Create Backup' to make your first backup.",
                icon="💾"
            ))
    else:
        empty_state(EmptyStateProps(
            title="Backup Directory Not Found",
            description="It will be created on first backup.",
            icon="📁"
        ))

    st.divider()

    # Section: Database Statistics
    section_header(
        title="Database Statistics",
        description="Current database size and record counts.",
        icon="📊"
    )

    stats = db.get_database_stats()

    # Use metric cards via card_simple in a grid
    stat_items = [
        ("Database Size", f"{stats.get('db_size_bytes', 0) / 1024:.1f} KB"),
        ("Telemetry Sessions", str(stats.get('telemetry_sessions', 0))),
        ("Telemetry Records", str(stats.get('telemetry_records', 0))),
        ("Maintenance Records", str(stats.get('maintenance_records', 0))),
        ("Diagnostic Reports", str(stats.get('diagnostic_reports', 0))),
        ("AI Conversations", str(stats.get('ai_conversations', 0))),
        ("Settings Stored", str(stats.get('settings', 0))),
        ("Vehicle Profiles", str(stats.get('vehicle_profile', 0))),
    ]

    # Render as responsive grid using card_simple
    st.markdown(f'<div style="{AUTO_FIT_METRIC_CSS}">', unsafe_allow_html=True)
    for label, value in stat_items:
        card_simple(
            title=label,
            content=value,
            elevated=True
        )
    st.markdown('</div>', unsafe_allow_html=True)


# =============================================================================
# Tab 6: About Settings
# =============================================================================

def render_about_settings():
    """Render About / Application Information settings."""
    # Section: Application Information
    section_header(
        title="Application Information",
        description="Version, build details, and system information.",
        icon="ℹ️"
    )

    # App Info grid using card_simple
    st.markdown(f'<div style="{AUTO_FIT_CARD_CSS}">', unsafe_allow_html=True)
    card_simple(
        title="Application",
        content="i20 AI Garage",
        elevated=False
    )
    card_simple(
        title="Version",
        content="1.0.0",
        elevated=False
    )
    card_simple(
        title="Build Date",
        content="2026-11-15",
        elevated=False
    )
    card_simple(
        title="Python",
        content=__import__('sys').version.split()[0],
        elevated=False
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # Section: Vehicle Profile
    section_header(
        title="Vehicle Profile",
        description="Configured vehicle specification for diagnostic context.",
        icon="🚗"
    )

    st.markdown(f'<div style="{AUTO_FIT_CARD_CSS}">', unsafe_allow_html=True)
    card_simple(
        title="Vehicle",
        content=f"{VEHICLE_INFO['make']} {VEHICLE_INFO['model']} ({VEHICLE_INFO['year']})",
        elevated=False
    )
    card_simple(
        title="Engine",
        content=VEHICLE_INFO['engine'],
        elevated=False
    )
    card_simple(
        title="Transmission",
        content=VEHICLE_INFO['transmission'],
        elevated=False
    )
    card_simple(
        title="Fuel Type",
        content=f"{VEHICLE_INFO['fuel_type']} ({VEHICLE_INFO['market']})",
        elevated=False
    )
    card_simple(
        title="ECU Tuning",
        content=VEHICLE_INFO['ecu_tuning'],
        elevated=False
    )
    card_simple(
        title="VIN Pattern",
        content=VEHICLE_INFO.get('vin', 'N/A'),
        elevated=False
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # Section: Engine Specifications
    section_header(
        title="Engine Specifications",
        description="Technical specifications for the 1.2L Kappa II engine.",
        icon="⚙️"
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div style="{AUTO_FIT_CARD_CSS}">', unsafe_allow_html=True)
        card_simple(
            title="Displacement",
            content=f"{ENGINE_SPECS['displacement_cc']} cc",
            elevated=False
        )
        card_simple(
            title="Cylinders",
            content=str(ENGINE_SPECS['cylinders']),
            elevated=False
        )
        card_simple(
            title="Max Power",
            content=f"{ENGINE_SPECS['max_power_ps']} PS @ {ENGINE_SPECS['max_power_rpm']} RPM",
            elevated=False
        )
        card_simple(
            title="Max Torque",
            content=f"{ENGINE_SPECS['max_torque_nm']} Nm @ {ENGINE_SPECS['max_torque_rpm']} RPM",
            elevated=False
        )
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div style="{AUTO_FIT_CARD_CSS}">', unsafe_allow_html=True)
        card_simple(
            title="Compression Ratio",
            content=str(ENGINE_SPECS['compression_ratio']),
            elevated=False
        )
        card_simple(
            title="Fuel System",
            content=ENGINE_SPECS['fuel_system'],
            elevated=False
        )
        card_simple(
            title="Emission Standard",
            content=ENGINE_SPECS['emission_standard'],
            elevated=False
        )
        card_simple(
            title="Redline / Idle",
            content=f"{ENGINE_SPECS['redline_rpm']} / {ENGINE_SPECS['idle_rpm']} RPM",
            elevated=False
        )
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # Section: Important Disclaimers
    section_header(
        title="Important Disclaimers",
        icon="⚠️"
    )

    alert(
        title="For Demonstration & Educational Purposes Only",
        message="""This application simulates vehicle telemetry and provides AI-assisted diagnostic suggestions.
It is <strong>not a substitute for professional automotive diagnosis</strong>.<br><br>
<strong>Safety Notes:</strong>
<ul style="margin: 0.5rem 0 0 1.5rem;">
    <li>Never rely solely on simulated data for vehicle safety decisions</li>
    <li>Always verify diagnostic suggestions with proper tools and expertise</li>
    <li>Do not disable emissions or safety systems based on AI suggestions</li>
    <li>Consult a qualified technician for actual vehicle issues</li>
    <li>Real OBD-II data requires compatible hardware (ELM327 adapter)</li>
</ul>""",
        variant=AlertVariant.WARNING,
    )

    alert(
        title="Open Source Project",
        message="i20 AI Garage is an open-source automotive diagnostic assistant for the 2023 Hyundai i20 Asta. Built with Streamlit, Plotly, SQLite, and LM Studio for local AI inference.",
        variant=AlertVariant.SUCCESS,
    )


# =============================================================================
# Export Functions (Preserved exactly from original)
# =============================================================================

def export_session_csv(db, session_id: int):
    """Export a telemetry session to CSV."""
    from pathlib import Path
    import csv

    records = db.get_session_records(session_id)
    if not records:
        alert(
            title="Export Failed",
            message="No data to export",
            variant=AlertVariant.WARNING,
        )
        return

    export_dir = Path("data/exports")
    export_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = export_dir / f"session_{session_id}_{timestamp}.csv"

    fieldnames = [
        "timestamp", "rpm", "speed_kmh", "coolant_temp_c",
        "throttle_pos_pct", "engine_load_pct", "intake_pressure_kpa",
        "stft_b1_pct", "ltft_b1_pct", "voltage_v", "maf_g_s", "map_kpa", "is_simulated"
    ]

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow({k: record.get(k) for k in fieldnames})

    alert(
        title="Export Successful",
        message=f"Exported to {filepath}",
        variant=AlertVariant.SUCCESS,
    )


def export_session_json(db, session_id: int):
    """Export a telemetry session to JSON."""
    from pathlib import Path

    records = db.get_session_records(session_id)
    session = None
    sessions = db.get_telemetry_sessions(limit=100)
    for s in sessions:
        if s['id'] == session_id:
            session = s
            break

    if not records:
        alert(
            title="Export Failed",
            message="No data to export",
            variant=AlertVariant.WARNING,
        )
        return

    export_dir = Path("data/exports")
    export_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = export_dir / f"session_{session_id}_{timestamp}.json"

    data = {
        "session": session,
        "records": records,
        "exported_at": datetime.now().isoformat(),
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

    alert(
        title="Export Successful",
        message=f"Exported to {filepath}",
        variant=AlertVariant.SUCCESS,
    )


def export_diagnostic_json(db, report_id: int):
    """Export a diagnostic report to JSON."""
    from pathlib import Path

    reports = db.get_diagnostic_reports(limit=100)
    report = None
    for r in reports:
        if r['id'] == report_id:
            report = r
            break

    if not report:
        alert(
            title="Export Failed",
            message="Report not found",
            variant=AlertVariant.WARNING,
        )
        return

    export_dir = Path("data/exports")
    export_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = export_dir / f"diagnostic_{report_id}_{timestamp}.json"

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)

    alert(
        title="Export Successful",
        message=f"Exported to {filepath}",
        variant=AlertVariant.SUCCESS,
    )


def export_maintenance_csv(db):
    """Export all maintenance records to CSV."""
    from pathlib import Path
    import csv

    records = db.get_maintenance_records(limit=1000)
    if not records:
        alert(
            title="Export Failed",
            message="No maintenance records to export",
            variant=AlertVariant.WARNING,
        )
        return

    export_dir = Path("data/exports")
    export_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = export_dir / f"maintenance_{timestamp}.csv"

    fieldnames = [
        "id", "service_type", "description", "service_date", "odometer_km",
        "cost", "notes", "next_service_km", "next_service_date",
        "created_at", "updated_at"
    ]

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow({k: record.get(k) for k in fieldnames})

    alert(
        title="Export Successful",
        message=f"Exported to {filepath}",
        variant=AlertVariant.SUCCESS,
    )


def export_complete_data(db):
    """Export all application data as a JSON archive."""
    from pathlib import Path

    export_dir = Path("data/exports")
    export_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = export_dir / f"i20_garage_complete_{timestamp}.json"

    # Gather all data
    data = {
        "exported_at": datetime.now().isoformat(),
        "version": "1.0.0",
        "vehicle_profile": db.get_vehicle_profile(),
        "telemetry_sessions": db.get_telemetry_sessions(limit=1000),
        "diagnostic_reports": db.get_diagnostic_reports(limit=1000),
        "maintenance_records": db.get_maintenance_records(limit=1000),
        "database_stats": db.get_database_stats(),
    }

    # Add records for each session
    for session in data["telemetry_sessions"]:
        session_id = session['id']
        data[f"session_{session_id}_records"] = db.get_session_records(session_id)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

    alert(
        title="Export Successful",
        message=f"Complete data archive exported to {filepath}",
        variant=AlertVariant.SUCCESS,
    )


def create_database_backup(db):
    """Create a database backup."""
    from pathlib import Path

    backup_dir = Path("data/backups")
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"i20_garage_backup_{timestamp}.db"

    with spinner("Creating backup..."):
        if db.backup_database(backup_path):
            alert(
                title="Backup Created",
                message=f"Backup created: {backup_path.name}",
                variant=AlertVariant.SUCCESS,
            )
        else:
            alert(
                title="Backup Failed",
                message="Failed to create backup",
                variant=AlertVariant.CRITICAL,
            )


def restore_database_backup(db, backup_path: Path):
    """Restore database from backup."""
    import shutil

    # Confirm restore (two-click pattern preserved)
    if st.session_state.get("confirm_restore"):
        try:
            shutil.copy2(backup_path, db.db_path)
            alert(
                title="Restore Successful",
                message=f"Database restored from {backup_path.name}",
                variant=AlertVariant.SUCCESS,
            )
            alert(
                title="Refresh Required",
                message="Please refresh the page to see changes",
                variant=AlertVariant.INFO,
            )
            st.session_state.confirm_restore = False
        except Exception as e:
            alert(
                title="Restore Failed",
                message=f"Restore failed: {e}",
                variant=AlertVariant.CRITICAL,
            )
    else:
        st.session_state.confirm_restore = True
        alert(
            title="Confirm Restore",
            message="This will overwrite the current database. Click again to confirm.",
            variant=AlertVariant.WARNING,
        )
        st.rerun()


def open_backup_folder():
    """Open the backup folder in file explorer."""
    import subprocess
    from pathlib import Path

    backup_dir = Path("data/backups").absolute()
    backup_dir.mkdir(parents=True, exist_ok=True)

    try:
        if os.name == 'nt':  # Windows
            subprocess.run(['explorer', str(backup_dir)], check=True)
        else:  # Linux/Mac
            subprocess.run(['xdg-open', str(backup_dir)], check=True)
        alert(
            title="Folder Opened",
            message="Opened backup folder",
            variant=AlertVariant.SUCCESS,
        )
    except Exception as e:
        alert(
            title="Error",
            message=f"Could not open folder: {e}",
            variant=AlertVariant.CRITICAL,
        )
        alert(
            title="Backup Location",
            message=f"Backup folder: {backup_dir}",
            variant=AlertVariant.INFO,
        )


def delete_session(db, session_id: int):
    """Delete a telemetry session and its records."""
    with db._get_connection() as conn:
        cursor = conn.cursor()
        # Delete records first (cascade should handle this, but explicit is safer)
        cursor.execute("DELETE FROM telemetry_records WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM telemetry_sessions WHERE id = ?", (session_id,))
        conn.commit()
    alert(
        title="Session Deleted",
        message=f"Session #{session_id} deleted",
        variant=AlertVariant.SUCCESS,
    )
    st.rerun()
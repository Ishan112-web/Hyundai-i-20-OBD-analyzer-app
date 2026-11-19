"""
i20 AI Garage - Vehicle Profile Module (Redesigned with Phase 6 Design System)

Vehicle profile display and editing with engine specifications,
connection statuses, and diagnostic information.

FULLY RESPONSIVE: mobile-first fluid grid, auto-fit cards, responsive forms.
"""

import streamlit as st
from typing import Dict, Any, Optional
from datetime import datetime

from config import (
    THEME, VEHICLE_INFO, ENGINE_SPECS, OBD_MODE, DEMO_DTCS
)
from services import get_database, get_ai_service, get_obd_service
from services.database import DatabaseService
from services.ai_service import AIService
from services.obd_service import OBDService

from components.ui import (
    # Styles & Layout
    inject_global_css,
    initialize_layout,
    page_header,
    responsive_container,
    section_header,
    card_container,
    grid_container,
    AUTO_FIT_CARD_CSS,
    AUTO_FIT_METRIC_CSS,
    status_indicator,
    # Components
    ButtonVariant,
    ButtonSize,
    ButtonProps,
    button,
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
    form_field,
    text_input,
    selectbox,
    TableColumn,
    TableProps,
    table,
    EmptyStateProps,
    empty_state,
    skeleton,
    skeleton_text,
    skeleton_card,
    spinner,
    loading_overlay,
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
    BORDER_DEFAULT,
    BORDER_SUBTLE,
    DIAG_CRITICAL,
    DIAG_MAJOR,
    DIAG_MINOR,
    DIAG_INFO,
    DATASOURCE_SIMULATION,
    DATASOURCE_REAL,
    SPACE_1,
    SPACE_2,
    SPACE_3,
    SPACE_4,
    SPACE_5,
    SPACE_6,
    GAP_FIELD,
    GAP_CARD_GRID,
    RADIUS_MD,
    RADIUS_LG,
    RADIUS_PILL,
    FONT_SIZE_LABEL,
    FONT_SIZE_BODY,
    FONT_SIZE_BODY_SM,
    FONT_SIZE_CAPTION,
    BUTTON_FONT_WEIGHT,
    TRANSITION_FAST,
    TRANSITION_NORMAL,
    CARD_RADIUS,
    CARD_PADDING,
    CARD_BORDER,
    INPUT_HEIGHT,
    INPUT_PADDING_VERTICAL,
    INPUT_PADDING_HORIZONTAL,
    INPUT_RADIUS,
    INPUT_FONT_SIZE,
    GAP_SECTION,
    GAP_CARD,
)


def render_vehicle_profile():
    """Render the complete vehicle profile page using design system - FULLY RESPONSIVE."""
    # Initialize services
    db = get_database()
    ai_service = get_ai_service()
    obd_service = get_obd_service()

    # Load vehicle profile from database (with config fallback)
    vehicle_profile = _load_vehicle_profile(db)

    # Inject global CSS (design system)
    inject_global_css()
    initialize_layout()

    # Page header using design system layout
    page_header(
        title=f"{vehicle_profile.get('make', 'Hyundai')} {vehicle_profile.get('model', 'i20 Asta')} ({vehicle_profile.get('year', 2023)})",
        subtitle=f"{vehicle_profile.get('engine', '1.2L Naturally Aspirated Petrol')} · {vehicle_profile.get('transmission', 'Manual')} · {vehicle_profile.get('fuel_type', 'Petrol')}",
        icon="🚗"
    )

    # Mode badge using design system badge component
    mode = vehicle_profile.get("diagnostic_mode", OBD_MODE).upper()
    badge_variant = BadgeVariant.WARNING if mode == "SIMULATION" else BadgeVariant.SUCCESS
    badge(
        label=f"{mode} MODE",
        variant=badge_variant,
        key="vehicle_mode_badge"
    )

    st.markdown(f"<div style='margin-bottom: {GAP_SECTION};'></div>", unsafe_allow_html=True)

    # Main content tabs using Streamlit native tabs (styled via global CSS)
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Vehicle Info",
        "⚙️ Engine Specs",
        "🔌 Connections",
        "🩺 Diagnostics"
    ])

    with tab1:
        _render_vehicle_info_tab(vehicle_profile, db)

    with tab2:
        _render_engine_specs_tab()

    with tab3:
        _render_connections_tab(ai_service, obd_service)

    with tab4:
        _render_diagnostics_tab(obd_service)


def _load_vehicle_profile(db: DatabaseService) -> Dict[str, Any]:
    """Load vehicle profile from database, fallback to config."""
    profile = db.get_vehicle_profile()
    if profile:
        return profile
    # Return config defaults if no profile in database
    return {
        "make": VEHICLE_INFO["make"],
        "model": VEHICLE_INFO["model"],
        "year": VEHICLE_INFO["year"],
        "engine": VEHICLE_INFO["engine"],
        "transmission": VEHICLE_INFO["transmission"],
        "fuel_type": VEHICLE_INFO["fuel_type"],
        "market": VEHICLE_INFO["market"],
        "ecu_tuning": VEHICLE_INFO["ecu_tuning"],
        "diagnostic_mode": VEHICLE_INFO["diagnostic_mode"],
        "vin": VEHICLE_INFO.get("vin", ""),
    }


def _render_vehicle_info_tab(vehicle_profile: Dict[str, Any], db: DatabaseService):
    """Render the Vehicle Info tab with editable fields using design system components - RESPONSIVE."""
    # Vehicle Information Section
    section_header(
        title="Vehicle Information",
        description="Core vehicle identity and configuration"
    )

    # Display current info in a responsive grid using design system AUTO_FIT_CARD_CSS
    info_items = [
        ("Make", vehicle_profile.get("make", "—"), "🏷️"),
        ("Model", vehicle_profile.get("model", "—"), "🚗"),
        ("Year", str(vehicle_profile.get("year", "—")), "📅"),
        ("Engine", vehicle_profile.get("engine", "—"), "🔧"),
        ("Transmission", vehicle_profile.get("transmission", "—"), "⚙️"),
        ("Fuel Type", vehicle_profile.get("fuel_type", "—"), "⛽"),
        ("Market", vehicle_profile.get("market", "—"), "🌍"),
        ("ECU Tuning", vehicle_profile.get("ecu_tuning", "—"), "🎛️"),
        ("Diagnostic Mode", vehicle_profile.get("diagnostic_mode", "—"), "🔌"),
        ("VIN", vehicle_profile.get("vin", "—") or "Not specified", "🔢"),
    ]

    # Build grid of info cards using design system AUTO_FIT_CARD_CSS - RESPONSIVE
    st.markdown(AUTO_FIT_CARD_CSS, unsafe_allow_html=True)
    grid_items = []
    for label, value, icon in info_items:
        card_html = card_simple(
            title=f"{icon} {label}",
            content=value,
            footer="",
            elevated=False,
            bordered=True,
            padding="md",
        )
        grid_items.append(f'<div class="i20-grid-item">{card_html}</div>')

    st.markdown(f"""
    <div class="i20-grid-auto-fit">
        {''.join(grid_items)}
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"<div style='margin-bottom: {GAP_SECTION};'></div>", unsafe_allow_html=True)

    # Edit form using design system form components - RESPONSIVE
    with st.expander("✏️ Edit Vehicle Profile", expanded=False):
        _render_edit_form(vehicle_profile, db)


def _render_edit_form(vehicle_profile: Dict[str, Any], db: DatabaseService):
    """Render the vehicle profile edit form using design system form components - RESPONSIVE."""
    with st.form("vehicle_profile_form"):
        # Row 1: Make, Model, Year - RESPONSIVE (columns stack on mobile)
        col1, col2, col3 = st.columns(3, gap="medium")
        with col1:
            make = text_input(
                label="Make",
                value=vehicle_profile.get("make", ""),
                placeholder="e.g., Hyundai",
                key="edit_make",
                required=True,
            )
        with col2:
            model = text_input(
                label="Model",
                value=vehicle_profile.get("model", ""),
                placeholder="e.g., i20 Asta",
                key="edit_model",
                required=True,
            )
        with col3:
            year = text_input(
                label="Year",
                value=str(vehicle_profile.get("year", 2023)),
                placeholder="2023",
                key="edit_year",
                required=True,
                type="number",
            )

        # Row 2: Engine, Transmission, Fuel Type
        col1, col2, col3 = st.columns(3, gap="medium")
        with col1:
            engine = text_input(
                label="Engine",
                value=vehicle_profile.get("engine", ""),
                placeholder="e.g., 1.2L Naturally Aspirated Petrol",
                key="edit_engine",
                required=True,
            )
        with col2:
            transmission = selectbox(
                label="Transmission",
                options=["Manual", "Automatic", "CVT", "DCT", "AMT"],
                index=["Manual", "Automatic", "CVT", "DCT", "AMT"].index(
                    vehicle_profile.get("transmission", "Manual")
                ),
                key="edit_transmission",
                required=True,
            )
        with col3:
            fuel_type = selectbox(
                label="Fuel Type",
                options=["Petrol", "Diesel", "CNG", "LPG", "Hybrid", "Electric"],
                index=["Petrol", "Diesel", "CNG", "LPG", "Hybrid", "Electric"].index(
                    vehicle_profile.get("fuel_type", "Petrol")
                ),
                key="edit_fuel_type",
                required=True,
            )

        # Row 3: Market, ECU Tuning, Diagnostic Mode
        col1, col2, col3 = st.columns(3, gap="medium")
        with col1:
            market = text_input(
                label="Market",
                value=vehicle_profile.get("market", ""),
                placeholder="e.g., India",
                key="edit_market",
                required=True,
            )
        with col2:
            ecu_tuning = selectbox(
                label="ECU Tuning",
                options=["Stock", "Stage 1", "Stage 2", "Stage 3", "Custom"],
                index=["Stock", "Stage 1", "Stage 2", "Stage 3", "Custom"].index(
                    vehicle_profile.get("ecu_tuning", "Stock")
                ),
                key="edit_ecu_tuning",
                required=True,
            )
        with col3:
            diagnostic_mode = selectbox(
                label="Diagnostic Mode",
                options=["Simulation", "Real"],
                index=["Simulation", "Real"].index(
                    vehicle_profile.get("diagnostic_mode", "Simulation")
                ),
                key="edit_diagnostic_mode",
                required=True,
            )

        # Row 4: VIN
        vin = text_input(
            label="VIN (optional)",
            value=vehicle_profile.get("vin", ""),
            placeholder="e.g., MALA841CLHM123456",
            key="edit_vin",
            help_text="17-character Vehicle Identification Number",
        )

        # Form actions - RESPONSIVE (full width buttons stack on mobile)
        st.markdown(f"<div style='margin-top: {SPACE_4}; display: flex; gap: {SPACE_3}; flex-wrap: wrap;'></div>", unsafe_allow_html=True)
        col_save, col_cancel = st.columns(2, gap="small")
        with col_save:
            submitted = button_primary(
                "💾 Save Changes",
                key="save_vehicle_profile",
                use_container_width=True,
                size=ButtonSize.MD,
            )
        with col_cancel:
            cancelled = button_secondary(
                "✖ Cancel",
                key="cancel_vehicle_profile",
                use_container_width=True,
                size=ButtonSize.MD,
            )

        if submitted:
            updates = {
                "make": make,
                "model": model,
                "year": int(year) if year.isdigit() else 2023,
                "engine": engine,
                "transmission": transmission,
                "fuel_type": fuel_type,
                "market": market,
                "ecu_tuning": ecu_tuning,
                "diagnostic_mode": diagnostic_mode,
                "vin": vin.upper() if vin else None,
            }
            if db.update_vehicle_profile(**updates):
                alert(
                    title="Success",
                    message="Vehicle profile updated successfully!",
                    variant=AlertVariant.SUCCESS,
                    key="profile_save_success"
                )
                st.rerun()
            else:
                alert(
                    title="Error",
                    message="Failed to update vehicle profile.",
                    variant=AlertVariant.CRITICAL,
                    key="profile_save_error"
                )

        if cancelled:
            st.rerun()


def _render_engine_specs_tab():
    """Render the Engine Specifications tab using design system components - RESPONSIVE."""
    # Engine Specifications Section
    section_header(
        title="Engine Specifications",
        description="Factory specifications for the 1.2L Kappa II engine"
    )

    specs = [
        ("🔧", "Displacement", f"{ENGINE_SPECS['displacement_cc']} cc", f"{ENGINE_SPECS['displacement_cc']/1000:.1f}L"),
        ("⚡", "Cylinders", f"{ENGINE_SPECS['cylinders']} Cylinder", "Inline-4"),
        ("🏁", "Max Power", f"{ENGINE_SPECS['max_power_ps']} PS @ {ENGINE_SPECS['max_power_rpm']:,} RPM", f"~{ENGINE_SPECS['max_power_ps']*0.735:.0f} kW"),
        ("🔩", "Max Torque", f"{ENGINE_SPECS['max_torque_nm']} Nm @ {ENGINE_SPECS['max_torque_rpm']:,} RPM", f"~{ENGINE_SPECS['max_torque_nm']*0.738:.0f} lb-ft"),
        ("📊", "Compression Ratio", ENGINE_SPECS['compression_ratio'], ""),
        ("⛽", "Fuel System", ENGINE_SPECS['fuel_system'], ""),
        ("🌱", "Emission Standard", ENGINE_SPECS['emission_standard'], "Bharat Stage 6"),
        ("📈", "Redline", f"{ENGINE_SPECS['redline_rpm']:,} RPM", "Fuel cut-off"),
        ("💤", "Idle RPM", f"{ENGINE_SPECS['idle_rpm']:,} RPM", "Operating temperature"),
    ]

    # Build spec cards using design system AUTO_FIT_METRIC_CSS - RESPONSIVE
    st.markdown(AUTO_FIT_METRIC_CSS, unsafe_allow_html=True)
    grid_items = []
    for icon, label, value, detail in specs:
        content = f"""
        <div style="font-size: 2.5rem; margin-bottom: {SPACE_3}; display: block;">{icon}</div>
        <div style="
            font-size: 1.75rem;
            font-weight: 700;
            color: {TEXT_PRIMARY};
            font-variant-numeric: tabular-nums;
            margin-bottom: {SPACE_1};
        ">{value}</div>
        <div style="
            font-size: {FONT_SIZE_CAPTION};
            font-weight: {BUTTON_FONT_WEIGHT};
            color: {TEXT_SECONDARY};
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: {SPACE_2};
        ">{label}</div>
        {f'<div style="font-size: {FONT_SIZE_CAPTION}; color: {TEXT_SECONDARY}; margin-top: {SPACE_2}; text-transform: uppercase; letter-spacing: 0.05em;">{detail}</div>' if detail else ''}
        """
        card_html = card_simple(
            title="",
            content=content,
            footer="",
            elevated=False,
            bordered=True,
            padding="lg",
            align="center",
        )
        grid_items.append(f'<div class="i20-grid-item">{card_html}</div>')

    st.markdown(f"""
    <div class="i20-grid-auto-fit-metric">
        {''.join(grid_items)}
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"<div style='margin-bottom: {GAP_SECTION};'></div>", unsafe_allow_html=True)

    # Derived Specifications Section
    section_header(
        title="Derived Specifications",
        description="Calculated performance metrics"
    )

    displacement_l = ENGINE_SPECS['displacement_cc'] / 1000
    power_per_liter = ENGINE_SPECS['max_power_ps'] / displacement_l
    torque_per_liter = ENGINE_SPECS['max_torque_nm'] / displacement_l
    bore_stroke_note = "Estimated bore × stroke: ~71.5mm × 74.5mm (square-ish)"

    derived = [
        ("Power per Liter", f"{power_per_liter:.1f} PS/L", "Specific output"),
        ("Torque per Liter", f"{torque_per_liter:.1f} Nm/L", "Specific torque"),
        ("Power-to-Weight (est.)", "~105 PS/tonne", "Assuming ~950 kg kerb weight"),
        ("Bore × Stroke", bore_stroke_note, "Typical for 1.2L 4-cyl"),
    ]

    derived_cards = []
    for label, value, detail in derived:
        card_html = card_simple(
            title=label,
            content=f'{value}<div style="font-size: {FONT_SIZE_CAPTION}; color: {TEXT_MUTED}; margin-top: {SPACE_1};">{detail}</div>',
            footer="",
            elevated=False,
            bordered=True,
            padding="md",
        )
        derived_cards.append(f'<div class="i20-grid-item">{card_html}</div>')

    st.markdown(f"""
    <style>{AUTO_FIT_CARD_CSS}</style>
    <div class="i20-grid-auto-fit">
        {''.join(derived_cards)}
    </div>
    """, unsafe_allow_html=True)


def _render_connections_tab(ai_service: AIService, obd_service: OBDService):
    """Render the Connections tab with OBD and AI status using design system components - RESPONSIVE."""
    obd_status = obd_service.get_status()
    ai_status = ai_service.get_system_status()

    # OBD-II Connection Section
    section_header(
        title="OBD-II Connection",
        description="Vehicle interface adapter status and configuration"
    )

    obd_mode = obd_status["mode"]
    obd_conn_state = obd_status["connection_state"]
    obd_sim_running = obd_status["simulation_running"]
    obd_scenario = obd_status["current_scenario"]

    # Determine OBD status
    if obd_conn_state == "connected" and obd_mode == "simulation":
        obd_status_class = "simulation"
        obd_status_text = "Simulation Connected"
        obd_badge_variant = BadgeVariant.WARNING
        obd_badge_label = "SIMULATION"
    elif obd_conn_state == "connected":
        obd_status_class = "connected"
        obd_status_text = "Connected"
        obd_badge_variant = BadgeVariant.SUCCESS
        obd_badge_label = "CONNECTED"
    elif obd_conn_state == "error":
        obd_status_class = "error"
        obd_status_text = "Connection Error"
        obd_badge_variant = BadgeVariant.CRITICAL
        obd_badge_label = "ERROR"
    else:
        obd_status_class = "disconnected"
        obd_status_text = "Disconnected"
        obd_badge_variant = BadgeVariant.NEUTRAL
        obd_badge_label = "DISCONNECTED"

    # OBD Status Card using design system components
    obd_status_color = STATUS_SUCCESS if obd_status_class == "connected" else DATASOURCE_SIMULATION if obd_status_class == "simulation" else STATUS_CRITICAL if obd_status_class == "error" else STATUS_NEUTRAL
    card(CardProps(
        title="OBD-II Adapter",
        subtitle=f"Mode: {obd_mode.upper()} · State: {obd_status_text}",
        content=f"""
        <div style="display: flex; align-items: center; gap: {SPACE_3}; margin-bottom: {SPACE_4};">
            <span style="width: 12px; height: 12px; border-radius: 50%; background: {obd_status_color};"></span>
            <span style="font-size: {FONT_SIZE_BODY}; color: {TEXT_PRIMARY}; font-weight: 500;">{obd_status_text}</span>
        </div>
        <div style="
            font-size: {FONT_SIZE_BODY_SM};
            color: {TEXT_SECONDARY};
            font-family: monospace;
            padding: {SPACE_3};
            background: {SURFACE_SECONDARY};
            border-radius: {RADIUS_SM};
            border: 1px solid {BORDER_SUBTLE};
        ">
            Port: {obd_status['port']} · Baudrate: {obd_status['baudrate']} · Protocol: {obd_status['protocol']}
        </div>
        """,
        elevated=(obd_status_class in ["connected", "simulation"]),
        bordered=True,
    ))

    st.markdown(f"<div style='margin-bottom: {GAP_FIELD};'></div>", unsafe_allow_html=True)

    # OBD Details Grid - RESPONSIVE using AUTO_FIT_CARD_CSS instead of fixed columns
    st.markdown(AUTO_FIT_CARD_CSS, unsafe_allow_html=True)
    st.markdown('<div class="i20-grid-auto-fit">', unsafe_allow_html=True)

    details_content = ""
    details = [
        ("Mode", obd_mode.upper()),
        ("State", obd_conn_state.title()),
        ("Port", obd_status['port']),
        ("Baudrate", str(obd_status['baudrate'])),
        ("Protocol", obd_status['protocol']),
    ]
    for label, value in details:
        details_content += f"""
        <div style="display: flex; justify-content: space-between; padding: {SPACE_2} 0; border-bottom: 1px solid {BORDER_SUBTLE};">
            <span style="color: {TEXT_SECONDARY}; font-size: {FONT_SIZE_BODY_SM};">{label}</span>
            <span style="font-weight: 500; color: {TEXT_PRIMARY}; font-size: {FONT_SIZE_BODY_SM};">{value}</span>
        </div>
        """
    card_html = card_simple(
        title="Connection Details",
        content=details_content,
        footer="",
        elevated=False,
        bordered=True,
    )
    st.markdown(f'<div class="i20-grid-item">{card_html}</div>', unsafe_allow_html=True)

    sim_status_text = "Running" if obd_sim_running else "Stopped"
    sim_details = [
        ("Status", sim_status_text),
        ("Scenario", obd_scenario.title()),
        ("Supported PIDs", str(obd_status['supported_pids_count'])),
        ("Last Update", obd_status['last_update'][:19] if obd_status['last_update'] else 'Never'),
    ]
    sim_content = ""
    for label, value in sim_details:
        sim_content += f"""
        <div style="display: flex; justify-content: space-between; padding: {SPACE_2} 0; border-bottom: 1px solid {BORDER_SUBTLE};">
            <span style="color: {TEXT_SECONDARY}; font-size: {FONT_SIZE_BODY_SM};">{label}</span>
            <span style="font-weight: 500; color: {TEXT_PRIMARY}; font-size: {FONT_SIZE_BODY_SM};">{value}</span>
        </div>
        """
    card_html = card_simple(
        title="Simulation Status",
        content=sim_content,
        footer="",
        elevated=False,
        bordered=True,
    )
    st.markdown(f'<div class="i20-grid-item">{card_html}</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"<div style='margin-bottom: {GAP_SECTION};'></div>", unsafe_allow_html=True)

    # AI Assistant Section
    section_header(
        title="AI Assistant (LM Studio)",
        description="Local AI server connection and model status"
    )

    ai_connected = ai_status["connected"]
    ai_model_available = ai_status["model_available"]
    ai_model = ai_status["configured_model"]
    ai_models = ai_status["available_models"]
    ai_url = ai_status["base_url"]

    if ai_connected and ai_model_available:
        ai_status_class = "connected"
        ai_status_text = "Connected & Model Ready"
        ai_badge_variant = BadgeVariant.SUCCESS
        ai_badge_label = "READY"
    elif ai_connected:
        ai_status_class = "warning"
        ai_status_text = "Connected - Model Not Loaded"
        ai_badge_variant = BadgeVariant.WARNING
        ai_badge_label = "NO MODEL"
    else:
        ai_status_class = "error"
        ai_status_text = "Disconnected"
        ai_badge_variant = BadgeVariant.CRITICAL
        ai_badge_label = "OFFLINE"

    ai_status_color = STATUS_SUCCESS if ai_status_class == "connected" else STATUS_WARNING if ai_status_class == "warning" else STATUS_CRITICAL
    card(CardProps(
        title="LM Studio Server",
        subtitle=ai_status_text,
        content=f"""
        <div style="display: flex; align-items: center; gap: {SPACE_3}; margin-bottom: {SPACE_4};">
            <span style="width: 12px; height: 12px; border-radius: 50%; background: {ai_status_color};"></span>
            <span style="font-size: {FONT_SIZE_BODY}; color: {TEXT_PRIMARY}; font-weight: 500;">{ai_status_text}</span>
        </div>
        <div style="
            font-size: {FONT_SIZE_BODY_SM};
            color: {TEXT_SECONDARY};
            font-family: monospace;
            padding: {SPACE_3};
            background: {SURFACE_SECONDARY};
            border-radius: {RADIUS_SM};
            border: 1px solid {BORDER_SUBTLE};
        ">
            {ai_url}
        </div>
        """,
        elevated=(ai_status_class == "connected"),
        bordered=True,
    ))

    st.markdown(f"<div style='margin-bottom: {GAP_FIELD};'></div>", unsafe_allow_html=True)

    # AI Details Grid - RESPONSIVE using AUTO_FIT_CARD_CSS
    st.markdown(AUTO_FIT_CARD_CSS, unsafe_allow_html=True)
    st.markdown('<div class="i20-grid-auto-fit">', unsafe_allow_html=True)

    ai_details = [
        ("Base URL", ai_url),
        ("Configured Model", ai_model),
        ("Temperature", str(ai_status['temperature'])),
        ("Timeout", f"{ai_status['timeout']}s"),
    ]
    ai_content = ""
    for label, value in ai_details:
        ai_content += f"""
        <div style="display: flex; justify-content: space-between; padding: {SPACE_2} 0; border-bottom: 1px solid {BORDER_SUBTLE};">
            <span style="color: {TEXT_SECONDARY}; font-size: {FONT_SIZE_BODY_SM};">{label}</span>
            <span style="font-weight: 500; color: {TEXT_PRIMARY}; font-size: {FONT_SIZE_BODY_SM}; font-family: monospace;">{value}</span>
        </div>
        """
    card_html = card_simple(
        title="Server Configuration",
        content=ai_content,
        footer="",
        elevated=False,
        bordered=True,
    )
    st.markdown(f'<div class="i20-grid-item">{card_html}</div>', unsafe_allow_html=True)

    models_content = f"""
    <div style="font-size: {FONT_SIZE_BODY_SM}; color: {TEXT_SECONDARY};">
        {', '.join(ai_models) if ai_models else 'No models loaded'}
    </div>
    <div style="margin-top: {SPACE_2}; font-size: {FONT_SIZE_CAPTION}; color: {TEXT_MUTED};">
        {len(ai_models)} model(s) available
    </div>
    """
    card_html = card_simple(
        title="Available Models",
        content=models_content,
        footer="",
        elevated=False,
        bordered=True,
    )
    st.markdown(f'<div class="i20-grid-item">{card_html}</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"<div style='margin-bottom: {GAP_SECTION};'></div>", unsafe_allow_html=True)

    # Action buttons - RESPONSIVE (flex-wrap handles mobile)
    col1, col2, col3 = st.columns(3, gap="small")
    with col1:
        if button_secondary("🔄 Refresh AI Status", key="refresh_ai", use_container_width=True):
            st.rerun()
    with col2:
        if button_secondary("🔄 Refresh OBD Status", key="refresh_obd", use_container_width=True):
            st.rerun()
    with col3:
        if obd_mode == "simulation" and not obd_sim_running:
            if button_primary("▶ Start Simulation", key="start_sim", use_container_width=True):
                if obd_service.start_simulation(obd_scenario):
                    alert("Success", "Simulation started", AlertVariant.SUCCESS, key="sim_started")
                    st.rerun()
                else:
                    alert("Error", "Failed to start simulation", AlertVariant.CRITICAL, key="sim_failed")


def _render_diagnostics_tab(obd_service: OBDService):
    """Render the Diagnostics tab with DTC information using design system components - RESPONSIVE."""
    # DTCs Section
    section_header(
        title="Diagnostic Trouble Codes (DTCs)",
        description="Current fault codes from vehicle ECU"
    )

    dtcs = obd_service.scan_dtcs()

    if dtcs:
        # Show demo warning if applicable
        demo_dtcs = [d for d in dtcs if getattr(d, 'is_demo', False)]
        if demo_dtcs:
            alert(
                title="Demo Mode",
                message=f"{len(demo_dtcs)} DTC(s) are from demo data — not from a real vehicle connection",
                variant=AlertVariant.WARNING,
                key="demo_dtc_warning"
            )

        for dtc in dtcs:
            # Map severity to badge variant
            severity_badge_map = {
                "critical": BadgeVariant.CRITICAL,
                "major": BadgeVariant.WARNING,
                "minor": BadgeVariant.INFO,
                "info": BadgeVariant.NEUTRAL,
            }
            severity_variant = severity_badge_map.get(dtc.severity, BadgeVariant.NEUTRAL)

            # Build diagnostic card using design system badge component
            severity_badge_html = badge(
                label=dtc.severity.upper(),
                variant=severity_variant,
                key=f"dtc_severity_{dtc.code}",
            )
            demo_badge_html = ""
            if getattr(dtc, 'is_demo', False):
                demo_badge_html = badge(
                    label="DEMO CODE",
                    variant=BadgeVariant.WARNING,
                    key=f"dtc_demo_{dtc.code}",
                )

            card(CardProps(
                title=f"{dtc.code} — {dtc.description}",
                subtitle=f"Status: {dtc.status.title()}",
                content=f"""
                <div style="display: flex; flex-wrap: wrap; gap: {SPACE_2}; margin-bottom: {SPACE_3};">
                    {severity_badge_html}
                    {demo_badge_html}
                </div>
                """,
                footer="",
                elevated=False,
                bordered=True,
                class_name="i20-dtc-card",
            ))
    else:
        # Empty state using design system
        empty_state(EmptyStateProps(
            title="No Diagnostic Trouble Codes",
            message="All systems operating normally. No active or stored fault codes detected.",
            icon="✅",
            action_label="",
            action_callback=None,
        ))

    st.markdown(f"<div style='margin-bottom: {GAP_SECTION};'></div>", unsafe_allow_html=True)

    # Diagnostic Summary Section
    section_header(
        title="Diagnostic Summary",
        description="Overview of detected issues by severity"
    )

    dtc_count = len(dtcs)
    critical_count = sum(1 for d in dtcs if d.severity == "critical")
    major_count = sum(1 for d in dtcs if d.severity == "major")
    minor_count = sum(1 for d in dtcs if d.severity == "minor")
    info_count = sum(1 for d in dtcs if d.severity == "info")

    summary_items = [
        ("Total DTCs", str(dtc_count), TEXT_PRIMARY),
        ("Critical", str(critical_count), DIAG_CRITICAL),
        ("Major", str(major_count), DIAG_MAJOR),
        ("Minor", str(minor_count), DIAG_MINOR),
        ("Info", str(info_count), DIAG_INFO),
    ]

    summary_cards = []
    for label, value, color in summary_items:
        card_html = card_simple(
            title=label,
            content=f'<div style="font-size: 2.5rem; font-weight: 700; color: {color}; font-variant-numeric: tabular-nums; line-height: 1;">{value}</div>',
            footer="",
            elevated=False,
            bordered=True,
            padding="lg",
            align="center",
        )
        summary_cards.append(f'<div class="i20-grid-item">{card_html}</div>')

    st.markdown(f"""
    <style>{AUTO_FIT_METRIC_CSS}</style>
    <div class="i20-grid-auto-fit-metric">
        {''.join(summary_cards)}
    </div>
    """, unsafe_allow_html=True)

    # Recommended Actions
    if dtcs:
        st.markdown(f"<div style='margin-bottom: {GAP_SECTION};'></div>", unsafe_allow_html=True)
        section_header(
            title="Recommended Actions",
            description="Verification steps for detected issues"
        )

        # Build lookup from DEMO_DTCS for verification steps
        demo_dtc_lookup = {dtc["code"]: dtc for dtc in DEMO_DTCS}

        for dtc in dtcs:
            demo_dtc = demo_dtc_lookup.get(dtc.code)
            if demo_dtc and "recommended_verification" in demo_dtc:
                with st.expander(f"🔧 {dtc.code} — {dtc.description}", expanded=False):
                    for i, action in enumerate(demo_dtc["recommended_verification"], 1):
                        card_simple(
                            title="",
                            content=f"""
                            <div style="display: flex; align-items: flex-start; gap: {SPACE_3};">
                                <span style="
                                    flex-shrink: 0;
                                    width: 24px; height: 24px;
                                    border-radius: 50%;
                                    background: {ACCENT_PRIMARY};
                                    color: {TEXT_ON_ACCENT};
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                    font-size: {FONT_SIZE_CAPTION};
                                    font-weight: 600;
                                ">{i}</span>
                                <span style="font-size: {FONT_SIZE_BODY_SM}; color: {TEXT_PRIMARY}; line-height: 1.5;">{action}</span>
                            </div>
                            """,
                            footer="",
                            elevated=False,
                            bordered=True,
                            padding="sm",
                        )

    # Clear DTCs button (simulation only) - RESPONSIVE
    if dtcs and obd_service.mode.value == "simulation":
        st.markdown(f"<div style='margin-top: {GAP_SECTION};'></div>", unsafe_allow_html=True)
        if button_danger("🗑️ Clear All DTCs (Simulation)", key="clear_dtcs", use_container_width=True):
            if obd_service.clear_dtcs():
                alert("Success", "DTCs cleared (simulation mode)", AlertVariant.SUCCESS, key="dtcs_cleared")
                st.rerun()
            else:
                alert("Error", "Failed to clear DTCs", AlertVariant.CRITICAL, key="dtcs_clear_failed")
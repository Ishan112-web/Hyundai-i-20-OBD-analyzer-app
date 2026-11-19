"""
i20 AI Garage - OBD Connection Wizard

Professional UI workflow for real OBD-II connectivity:
1. Select OBD mode
2. Discover COM ports
3. Select adapter
4. Connect
5. Detect ECU
6. Discover supported PIDs
7. Display connection success or failure
8. Allow disconnect

FULLY RESPONSIVE: mobile-first fluid grid, auto-fit cards, responsive wizard.
"""

import streamlit as st
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from config import (
    OBD_REAL_CONFIG, PID_POLLING_CONFIG,
    THEME, VEHICLE_INFO
)
from services import (
    get_obd_service, get_database,
    ConnectionManager, PortInfo, ConnectionState, OBDMode
)

# Design System imports
from components.ui import (
    # Layout
    page_header, section_header, inject_global_css, initialize_layout,
    # Components
    card, card_simple, badge, alert, button_primary, button_secondary,
    button_ghost, button_danger, text_input, selectbox, empty_state,
    spinner, skeleton_card, WizardStep, WizardProps, wizard,
    # Tokens
    ACCENT_PRIMARY, ACCENT_PRIMARY_HOVER, ACCENT_PRIMARY_ACTIVE, ACCENT_SECONDARY,
    STATUS_SUCCESS, STATUS_WARNING, STATUS_CRITICAL, STATUS_INFO, STATUS_NEUTRAL,
    SURFACE_PRIMARY, SURFACE_SECONDARY, SURFACE_INTERACTIVE,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_ON_ACCENT,
    BORDER_DEFAULT, BORDER_SUBTLE, BORDER_FOCUS,
    DATASOURCE_SIMULATION, DATASOURCE_REAL,
    SPACE_1, SPACE_2, SPACE_3, SPACE_4, SPACE_5, SPACE_6,
    GAP_INLINE, GAP_FIELD, GAP_CARD_GRID, GAP_SECTION,
    FONT_SIZE_LABEL, FONT_SIZE_BODY, FONT_SIZE_BODY_SM, FONT_SIZE_CAPTION,
    FONT_WEIGHT_LABEL, FONT_WEIGHT_BODY,
    LETTER_SPACING_LABEL, LETTER_SPACING_CAPTION,
    RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_PILL,
    SHADOW_SM, SHADOW_MD, SHADOW_FOCUS,
    TRANSITION_FAST, TRANSITION_NORMAL,
    WIZARD_CARD_RADIUS, WIZARD_CARD_SHADOW, WIZARD_CARD_PADDING,
    BUTTON_MIN_HEIGHT, BUTTON_PADDING_VERTICAL, BUTTON_PADDING_HORIZONTAL,
    BUTTON_RADIUS, BUTTON_FONT_SIZE, BUTTON_FONT_WEIGHT,
    BADGE_PADDING_VERTICAL, BADGE_PADDING_HORIZONTAL, BADGE_RADIUS,
    BADGE_FONT_SIZE, BADGE_FONT_WEIGHT,
    CARD_RADIUS, CARD_PADDING, CARD_BORDER,
    INPUT_HEIGHT, INPUT_PADDING_VERTICAL, INPUT_PADDING_HORIZONTAL,
    INPUT_RADIUS, INPUT_FONT_SIZE,
    FONT_SIZE_H3, FONT_SIZE_H2, FONT_SIZE_H4,
    FONT_FAMILY_MONO, FONT_WEIGHT_NUMERIC,
    AUTO_FIT_CARD_CSS, AUTO_FIT_METRIC_CSS,
    BadgeVariant,
)


def render_obd_connection():
    """Render the OBD Connection Wizard page using Design System - FULLY RESPONSIVE."""
    # Initialize design system
    inject_global_css()
    initialize_layout()

    obd_service = get_obd_service()

    # Initialize wizard state
    if "wizard_step" not in st.session_state:
        st.session_state.wizard_step = 1
    if "wizard_selected_port" not in st.session_state:
        st.session_state.wizard_selected_port = None
    if "wizard_discovered_ports" not in st.session_state:
        st.session_state.wizard_discovered_ports = []
    if "wizard_connection_log" not in st.session_state:
        st.session_state.wizard_connection_log = []
    if "wizard_auto_connect" not in st.session_state:
        st.session_state.wizard_auto_connect = False

    # Get current OBD status
    obd_status = obd_service.get_status()
    is_connected = obd_status.get("connection_state") == "connected"

    # If already connected in real mode, show connected state
    if is_connected and obd_status.get("mode") == "real":
        render_connected_state(obd_service, obd_status)
        return

    # Page header
    page_header(
        title="OBD Connection",
        subtitle="Connect to your Hyundai i20 via ELM327 adapter or use simulation mode",
        icon="🔌"
    )

    # Wizard steps definition - 8 steps with full accessibility support
    wizard_steps = [
        WizardStep(
            label="Mode",
            icon="1",
            description="Select OBD connection mode: Simulation or Real OBD-II hardware"
        ),
        WizardStep(
            label="Discover",
            icon="2",
            description="Scan for available serial ports and ELM327 adapters"
        ),
        WizardStep(
            label="Select",
            icon="3",
            description="Choose the serial port and configure connection parameters"
        ),
        WizardStep(
            label="Connect",
            icon="4",
            description="Establish connection to the ELM327 adapter and vehicle ECU"
        ),
        WizardStep(
            label="ECU",
            icon="5",
            description="Detect vehicle ECU and read identification information (VIN, CALID, CVN)"
        ),
        WizardStep(
            label="PIDs",
            icon="6",
            description="Discover supported Parameter IDs (PIDs) for real-time data"
        ),
        WizardStep(
            label="Success",
            icon="7",
            description="Connection successful - ready for diagnostics"
        ),
        WizardStep(
            label="Error",
            icon="8",
            description="Connection failed - view troubleshooting steps and retry options"
        ),
    ]

    # Build step content based on current step
    step_content = ""
    current_step_idx = st.session_state.wizard_step - 1

    # Step 1: Mode Selection
    if st.session_state.wizard_step == 1:
        step_content = render_step_mode_selection(obd_service)

    # Step 2: Port Discovery
    elif st.session_state.wizard_step == 2:
        step_content = render_step_port_discovery(obd_service)

    # Step 3: Port Selection
    elif st.session_state.wizard_step == 3:
        step_content = render_step_port_selection(obd_service)

    # Step 4: Connection
    elif st.session_state.wizard_step == 4:
        step_content = render_step_connection(obd_service)

    # Step 5: ECU Detection
    elif st.session_state.wizard_step == 5:
        step_content = render_step_ecu_detection(obd_service)

    # Step 6: PID Discovery
    elif st.session_state.wizard_step == 6:
        step_content = render_step_pid_discovery(obd_service)

    # Step 7: Success
    elif st.session_state.wizard_step == 7:
        step_content = render_step_success(obd_service)

    # Step 8: Error
    elif st.session_state.wizard_step == 8:
        step_content = render_step_error(obd_service)

    # Update step states based on current step
    for i, step in enumerate(wizard_steps):
        if i < current_step_idx:
            step.completed = True
            step.active = False
            step.error = False
        elif i == current_step_idx:
            step.completed = False
            step.active = True
            step.error = False
        else:
            step.completed = False
            step.active = False
            step.error = False

    # Mark error step if on step 8 (error)
    if st.session_state.wizard_step == 8:
        wizard_steps[7].error = True
        wizard_steps[7].active = True

    # Render wizard component with accessibility features
    wizard_props = WizardProps(
        steps=wizard_steps,
        current_step=current_step_idx,
        content=step_content,
        next_label="Next",
        prev_label="Back",
        finish_label="Finish",
        on_next=wizard_next,
        on_prev=wizard_prev,
        on_finish=wizard_finish,
        key="obd_wizard",
        announce_step_change=True,
        live_region_id="i20-live-polite",
        show_progress=True,
    )
    wizard(wizard_props)

    # Show connection logs at bottom
    render_connection_logs()


def wizard_next():
    """Handle wizard next button."""
    if st.session_state.wizard_step < 8:
        st.session_state.wizard_step += 1
        st.rerun()


def wizard_prev():
    """Handle wizard previous button."""
    if st.session_state.wizard_step > 1:
        st.session_state.wizard_step -= 1
        st.rerun()


def wizard_finish():
    """Handle wizard finish button."""
    # On step 7 (success), go to dashboard
    if st.session_state.wizard_step == 7:
        st.session_state.current_page = "dashboard"
        st.session_state.wizard_step = 1
        # Reset wizard state
        for key in ["connection_attempted", "ecu_detected", "pids_discovered", "vehicle_info"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()


def render_step_mode_selection(obd_service) -> str:
    """Step 1: Select OBD mode (Simulation vs Real). Returns HTML content - RESPONSIVE."""
    # Simulation mode card
    sim_card = card_simple(f"""
<div style="text-align: center; padding: {SPACE_4} 0;">
  <h3 style="color: {STATUS_WARNING}; margin: 0 0 {SPACE_2} 0;">📱 Simulation Mode</h3>
  <p style="color: {TEXT_SECONDARY}; margin: 0; line-height: 1.6;">
    Demo data with realistic driving scenarios (idle, city, highway, acceleration, overheating).<br>
    No hardware required. Perfect for learning and testing.
  </p>
</div>
""", elevated=True)

    # Real mode card
    real_card = card_simple(f"""
<div style="text-align: center; padding: {SPACE_4} 0;">
  <h3 style="color: {STATUS_SUCCESS}; margin: 0 0 {SPACE_2} 0;">🔌 Real OBD-II Mode</h3>
  <p style="color: {TEXT_SECONDARY}; margin: 0; line-height: 1.6;">
    Connect to actual ELM327 adapter via USB, Bluetooth, or WiFi.<br>
    Live data from your Hyundai i20 Asta 2023 ECU.
  </p>
</div>
""", elevated=True)

    # Buttons - RESPONSIVE (full width on mobile)
    sim_clicked = button_primary(
        "Select Simulation Mode",
        key="select_sim",
        use_container_width=True,
        icon="📱"
    )
    if sim_clicked:
        obd_service.set_mode(OBDMode.SIMULATION)
        obd_service.start_simulation("idle")
        st.session_state.obd_connected = True
        alert("Simulation Activated", "Simulation mode is now running with idle scenario.", AlertVariant.SUCCESS, key="sim_alert")
        st.rerun()

    real_clicked = button_secondary(
        "Select Real OBD Mode",
        key="select_real",
        use_container_width=True,
        icon="🔌"
    )
    if real_clicked:
        st.session_state.wizard_step = 2
        st.rerun()

    # Build content using AUTO_FIT_CARD_CSS for responsive grid
    st.markdown(AUTO_FIT_CARD_CSS, unsafe_allow_html=True)
    st.markdown(f'''
<div class="i20-grid-auto-fit" style="margin-bottom: {SPACE_4};">
  <div class="i20-grid-item">{sim_card}</div>
  <div class="i20-grid-item">{real_card}</div>
</div>
''', unsafe_allow_html=True)

    st.markdown(f"""
<div style="margin-top: {SPACE_4}; padding-top: {SPACE_4}; border-top: 1px solid {BORDER_SUBTLE};">
  <p style="color: {TEXT_MUTED}; font-size: {FONT_SIZE_CAPTION}; margin: 0;">
    💡 In simulation mode, all data is generated. In real mode, you'll need an ELM327-compatible OBD-II adapter.
  </p>
</div>
""", unsafe_allow_html=True)

    return ""


def render_step_port_discovery(obd_service) -> str:
    """Step 2: Discover COM ports. Returns HTML content - RESPONSIVE."""
    # Auto-discovery
    if not st.session_state.wizard_discovered_ports:
        with st.spinner("Scanning serial ports..."):
            ports = obd_service.discover_ports()
            st.session_state.wizard_discovered_ports = ports
            add_log_entry("discover", f"Found {len(ports)} serial port(s)")

    ports = st.session_state.wizard_discovered_ports

    if not ports:
        empty = empty_state(EmptyStateProps(
            title="No Serial Ports Found",
            message="Make sure your ELM327 adapter is connected and powered on.",
            icon="🔍",
            action_label="Rescan Ports",
            action_callback=lambda: (setattr(st.session_state, 'wizard_discovered_ports', []), st.rerun()),
            action_key="rescan_empty"
        ))
        return f"""
<div style="display: flex; flex-direction: column; gap: {GAP_CARD_GRID};">
  <div>{empty}</div>
  <div style="display: flex; gap: {GAP_FIELD}; flex-wrap: wrap;">
    <div style="flex: 1; min-width: 200px;"></div>
    <div style="flex: 1; min-width: 200px;"></div>
  </div>
</div>
"""

    # Port cards using design system badge component - RESPONSIVE using AUTO_FIT_CARD_CSS
    port_cards = []
    for port in ports:
        if port.is_likely_obd:
            likely_badge = badge(label="✓ Likely OBD Adapter", variant=BadgeVariant.SUCCESS, key=f"port_likely_{port.device}")
        else:
            likely_badge = badge(label="Standard Serial Port", variant=BadgeVariant.NEUTRAL, key=f"port_std_{port.device}")

        port_card = card_simple(
            title=port.device,
            content=f"""
            <div style="color: {TEXT_SECONDARY}; font-size: {FONT_SIZE_BODY_SM}; line-height: 1.6;">
                <strong>{port.description}</strong>
                <div style="display: flex; gap: {SPACE_4}; margin-top: {SPACE_2}; flex-wrap: wrap;">
                    <div><span style="color: {TEXT_PRIMARY}; font-weight: {FONT_WEIGHT_LABEL};">Manufacturer:</span> {port.manufacturer or "Unknown"}</div>
                    <div><span style="color: {TEXT_PRIMARY}; font-weight: {FONT_WEIGHT_LABEL};">VID/PID:</span> {f"{port.vid:04X}:{port.pid:04X}" if port.vid and port.pid else "Unknown"}</div>
                    <div><span style="color: {TEXT_PRIMARY}; font-weight: {FONT_WEIGHT_LABEL};">Serial:</span> {port.serial_number or "Unknown"}</div>
                </div>
            </div>
            """,
            footer=likely_badge,
            elevated=False,
            bordered=True,
            padding="md",
        )
        port_cards.append(f'<div class="i20-grid-item">{port_card}</div>')

    # Navigation buttons - RESPONSIVE
    rescan_clicked = button_ghost("🔄 Rescan Ports", key="rescan_ports", use_container_width=True)
    if rescan_clicked:
        st.session_state.wizard_discovered_ports = []
        st.rerun()

    back_clicked = button_secondary("⬅️ Back", key="back_from_discover", use_container_width=True)
    if back_clicked:
        st.session_state.wizard_step = 1
        st.rerun()

    # Continue button if likely ports found
    likely_ports = [p for p in ports if p.is_likely_obd]
    continue_content = ""
    if likely_ports:
        continue_clicked = button_primary(
            f"➡️ Continue with {likely_ports[0].device} (Recommended)",
            key="continue_recommended",
            use_container_width=True
        )
        if continue_clicked:
            st.session_state.wizard_selected_port = likely_ports[0].device
            st.session_state.wizard_step = 4
            st.rerun()
        continue_content = f"""
<div style="margin-top: {SPACE_4}; padding-top: {SPACE_4}; border-top: 1px solid {BORDER_SUBTLE};">
  <p style="color: {TEXT_MUTED}; font-size: {FONT_SIZE_CAPTION}; margin: 0 0 {SPACE_2} 0;">Recommended port detected:</p>
</div>
"""

    st.markdown(AUTO_FIT_CARD_CSS, unsafe_allow_html=True)
    st.markdown(f"""
<div style="display: flex; flex-direction: column; gap: {GAP_CARD_GRID};">
  <div>
    <h4 style="margin: 0 0 {SPACE_2} 0; color: {TEXT_PRIMARY};">Found {len(ports)} port(s):</h4>
    <div class="i20-grid-auto-fit">
        {''.join(port_cards)}
    </div>
  </div>
  {continue_content}
  <div style="margin-top: {SPACE_4}; padding-top: {SPACE_4}; border-top: 1px solid {BORDER_SUBTLE};">
    <div style="display: flex; gap: {GAP_FIELD}; flex-wrap: wrap;">
      <div style="flex: 1; min-width: 150px;"></div>
      <div style="flex: 1; min-width: 150px;"></div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    return ""


def render_step_port_selection(obd_service) -> str:
    """Step 3: Select adapter port and configure connection. Returns HTML content - RESPONSIVE."""
    ports = st.session_state.wizard_discovered_ports

    if not ports:
        alert("No Ports Discovered", "Please go back and discover ports first.", AlertVariant.WARNING, key="no_ports_warn")
        back_clicked = button_secondary("⬅️ Back to Discovery", key="back_to_discover", use_container_width=True)
        if back_clicked:
            st.session_state.wizard_step = 2
            st.rerun()
        return ""

    # Port selection - RESPONSIVE (full width)
    port_options = {f"{p.device} - {p.description}": p.device for p in ports}
    default_idx = 0
    if st.session_state.wizard_selected_port:
        for i, (label, device) in enumerate(port_options.items()):
            if device == st.session_state.wizard_selected_port:
                default_idx = i
                break

    selected_label = selectbox(
        "Select Serial Port",
        options=list(port_options.keys()),
        index=default_idx,
        key="port_select",
        help_text="Choose the COM port your ELM327 adapter is connected to"
    )
    st.session_state.wizard_selected_port = port_options[selected_label]

    # Connection parameters - RESPONSIVE (columns stack on mobile)
    col1, col2 = st.columns(2, gap="medium")
    with col1:
        baudrate = selectbox(
            "Baud Rate",
            options=[str(b) for b in OBD_REAL_CONFIG["preferred_baudrates"]],
            index=0,
            key="baudrate_select",
            help_text="Communication speed. Most ELM327 adapters use 38400."
        )

        timeout = text_input(
            "Connection Timeout (seconds)",
            value=str(OBD_REAL_CONFIG["connection_timeout"]),
            key="timeout_input",
            help_text="How long to wait for connection"
        )

    with col2:
        protocol = selectbox(
            "Protocol",
            options=OBD_REAL_CONFIG["preferred_protocols"],
            index=0,
            key="protocol_select",
            help_text="OBD-II protocol. AUTO detects automatically."
        )

        query_timeout = text_input(
            "Query Timeout (seconds)",
            value=str(OBD_REAL_CONFIG["query_timeout"]),
            key="query_timeout_input",
            help_text="How long to wait for PID responses"
        )

    # Navigation - RESPONSIVE
    col1, col2 = st.columns(2, gap="small")
    with col1:
        back_clicked = button_secondary("⬅️ Back", key="back_from_config", use_container_width=True)
        if back_clicked:
            st.session_state.wizard_step = 2
            st.rerun()

    with col2:
        connect_clicked = button_primary("➡️ Connect", key="connect_from_config", use_container_width=True)
        if connect_clicked:
            st.session_state.wizard_step = 4
            st.rerun()

    return ""


def render_step_connection(obd_service) -> str:
    """Step 4: Connect to OBD adapter. Returns HTML content - RESPONSIVE."""
    # Show connection details - RESPONSIVE grid
    detail_cards = f"""
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: {GAP_FIELD}; margin-bottom: {SPACE_4};">
  <div style="background: {SURFACE_SECONDARY}; border: 1px solid {BORDER_DEFAULT}; border-radius: {RADIUS_MD}; padding: {SPACE_3};">
    <div style="font-size: {FONT_SIZE_CAPTION}; color: {TEXT_MUTED}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_CAPTION}; margin-bottom: {SPACE_1};">Port</div>
    <div style="font-family: {FONT_FAMILY_MONO}; font-size: {FONT_SIZE_BODY}; font-weight: {FONT_WEIGHT_LABEL};">{st.session_state.wizard_selected_port}</div>
  </div>
  <div style="background: {SURFACE_SECONDARY}; border: 1px solid {BORDER_DEFAULT}; border-radius: {RADIUS_MD}; padding: {SPACE_3};">
    <div style="font-size: {FONT_SIZE_CAPTION}; color: {TEXT_MUTED}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_CAPTION}; margin-bottom: {SPACE_1};">Baud Rate</div>
    <div style="font-family: {FONT_FAMILY_MONO}; font-size: {FONT_SIZE_BODY}; font-weight: {FONT_WEIGHT_LABEL};">{OBD_REAL_CONFIG['preferred_baudrates'][0]}</div>
  </div>
</div>
"""

    # Perform connection
    if "connection_attempted" not in st.session_state:
        st.session_state.connection_attempted = False

    if not st.session_state.connection_attempted:
        st.session_state.connection_attempted = True

        # We can't easily show progress bar in returned HTML, so we use a different pattern
        # The connection logic runs on rerun
        pass

    if obd_service.connection_state == ConnectionState.CONNECTED:
        st.session_state.wizard_step = 5
        st.rerun()
        return ""

    if st.session_state.connection_attempted:
        if obd_service.connection_state == ConnectionState.CONNECTED:
            return f"""
<div style="text-align: center; padding: {SPACE_6};">
  <div style="font-size: 4rem; color: {STATUS_SUCCESS}; margin-bottom: {SPACE_3};">✅</div>
  <h3 style="margin: 0 0 {SPACE_2} 0; color: {TEXT_PRIMARY};">Connected Successfully!</h3>
  <p style="color: {TEXT_SECONDARY}; font-size: {FONT_SIZE_BODY_LG}; margin: 0;">ELM327 adapter connected and ready.</p>
  <div style="margin-top: {SPACE_6};">
  </div>
</div>
"""
        else:
            retry_clicked = button_primary("🔄 Retry Connection", key="retry_connect", use_container_width=True)
            if retry_clicked:
                st.session_state.connection_attempted = False
                st.rerun()

            back_clicked = button_secondary("⬅️ Back to Port Selection", key="back_to_port", use_container_width=True)
            if back_clicked:
                st.session_state.wizard_step = 3
                st.session_state.connection_attempted = False
                st.rerun()

            return f"""
<div style="text-align: center; padding: {SPACE_6};">
  <div style="font-size: 4rem; color: {STATUS_CRITICAL}; margin-bottom: {SPACE_3};">❌</div>
  <h3 style="margin: 0 0 {SPACE_2} 0; color: {TEXT_PRIMARY};">Connection Failed</h3>
  <p style="color: {TEXT_SECONDARY}; font-size: {FONT_SIZE_BODY_LG}; margin: 0;">Unable to connect to the OBD-II adapter.</p>
  <div style="margin-top: {SPACE_6}; display: flex; gap: {GAP_FIELD}; justify-content: center; flex-wrap: wrap;">
  </div>
</div>
"""

    # Initial connection state - show progress
    return f"""
{detail_cards}
<div style="text-align: center; padding: {SPACE_6};">
  <div style="font-size: 3rem; color: {ACCENT_PRIMARY}; margin-bottom: {SPACE_3};">🔌</div>
  <h3 style="margin: 0 0 {SPACE_2} 0; color: {TEXT_PRIMARY};">Connecting...</h3>
  <p style="color: {TEXT_SECONDARY}; margin: 0;">Establishing connection to ELM327 adapter and vehicle ECU...</p>
</div>
"""


def render_step_ecu_detection(obd_service) -> str:
    """Step 5: Detect ECU and get vehicle info. Returns HTML content - RESPONSIVE."""
    if "ecu_detected" not in st.session_state:
        st.session_state.ecu_detected = False

    if not st.session_state.ecu_detected:
        st.session_state.ecu_detected = True

        vehicle_info = {}
        steps = [
            ("Reading VIN...", "vin"),
            ("Reading CALID...", "calid"),
            ("Reading CVN...", "cvn"),
            ("Reading ECU Name...", "ecu_name"),
            ("Reading Fuel System Status...", "fuel_status"),
            ("Reading Engine Runtime...", "runtime"),
        ]

        # Show skeleton while detecting - RESPONSIVE
        skeleton_html = ""
        for i, (text, key) in enumerate(steps):
            skeleton_html += f"""
<div style="background: {SURFACE_SECONDARY}; border: 1px solid {BORDER_DEFAULT}; border-radius: {RADIUS_MD}; padding: {SPACE_3}; margin-bottom: {SPACE_2};">
  <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: {SPACE_2};">
    <span style="color: {TEXT_PRIMARY}; font-weight: {FONT_WEIGHT_LABEL};">{text}</span>
    <div style="width: 120px; height: 1.5rem; background: linear-gradient(90deg, {SURFACE_SECONDARY} 25%, {SURFACE_INTERACTIVE} 50%, {SURFACE_SECONDARY} 75%); background-size: 200% 100%; animation: i20-skeleton-pulse 1.5s ease-in-out infinite; border-radius: {RADIUS_SM};"></div>
  </div>
</div>
"""

        return f"""
<div style="display: flex; flex-direction: column; gap: {GAP_FIELD};">
  {skeleton_html}
</div>
"""

    # Display results - RESPONSIVE grid
    vehicle_info = st.session_state.get("vehicle_info", {})

    info_fields = [
        ("VIN", vehicle_info.get("vin") or "Not available"),
        ("CALID", vehicle_info.get("calid") or "Not available"),
        ("CVN", vehicle_info.get("cvn") or "Not available"),
        ("ECU Name", vehicle_info.get("ecu_name") or "Not available"),
        ("Fuel System", vehicle_info.get("fuel_status") or "Not available"),
        ("Engine Runtime", f"{vehicle_info.get('runtime', 0):.0f}s" if vehicle_info.get("runtime") else "Not available"),
    ]

    info_cards = []
    for label, value in info_fields:
        info_cards.append(f"""
<div style="background: {SURFACE_SECONDARY}; border: 1px solid {BORDER_DEFAULT}; border-radius: {RADIUS_MD}; padding: {SPACE_3};">
  <div style="font-size: {FONT_SIZE_CAPTION}; color: {TEXT_MUTED}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_CAPTION}; margin-bottom: {SPACE_1};">{label}</div>
  <div style="font-family: {FONT_FAMILY_MONO}; font-size: {FONT_SIZE_BODY_SM}; color: {TEXT_PRIMARY}; word-break: break-all;">{value}</div>
</div>
""")

    # Navigation - RESPONSIVE
    col1, col2 = st.columns(2, gap="small")
    with col1:
        back_clicked = button_secondary("⬅️ Back", key="back_from_ecu", use_container_width=True)
        if back_clicked:
            st.session_state.wizard_step = 4
            st.rerun()

    with col2:
        continue_clicked = button_primary("➡️ Discover Supported PIDs", key="continue_pids", use_container_width=True)
        if continue_clicked:
            st.session_state.wizard_step = 6
            st.rerun()

    st.markdown(f"""
<div style="display: flex; flex-direction: column; gap: {GAP_CARD_GRID};">
  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: {GAP_CARD_GRID};">
    {''.join(info_cards)}
  </div>
  <div style="margin-top: {SPACE_4}; padding-top: {SPACE_4}; border-top: 1px solid {BORDER_SUBTLE};">
    <div style="display: flex; gap: {GAP_FIELD}; flex-wrap: wrap;">
      <div style="flex: 1; min-width: 150px;"></div>
      <div style="flex: 2; min-width: 200px;"></div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    return ""


def render_step_pid_discovery(obd_service) -> str:
    """Step 6: Discover supported PIDs. Returns HTML content - RESPONSIVE."""
    if "pids_discovered" not in st.session_state:
        st.session_state.pids_discovered = False

    if not st.session_state.pids_discovered:
        st.session_state.pids_discovered = True

        if obd_service.real_adapter:
            pids = obd_service.real_adapter.supported_pids
            obd_service.pid_registry.set_supported_pids(pids)
            add_log_entry("pid", f"Discovered {len(pids)} supported PIDs")

        return f"""
<div style="text-align: center; padding: {SPACE_6};">
  <div style="font-size: 3rem; color: {ACCENT_PRIMARY}; margin-bottom: {SPACE_3};">📋</div>
  <h3 style="margin: 0 0 {SPACE_2} 0; color: {TEXT_PRIMARY};">Discovering Supported PIDs</h3>
  <p style="color: {TEXT_SECONDARY}; margin: 0;">Querying the ECU to determine which PIDs are supported...</p>
</div>
"""

    # Display supported PIDs - RESPONSIVE using AUTO_FIT_CARD_CSS
    pids = obd_service.pid_registry.supported_pids
    registry_summary = obd_service.pid_registry.get_registry_summary()

    # PID grid using design system card_simple
    pid_items = []
    for pid_def in obd_service.pid_registry.get_active_pids():
        is_supported = pid_def.pid in pids
        if is_supported:
            status_variant = BadgeVariant.SUCCESS
            status_text = "Supported"
        else:
            status_variant = BadgeVariant.WARNING
            status_text = "Not Supported"

        status_badge = badge(label=status_text, variant=status_variant, key=f"pid_status_{pid_def.pid}")

        pid_card = card_simple(
            title=pid_def.pid,
            content=f"""
            <div style="font-size: {FONT_SIZE_CAPTION}; color: {TEXT_SECONDARY}; margin-bottom: {SPACE_2}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{pid_def.name}</div>
            {status_badge}
            """,
            footer="",
            elevated=False,
            bordered=True,
            padding="md",
            align="center",
        )
        pid_items.append(f'<div class="i20-grid-item">{pid_card}</div>')

    unsupported = registry_summary.get("unsupported_count", 0)
    unsupported_msg = ""
    if unsupported > 0:
        unsupported_msg = f'<p style="color: {TEXT_MUTED}; font-size: {FONT_SIZE_CAPTION}; margin: {SPACE_3} 0 0 0;">⚠️ {unsupported} standard PIDs not supported by this vehicle (normal for some models)</p>'

    # Navigation - RESPONSIVE
    col1, col2 = st.columns(2, gap="small")
    with col1:
        back_clicked = button_secondary("⬅️ Back", key="back_from_pids", use_container_width=True)
        if back_clicked:
            st.session_state.wizard_step = 5
            st.rerun()

    with col2:
        complete_clicked = button_primary("✅ Complete Setup", key="complete_setup", use_container_width=True)
        if complete_clicked:
            st.session_state.wizard_step = 7
            st.session_state.obd_connected = True
            st.rerun()

    st.markdown(AUTO_FIT_CARD_CSS, unsafe_allow_html=True)
    st.markdown(f"""
<div style="display: flex; flex-direction: column; gap: {GAP_CARD_GRID};">
  <div>
    <h4 style="margin: 0 0 {SPACE_2} 0; color: {TEXT_PRIMARY};">Supported PIDs: {len(pids)} / {registry_summary['standard_pid_count']} standard</h4>
    <div class="i20-grid-auto-fit">
      {''.join(pid_items)}
    </div>
    {unsupported_msg}
  </div>
  <div style="margin-top: {SPACE_4}; padding-top: {SPACE_4}; border-top: 1px solid {BORDER_SUBTLE};">
    <div style="display: flex; gap: {GAP_FIELD}; flex-wrap: wrap;">
      <div style="flex: 1; min-width: 150px;"></div>
      <div style="flex: 2; min-width: 200px;"></div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    return ""


def render_step_success(obd_service) -> str:
    """Step 7: Connection successful. Returns HTML content - RESPONSIVE."""
    status = obd_service.get_status()

    # Summary metrics using design system card_simple - RESPONSIVE AUTO_FIT_METRIC_CSS
    metric_items = [
        ("Connection", "Live" if status.get("mode") == "real" else "Simulation"),
        ("Port", status.get("port", "N/A")),
        ("Supported PIDs", str(status.get("supported_pids_count", 0))),
        ("Adapter", status.get("adapter_type", "Unknown").title() if status.get("adapter_type") else "N/A"),
        ("Baud Rate", str(status.get("baudrate", "N/A"))),
        ("Protocol", str(status.get("protocol", "N/A"))),
    ]

    metric_cards_list = []
    for label, value in metric_items:
        card_html = card_simple(
            title=label,
            content=f'<div style="font-size: {FONT_SIZE_H3}; font-weight: {FONT_WEIGHT_LABEL}; color: {TEXT_PRIMARY}; font-family: {FONT_FAMILY_MONO};">{value}</div>',
            footer="",
            elevated=False,
            bordered=True,
            padding="lg",
            align="center",
        )
        metric_cards_list.append(f'<div class="i20-grid-item">{card_html}</div>')

    st.markdown(AUTO_FIT_METRIC_CSS, unsafe_allow_html=True)
    metric_cards = f"""
<div class="i20-grid-auto-fit-metric" style="margin-bottom: {SPACE_6};">
    {''.join(metric_cards_list)}
</div>
"""

    # Actions - RESPONSIVE (flex-wrap)
    col1, col2, col3 = st.columns(3, gap="small")
    with col1:
        dash_clicked = button_primary("🏠 Go to Dashboard", key="goto_dashboard", use_container_width=True)
        if dash_clicked:
            st.session_state.current_page = "dashboard"
            st.session_state.wizard_step = 1
            for key in ["connection_attempted", "ecu_detected", "pids_discovered", "vehicle_info"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    with col2:
        diag_clicked = button_secondary("🔧 Go to Diagnostics", key="goto_diagnostics", use_container_width=True)
        if diag_clicked:
            st.session_state.current_page = "diagnostics"
            st.session_state.wizard_step = 1
            for key in ["connection_attempted", "ecu_detected", "pids_discovered", "vehicle_info"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    with col3:
        disc_clicked = button_ghost("🔌 Disconnect", key="disconnect_success", use_container_width=True)
        if disc_clicked:
            obd_service.disconnect()
            st.session_state.obd_connected = False
            st.session_state.wizard_step = 1
            for key in ["connection_attempted", "ecu_detected", "pids_discovered", "vehicle_info",
                        "wizard_selected_port", "wizard_discovered_ports", "wizard_connection_log"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    st.markdown(f"""
<div style="display: flex; flex-direction: column; gap: {GAP_SECTION};">
  <div style="text-align: center; padding: {SPACE_6};">
    <div style="font-size: 4rem; color: {STATUS_SUCCESS}; margin-bottom: {SPACE_3};">✅</div>
    <h3 style="margin: 0 0 {SPACE_2} 0; color: {TEXT_PRIMARY};">Connected Successfully!</h3>
    <p style="color: {TEXT_SECONDARY}; font-size: {FONT_SIZE_BODY_LG}; margin: 0;">Your Hyundai i20 is now connected and ready for real-time diagnostics.</p>
  </div>
  <div>
    <h3 style="margin: 0 0 {SPACE_3} 0; color: {TEXT_PRIMARY};">Connection Summary</h3>
    {metric_cards}
  </div>
  <div style="margin-top: {SPACE_4}; padding-top: {SPACE_4}; border-top: 1px solid {BORDER_SUBTLE};">
    <div style="display: flex; gap: {GAP_FIELD}; flex-wrap: wrap;">
      <div style="flex: 1; min-width: 200px;"></div>
      <div style="flex: 1; min-width: 200px;"></div>
      <div style="flex: 1; min-width: 200px;"></div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    return ""


def render_step_error(obd_service) -> str:
    """Step 8: Connection error. Returns HTML content - RESPONSIVE."""
    # Show error details
    if obd_service.real_adapter:
        error = obd_service.real_adapter._last_error
        if error:
            alert("Connection Error", error, AlertVariant.CRITICAL, key="conn_error")

    troubleshooting_steps = [
        ("🔌 Hardware", "Ensure your ELM327 adapter is firmly plugged into the OBD-II port (under dashboard, near steering column)"),
        ("🔋 Power", "Turn the ignition to ON position (not START) - the ECU needs power but engine doesn't need to be running"),
        ("📱 Pairing", "For Bluetooth/WiFi adapters: pair with Windows first, then check which COM port was assigned"),
        ("🔧 Drivers", "Install FTDI, Silicon Labs CP210x, CH340, or Prolific PL2303 drivers if using USB adapter"),
        ("⚙️ Settings", "Try different baud rates (38400, 115200, 9600, 57600) and protocols (AUTO, 6=CAN)"),
        ("🚗 Vehicle", "Confirm your 2023 Hyundai i20 supports standard OBD-II (it should - all 2001+ petrol, 2004+ diesel)"),
        ("🔄 Retry", "Disconnect and reconnect the adapter, then try again"),
    ]

    trouble_cards = []
    for title, desc in troubleshooting_steps:
        trouble_cards.append(f"""
<div style="background: {SURFACE_PRIMARY}; border: 1px solid {BORDER_DEFAULT}; border-radius: {RADIUS_MD}; padding: {SPACE_4};">
  <strong style="color: {TEXT_PRIMARY};">{title}</strong>
  <div style="color: {TEXT_SECONDARY}; margin-top: {SPACE_1}; font-size: {FONT_SIZE_BODY_SM};">{desc}</div>
</div>
""")

    # Navigation - RESPONSIVE
    col1, col2 = st.columns(2, gap="small")
    with col1:
        retry_clicked = button_primary("🔄 Retry Connection", key="retry_from_error", use_container_width=True)
        if retry_clicked:
            st.session_state.wizard_step = 4
            st.session_state.connection_attempted = False
            st.rerun()

    with col2:
        back_clicked = button_secondary("⬅️ Back to Port Selection", key="back_from_error", use_container_width=True)
        if back_clicked:
            st.session_state.wizard_step = 3
            st.session_state.connection_attempted = False
            st.rerun()

    st.markdown(f"""
<div style="display: flex; flex-direction: column; gap: {GAP_SECTION};">
  <div style="text-align: center; padding: {SPACE_6};">
    <div style="font-size: 4rem; color: {STATUS_CRITICAL}; margin-bottom: {SPACE_3};">❌</div>
    <h3 style="margin: 0 0 {SPACE_2} 0; color: {TEXT_PRIMARY};">Connection Failed</h3>
    <p style="color: {TEXT_SECONDARY}; font-size: {FONT_SIZE_BODY_LG}; margin: 0;">Unable to connect to the OBD-II adapter. Please check the troubleshooting steps below.</p>
  </div>
  <div>
    <h4 style="margin: 0 0 {SPACE_3} 0; color: {TEXT_PRIMARY};">Troubleshooting</h4>
    <div style="display: flex; flex-direction: column; gap: {GAP_FIELD};">
      {''.join(trouble_cards)}
    </div>
  </div>
  <div style="margin-top: {SPACE_4}; padding-top: {SPACE_4}; border-top: 1px solid {BORDER_SUBTLE};">
    <div style="display: flex; gap: {GAP_FIELD}; flex-wrap: wrap;">
      <div style="flex: 1; min-width: 200px;"></div>
      <div style="flex: 1; min-width: 200px;"></div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    return ""


def render_connected_state(obd_service, obd_status):
    """Render the connected state with disconnect option - RESPONSIVE."""
    inject_global_css()
    initialize_layout()

    page_header(
        title="OBD Connected",
        subtitle="Real-time OBD-II data is streaming from your Hyundai i20 Asta 2023",
        icon="🟢"
    )

    # Connection details using design system card_simple - RESPONSIVE
    section_header("Connection Status", "Live connection metrics")

    metric_items = [
        ("Mode", "Real OBD-II" if obd_status.get("mode") == "real" else "Simulation"),
        ("Port", obd_status.get("port", "N/A")),
        ("PIDs", str(obd_status.get("supported_pids_count", 0))),
        ("Adapter", obd_status.get("adapter_type", "Unknown").title() if obd_status.get("adapter_type") else "N/A"),
    ]

    metric_cards_list = []
    for label, value in metric_items:
        card_html = card_simple(
            title=label,
            content=f'<div style="font-size: {FONT_SIZE_H3}; font-weight: {FONT_WEIGHT_LABEL}; color: {TEXT_PRIMARY}; font-family: {FONT_FAMILY_MONO};">{value}</div>',
            footer="",
            elevated=False,
            bordered=True,
            padding="lg",
            align="center",
        )
        metric_cards_list.append(f'<div class="i20-grid-item">{card_html}</div>')

    st.markdown(AUTO_FIT_METRIC_CSS, unsafe_allow_html=True)
    st.markdown(f"""
<div class="i20-grid-auto-fit-metric">
    {''.join(metric_cards_list)}
</div>
""", unsafe_allow_html=True)

    # Health check using design system card_simple - RESPONSIVE
    health = obd_status.get("health", {})
    if health:
        section_header("Health Check", "Connection diagnostics")

        connected_color = STATUS_SUCCESS if health.get("connected") else STATUS_CRITICAL
        query_color = STATUS_SUCCESS if health.get("query_test") == "passed" else STATUS_CRITICAL

        health_items = [
            ("Connected", "Yes" if health.get("connected") else "No", connected_color),
            ("Query Test", health.get("query_test", "unknown").title(), query_color),
            ("PIDs Available", str(health.get("supported_pids_count", 0)), TEXT_PRIMARY),
        ]

        health_cards_list = []
        for label, value, color in health_items:
            card_html = card_simple(
                title=label,
                content=f'<div style="font-size: {FONT_SIZE_H3}; font-weight: {FONT_WEIGHT_LABEL}; color: {color}; font-family: {FONT_FAMILY_MONO};">{value}</div>',
                footer="",
                elevated=False,
                bordered=True,
                padding="lg",
                align="center",
            )
            health_cards_list.append(f'<div class="i20-grid-item">{card_html}</div>')

        st.markdown(AUTO_FIT_METRIC_CSS, unsafe_allow_html=True)
        st.markdown(f"""
<div class="i20-grid-auto-fit-metric">
    {''.join(health_cards_list)}
</div>
""", unsafe_allow_html=True)

    # Actions - RESPONSIVE
    st.markdown(f"<div style='margin-top: {SPACE_6}; padding-top: {SPACE_4}; border-top: 1px solid {BORDER_SUBTLE};'></div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3, gap="small")
    with col1:
        dash_clicked = button_primary("🏠 Dashboard", key="connected_dashboard", use_container_width=True)
        if dash_clicked:
            st.session_state.current_page = "dashboard"
            st.rerun()

    with col2:
        diag_clicked = button_secondary("🔧 Diagnostics", key="connected_diagnostics", use_container_width=True)
        if diag_clicked:
            st.session_state.current_page = "diagnostics"
            st.rerun()

    with col3:
        disc_clicked = button_ghost("🔌 Disconnect", key="connected_disconnect", use_container_width=True)
        if disc_clicked:
            obd_service.disconnect()
            st.session_state.obd_connected = False
            alert("Disconnected", "Disconnected from OBD adapter", AlertVariant.INFO, key="disc_alert")
            st.rerun()

    # Show connection logs
    render_connection_logs()


def add_log_entry(event_type: str, details: str):
    """Add an entry to the connection log."""
    from datetime import datetime
    entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "event_type": event_type,
        "details": details
    }
    if "wizard_connection_log" not in st.session_state:
        st.session_state.wizard_connection_log = []
    st.session_state.wizard_connection_log.append(entry)


def render_connection_logs():
    """Render connection log history - RESPONSIVE."""
    logs = st.session_state.get("wizard_connection_log", [])

    if not logs:
        return

    with st.expander("📜 Connection Log", expanded=False):
        log_items = []
        for entry in logs[-20:]:  # Show last 20 entries
            event_type = entry["event_type"]
            type_colors = {
                "connect": STATUS_SUCCESS,
                "disconnect": STATUS_WARNING,
                "error": STATUS_CRITICAL,
                "reconnect": ACCENT_PRIMARY,
                "discover": ACCENT_PRIMARY,
                "ecu": ACCENT_PRIMARY,
                "pid": ACCENT_PRIMARY,
            }
            type_color = type_colors.get(event_type, TEXT_SECONDARY)

            log_items.append(f"""
<div style="display: flex; gap: {GAP_FIELD}; padding: {SPACE_2} 0; border-bottom: 1px solid {BORDER_SUBTLE}; font-family: {FONT_FAMILY_MONO}; font-size: {FONT_SIZE_CAPTION};">
  <span style="color: {TEXT_MUTED};">[{entry["timestamp"]}]</span>
  <span style="color: {type_color}; font-weight: {FONT_WEIGHT_LABEL}; text-transform: uppercase;">[{event_type}]</span>
  <span style="color: {TEXT_PRIMARY};">{entry["details"]}</span>
</div>
""")

        clear_clicked = button_ghost("🗑️ Clear Log", key="clear_log", use_container_width=True)
        if clear_clicked:
            st.session_state.wizard_connection_log = []
            st.rerun()

        st.markdown(f"""
<div style="background: {SURFACE_PRIMARY}; border: 1px solid {BORDER_DEFAULT}; border-radius: {RADIUS_MD}; padding: {SPACE_4}; max-height: 300px; overflow-y: auto; font-family: {FONT_FAMILY_MONO}; font-size: {FONT_SIZE_CAPTION};">
  {''.join(log_items)}
</div>
""", unsafe_allow_html=True)
"""
i20 AI Garage - Sidebar Navigation Components

Professional sidebar with navigation menu, vehicle status summary,
connection indicators, and simulation status. Uses THEME from config.py
for consistent styling.
"""

from typing import Optional, Dict, Any, List
import streamlit as st
from config import THEME, VEHICLE_INFO


# Navigation menu items with icons
NAVIGATION_ITEMS = [
    {"id": "dashboard", "label": "Dashboard", "icon": "🏠", "description": "Overview & key metrics"},
    {"id": "diagnostics", "label": "Diagnostics", "icon": "🔧", "description": "DTC codes & health checks"},
    {"id": "performance", "label": "Performance", "icon": "📊", "description": "Telemetry & analytics"},
    {"id": "maintenance", "label": "Maintenance", "icon": "🔩", "description": "Service intervals & history"},
    {"id": "reports", "label": "Reports", "icon": "📋", "description": "Professional report generation"},
    {"id": "vehicle_profile", "label": "Vehicle Profile", "icon": "🚗", "description": "Vehicle specifications"},
    {"id": "ai_assistant", "label": "AI Assistant", "icon": "🤖", "description": "Diagnostic chat assistant"},
    {"id": "obd_connection", "label": "OBD Connection", "icon": "🔌", "description": "Real OBD-II setup & monitor"},
    {"id": "settings", "label": "Settings", "icon": "⚙️", "description": "Configuration & preferences"},
]


def _get_theme_styles() -> Dict[str, str]:
    """Return CSS styles derived from THEME."""
    return {
        "bg_primary": THEME["bg_primary"],
        "bg_secondary": THEME["bg_secondary"],
        "bg_card": THEME["bg_card"],
        "border": THEME["border"],
        "text_primary": THEME["text_primary"],
        "text_secondary": THEME["text_secondary"],
        "accent_blue": THEME["accent_blue"],
        "accent_green": THEME["accent_green"],
        "accent_amber": THEME["accent_amber"],
        "accent_red": THEME["accent_red"],
        "accent_purple": THEME["accent_purple"],
    }


def _inject_sidebar_css():
    """Inject custom CSS for sidebar styling."""
    styles = _get_theme_styles()
    css = f"""
    <style>
    /* Sidebar container */
    [data-testid="stSidebar"] {{
        background-color: {styles["bg_primary"]} !important;
        border-right: 1px solid {styles["border"]} !important;
    }}

    [data-testid="stSidebar"] > div:first-child {{
        background-color: {styles["bg_primary"]} !important;
    }}

    /* Sidebar header */
    .sidebar-header {{
        padding: 1.5rem 1rem 1rem 1rem;
        border-bottom: 1px solid {styles["border"]};
        margin-bottom: 1rem;
    }}

    .sidebar-title {{
        font-size: 1.25rem;
        font-weight: 700;
        color: {styles["text_primary"]};
        margin: 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}

    .sidebar-subtitle {{
        font-size: 0.8rem;
        color: {styles["text_secondary"]};
        margin: 0.25rem 0 0 0;
    }}

    /* Navigation menu */
    .nav-menu {{
        padding: 0 0.5rem;
    }}

    .nav-item {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        margin-bottom: 0.25rem;
        background: transparent;
        border: none;
        width: 100%;
        text-align: left;
        color: {styles["text_secondary"]};
        font-size: 0.9rem;
        font-weight: 500;
    }}

    .nav-item:hover {{
        background-color: {styles["bg_card"]};
        color: {styles["text_primary"]};
    }}

    .nav-item.active {{
        background-color: {styles["bg_card"]};
        color: {styles["accent_blue"]};
        border-left: 3px solid {styles["accent_blue"]};
    }}

    .nav-item .icon {{
        font-size: 1.1rem;
        width: 24px;
        text-align: center;
    }}

    .nav-item .label {{
        flex: 1;
    }}

    /* Vehicle status summary */
    .vehicle-status {{
        padding: 1rem;
        margin: 1rem 0.5rem;
        background-color: {styles["bg_card"]};
        border: 1px solid {styles["border"]};
        border-radius: 10px;
    }}

    .vehicle-status-title {{
        font-size: 0.85rem;
        font-weight: 600;
        color: {styles["text_secondary"]};
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.75rem;
    }}

    .vehicle-info-row {{
        display: flex;
        justify-content: space-between;
        padding: 0.35rem 0;
        border-bottom: 1px solid {styles["border"]};
    }}

    .vehicle-info-row:last-child {{
        border-bottom: none;
    }}

    .vehicle-info-label {{
        color: {styles["text_secondary"]};
        font-size: 0.85rem;
    }}

    .vehicle-info-value {{
        color: {styles["text_primary"]};
        font-size: 0.85rem;
        font-weight: 500;
        text-align: right;
    }}

    /* Connection indicators */
    .connection-indicators {{
        padding: 0 0.5rem 1rem 0.5rem;
    }}

    .indicator-group {{
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }}

    .indicator-item {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.6rem 0.85rem;
        background-color: {styles["bg_card"]};
        border: 1px solid {styles["border"]};
        border-radius: 8px;
    }}

    .indicator-dot {{
        width: 10px;
        height: 10px;
        border-radius: 50%;
        flex-shrink: 0;
    }}

    .indicator-dot.connected {{
        background-color: {styles["accent_green"]};
        box-shadow: 0 0 8px {styles["accent_green"]};
    }}

    .indicator-dot.disconnected {{
        background-color: {styles["accent_red"]};
        box-shadow: 0 0 8px {styles["accent_red"]};
    }}

    .indicator-dot.simulating {{
        background-color: {styles["accent_amber"]};
        box-shadow: 0 0 8px {styles["accent_amber"]};
        animation: pulse 2s infinite;
    }}

    .indicator-dot.ai-connected {{
        background-color: {styles["accent_purple"]};
        box-shadow: 0 0 8px {styles["accent_purple"]};
    }}

    @keyframes pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.5; }}
    }}

    .indicator-info {{
        flex: 1;
        min-width: 0;
    }}

    .indicator-label {{
        font-size: 0.8rem;
        font-weight: 600;
        color: {styles["text_primary"]};
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    .indicator-detail {{
        font-size: 0.7rem;
        color: {styles["text_secondary"]};
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    /* Simulation status */
    .simulation-status {{
        padding: 1rem;
        margin: 0 0.5rem 1rem 0.5rem;
        background-color: {styles["bg_card"]};
        border: 1px solid {styles["border"]};
        border-radius: 10px;
    }}

    .simulation-header {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.75rem;
    }}

    .simulation-badge {{
        font-size: 0.7rem;
        font-weight: 700;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    .simulation-badge.simulation {{
        background-color: rgba(243, 156, 18, 0.2);
        color: {styles["accent_amber"]};
    }}

    .simulation-badge.real {{
        background-color: rgba(46, 204, 113, 0.2);
        color: {styles["accent_green"]};
    }}

    .simulation-scenario {{
        font-size: 0.8rem;
        color: {styles["text_secondary"]};
    }}

    .simulation-scenario strong {{
        color: {styles["text_primary"]};
    }}

    /* Section divider */
    .sidebar-divider {{
        height: 1px;
        background: linear-gradient(90deg, transparent, {styles["border"]}, transparent);
        margin: 1rem 0.5rem;
    }}

    /* Footer */
    .sidebar-footer {{
        padding: 1rem 0.5rem;
        border-top: 1px solid {styles["border"]};
        margin-top: auto;
    }}

    .footer-text {{
        font-size: 0.7rem;
        color: {styles["text_secondary"]};
        text-align: center;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def create_sidebar(
    current_page: str = "dashboard",
    obd_connected: bool = False,
    ai_connected: bool = False,
    simulation_mode: str = "simulation",
    current_scenario: str = "idle",
    obd_status_details: Optional[Dict[str, Any]] = None,
    on_navigate: Optional[callable] = None,
) -> str:
    """
    Create the complete sidebar with navigation, vehicle status, and connection indicators.

    Args:
        current_page: Currently active navigation item ID
        obd_connected: Whether OBD connection is active
        ai_connected: Whether AI/LM Studio connection is active
        simulation_mode: "simulation" or "real"
        current_scenario: Current simulation scenario name
        obd_status_details: Detailed OBD status from get_status()
        on_navigate: Callback function when navigation item is clicked

    Returns:
        The selected page ID (if using session state) or current_page
    """
    _inject_sidebar_css()

    with st.sidebar:
        # Header
        st.markdown(f"""
        <div class="sidebar-header">
            <div class="sidebar-title">
                <span>🏎️</span> i20 AI Garage
            </div>
            <div class="sidebar-subtitle">Hyundai i20 Asta 2023</div>
        </div>
        """, unsafe_allow_html=True)

        # Navigation Menu
        st.markdown('<div class="nav-menu">', unsafe_allow_html=True)
        for item in NAVIGATION_ITEMS:
            is_active = item["id"] == current_page
            active_class = "active" if is_active else ""

            if st.button(
                f"{item['icon']}  {item['label']}",
                key=f"nav_{item['id']}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                if on_navigate:
                    on_navigate(item["id"])
                else:
                    st.session_state.current_page = item["id"]
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # Divider
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

        # Vehicle Status Summary
        create_vehicle_status_summary()

        # Divider
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

        # Connection Indicators
        create_connection_indicators(obd_connected, ai_connected, simulation_mode, obd_status_details)

        # Simulation Status
        create_simulation_status(simulation_mode, current_scenario)

        # Footer
        footer_mode = "Real OBD-II" if simulation_mode == "real" else "Simulation Mode"
        st.markdown(f"""
        <div class="sidebar-footer">
            <div class="footer-text">
                v1.0.0 • {footer_mode}
            </div>
        </div>
        """, unsafe_allow_html=True)

    return st.session_state.get("current_page", current_page)


def create_navigation_menu(
    current_page: str = "dashboard",
    on_navigate: Optional[callable] = None,
) -> str:
    """
    Create just the navigation menu component.

    Args:
        current_page: Currently active navigation item ID
        on_navigate: Callback function when navigation item is clicked

    Returns:
        The selected page ID
    """
    _inject_sidebar_css()

    st.markdown('<div class="nav-menu">', unsafe_allow_html=True)
    for item in NAVIGATION_ITEMS:
        is_active = item["id"] == current_page

        if st.button(
            f"{item['icon']}  {item['label']}",
            key=f"nav_{item['id']}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            if on_navigate:
                on_navigate(item["id"])
            else:
                st.session_state.current_page = item["id"]
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    return st.session_state.get("current_page", current_page)


def create_vehicle_status_summary():
    """Create the vehicle status summary card in the sidebar."""
    _inject_sidebar_css()

    vehicle = VEHICLE_INFO

    st.markdown(f"""
    <div class="vehicle-status">
        <div class="vehicle-status-title">Vehicle Status</div>
        <div class="vehicle-info-row">
            <span class="vehicle-info-label">Make / Model</span>
            <span class="vehicle-info-value">{vehicle['make']} {vehicle['model']}</span>
        </div>
        <div class="vehicle-info-row">
            <span class="vehicle-info-label">Year</span>
            <span class="vehicle-info-value">{vehicle['year']}</span>
        </div>
        <div class="vehicle-info-row">
            <span class="vehicle-info-label">Engine</span>
            <span class="vehicle-info-value">{vehicle['engine']}</span>
        </div>
        <div class="vehicle-info-row">
            <span class="vehicle-info-label">Transmission</span>
            <span class="vehicle-info-value">{vehicle['transmission']}</span>
        </div>
        <div class="vehicle-info-row">
            <span class="vehicle-info-label">Fuel Type</span>
            <span class="vehicle-info-value">{vehicle['fuel_type']}</span>
        </div>
        <div class="vehicle-info-row">
            <span class="vehicle-info-label">Market</span>
            <span class="vehicle-info-value">{vehicle['market']}</span>
        </div>
        <div class="vehicle-info-row">
            <span class="vehicle-info-label">ECU Tuning</span>
            <span class="vehicle-info-value">{vehicle['ecu_tuning']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def create_connection_indicators(
    obd_connected: bool = False,
    ai_connected: bool = False,
    simulation_mode: str = "simulation",
    obd_status_details: Optional[Dict[str, Any]] = None,
):
    """
    Create connection status indicators for OBD and AI.

    Args:
        obd_connected: Whether OBD connection is active
        ai_connected: Whether AI/LM Studio connection is active
        simulation_mode: "simulation" or "real"
        obd_status_details: Detailed OBD status from get_status()
    """
    _inject_sidebar_css()
    styles = _get_theme_styles()

    # Get details from status if provided
    port = "N/A"
    baudrate = "N/A"
    adapter_type = "Unknown"
    supported_pids = 0

    if obd_status_details:
        port = obd_status_details.get("port", "N/A")
        baudrate = obd_status_details.get("baudrate", "N/A")
        adapter_type = obd_status_details.get("adapter_type", "Unknown")
        supported_pids = obd_status_details.get("supported_pids_count", 0)

    # OBD Connection
    obd_status = "connected" if obd_connected else "disconnected"
    obd_label = "Connected" if obd_connected else "Disconnected"
    if obd_connected and simulation_mode == "real":
        obd_detail = f"{port} • {baudrate} baud • {adapter_type} • {supported_pids} PIDs"
    elif obd_connected:
        obd_detail = "Simulation mode active"
    else:
        obd_detail = "Click to connect"

    # Simulation indicator
    sim_status = "simulating" if simulation_mode == "simulation" else "connected"
    sim_label = "Simulation Active" if simulation_mode == "simulation" else "Real OBD Active"
    sim_detail = "Demo data • No real connection" if simulation_mode == "simulation" else f"Live data • {supported_pids} PIDs"

    # AI Connection
    ai_status = "ai-connected" if ai_connected else "disconnected"
    ai_label = "Connected" if ai_connected else "Disconnected"
    ai_detail = "LM Studio • qwen2.5-3b" if ai_connected else "Start LM Studio server"

    st.markdown(f"""
    <div class="connection-indicators">
        <div class="indicator-group">
            <div class="indicator-item">
                <div class="indicator-dot {obd_status}"></div>
                <div class="indicator-info">
                    <div class="indicator-label">OBD-II Connection</div>
                    <div class="indicator-detail">{obd_detail}</div>
                </div>
            </div>
            <div class="indicator-item">
                <div class="indicator-dot {sim_status}"></div>
                <div class="indicator-info">
                    <div class="indicator-label">Data Source</div>
                    <div class="indicator-detail">{sim_detail}</div>
                </div>
            </div>
            <div class="indicator-item">
                <div class="indicator-dot {ai_status}"></div>
                <div class="indicator-info">
                    <div class="indicator-label">AI Assistant</div>
                    <div class="indicator-detail">{ai_detail}</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def create_simulation_status(
    simulation_mode: str = "simulation",
    current_scenario: str = "idle",
):
    """
    Create the simulation status display.

    Args:
        simulation_mode: "simulation" or "real"
        current_scenario: Current simulation scenario key
    """
    _inject_sidebar_css()
    styles = _get_theme_styles()

    from config import SIMULATION_SCENARIOS

    scenario = SIMULATION_SCENARIOS.get(current_scenario, SIMULATION_SCENARIOS["idle"])

    badge_class = "simulation" if simulation_mode == "simulation" else "real"
    badge_text = "SIMULATION" if simulation_mode == "simulation" else "LIVE DATA"

    st.markdown(f"""
    <div class="simulation-status">
        <div class="simulation-header">
            <span class="simulation-badge {badge_class}">{badge_text}</span>
        </div>
        <div class="simulation-scenario">
            <strong>Scenario:</strong> {scenario['name']}
        </div>
        <div class="simulation-scenario" style="margin-top: 0.25rem;">
            {scenario['description']}
        </div>
    </div>
    """, unsafe_allow_html=True)
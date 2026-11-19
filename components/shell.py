"""
i20 AI Garage - Global Application Shell

Unified application shell integrating the Stage 3 design system:
- Global stylesheet injection
- Sidebar navigation
- Top bar with breadcrumbs and status
- Page header and container
- Vehicle context and connection status
"""

from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass

import streamlit as st

from config import THEME, VEHICLE_INFO, SIMULATION_SCENARIOS
from services import get_database, get_ai_service, get_obd_service

from .ui import (
    # Styles
    inject_global_css,
    initialize_layout,
    GLOBAL_STYLESHEET,
    # Layout
    page_header,
    responsive_container,
    LAYOUT_CSS,
    # Components
    SidebarNavItem,
    SidebarProps,
    sidebar,
    TopBarProps,
    top_bar,
    status_indicator,
    # Tokens
    ACCENT_PRIMARY,
    STATUS_SUCCESS, STATUS_WARNING, STATUS_CRITICAL, STATUS_INFO,
    TEXT_PRIMARY, TEXT_SECONDARY,
)

from .ui.accessibility import (
    render_skip_link,
    render_persistent_live_regions,
    render_reduced_motion_detection_script,
    render_landmark_fix_script,
    render_footer,
    get_touch_target_css,
)


# =============================================================================
# NAVIGATION CONFIGURATION
# =============================================================================

# Navigation items matching existing NAVIGATION_ITEMS from sidebar.py
NAVIGATION_ITEMS: List[SidebarNavItem] = [
    SidebarNavItem(
        label="Dashboard",
        icon="🏠",
        page="dashboard",
        description="Overview & key metrics"
    ),
    SidebarNavItem(
        label="Diagnostics",
        icon="🔧",
        page="diagnostics",
        description="DTC codes & health checks"
    ),
    SidebarNavItem(
        label="Performance",
        icon="📊",
        page="performance",
        description="Telemetry & analytics"
    ),
    SidebarNavItem(
        label="Maintenance",
        icon="🔩",
        page="maintenance",
        description="Service intervals & history"
    ),
    SidebarNavItem(
        label="Reports",
        icon="📋",
        page="reports",
        description="Professional report generation"
    ),
    SidebarNavItem(
        label="Vehicle Profile",
        icon="🚗",
        page="vehicle_profile",
        description="Vehicle specifications"
    ),
    SidebarNavItem(
        label="AI Assistant",
        icon="🤖",
        page="ai_assistant",
        description="Diagnostic chat assistant"
    ),
    SidebarNavItem(
        label="OBD Connection",
        icon="🔌",
        page="obd_connection",
        description="Real OBD-II setup & monitor"
    ),
    SidebarNavItem(
        label="Settings",
        icon="⚙️",
        page="settings",
        description="Configuration & preferences"
    ),
]


# =============================================================================
# STATUS HELPERS
# =============================================================================

def get_obd_status_details() -> Dict[str, Any]:
    """Get detailed OBD status from the service."""
    try:
        obd_service = get_obd_service()
        return obd_service.get_status()
    except Exception:
        return {
            "connected": False,
            "mode": "simulation",
            "port": "N/A",
            "baudrate": "N/A",
            "adapter_type": "Unknown",
            "supported_pids_count": 0,
            "connection_state": "disconnected",
            "current_scenario": "idle",
        }


def get_ai_status() -> Dict[str, Any]:
    """Get AI service status."""
    try:
        ai_service = get_ai_service()
        # Fixed: use check_connection() instead of is_available()
        available = ai_service.check_connection()
        return {
            "connected": available,
            "text": "LM Studio • qwen2.5-3b" if available else "Start LM Studio server",
            "status": "success" if available else "critical",
        }
    except Exception:
        return {
            "connected": False,
            "text": "Unavailable",
            "status": "critical",
        }


def get_simulation_status(obd_status: Dict[str, Any]) -> Dict[str, Any]:
    """Get simulation/real mode status."""
    mode = obd_status.get("mode", "simulation")
    current_scenario = obd_status.get("current_scenario", "idle")
    scenario = SIMULATION_SCENARIOS.get(current_scenario, SIMULATION_SCENARIOS["idle"])

    if mode == "simulation":
        return {
            "connected": True,
            "text": f"Simulation • {scenario['name']}",
            "status": "warning",
        }
    else:
        supported_pids = obd_status.get("supported_pids_count", 0)
        return {
            "connected": True,
            "text": f"Live Data • {supported_pids} PIDs",
            "status": "success",
        }


def get_vehicle_info() -> Dict[str, str]:
    """Get vehicle information for display."""
    return {
        "make": VEHICLE_INFO.get("make", ""),
        "model": VEHICLE_INFO.get("model", ""),
        "year": str(VEHICLE_INFO.get("year", "")),
        "engine": VEHICLE_INFO.get("engine", ""),
        "transmission": VEHICLE_INFO.get("transmission", ""),
        "fuel_type": VEHICLE_INFO.get("fuel_type", ""),
        "market": VEHICLE_INFO.get("market", ""),
        "vin": VEHICLE_INFO.get("vin", "N/A"),
    }


# =============================================================================
# SIDEBAR INTEGRATION
# =============================================================================

def render_sidebar(
    current_page: str,
    on_navigate: Callable[[str], None],
    collapsed: bool = False,
    mobile_open: bool = False,
    on_toggle_collapse: Optional[Callable] = None,
    on_toggle_mobile: Optional[Callable] = None,
) -> str:
    """
    Render the sidebar navigation using Stage 3 components.

    Args:
        current_page: Currently active page ID
        on_navigate: Callback when navigation item is clicked
        collapsed: Whether sidebar is collapsed
        mobile_open: Whether mobile drawer is open
        on_toggle_collapse: Callback for collapse toggle
        on_toggle_mobile: Callback for mobile drawer toggle

    Returns:
        Selected page ID (or current_page if no change)
    """
    obd_status = get_obd_status_details()

    props = SidebarProps(
        nav_items=NAVIGATION_ITEMS,
        current_page=current_page,
        vehicle_info=get_vehicle_info(),
        obd_status={"connected": obd_status.get("connected", False), "text": "Connected" if obd_status.get("connected") else "Disconnected"},
        ai_status=get_ai_status(),
        simulation_status=get_simulation_status(obd_status),
        collapsed=collapsed,
        mobile_open=mobile_open,
        on_navigate=on_navigate,
        on_toggle_collapse=on_toggle_collapse,
        on_toggle_mobile=on_toggle_mobile,
    )

    sidebar(props)
    return st.session_state.get("current_page", current_page)


# =============================================================================
# TOP BAR INTEGRATION
# =============================================================================

def get_breadcrumb_for_page(page_id: str) -> List[tuple[str, str]]:
    """Generate breadcrumb trail for a page."""
    # Map page IDs to breadcrumb paths
    breadcrumb_map = {
        "dashboard": [("i20 AI Garage", "#"), ("Dashboard", "#")],
        "diagnostics": [("i20 AI Garage", "#"), ("Diagnostics", "#")],
        "performance": [("i20 AI Garage", "#"), ("Performance", "#")],
        "maintenance": [("i20 AI Garage", "#"), ("Maintenance", "#")],
        "reports": [("i20 AI Garage", "#"), ("Reports", "#")],
        "vehicle_profile": [("i20 AI Garage", "#"), ("Vehicle Profile", "#")],
        "ai_assistant": [("i20 AI Garage", "#"), ("AI Assistant", "#")],
        "obd_connection": [("i20 AI Garage", "#"), ("OBD Connection", "#")],
        "settings": [("i20 AI Garage", "#"), ("Settings", "#")],
    }
    return breadcrumb_map.get(page_id, [("i20 AI Garage", "#")])


def get_page_title(page_id: str) -> str:
    """Get display title for a page."""
    title_map = {
        "dashboard": "Dashboard",
        "diagnostics": "Diagnostics",
        "performance": "Performance",
        "maintenance": "Maintenance",
        "reports": "Reports",
        "vehicle_profile": "Vehicle Profile",
        "ai_assistant": "AI Assistant",
        "obd_connection": "OBD Connection",
        "settings": "Settings",
    }
    return title_map.get(page_id, page_id.title())


def get_page_icon(page_id: str) -> str:
    """Get icon for a page."""
    icon_map = {
        "dashboard": "🏠",
        "diagnostics": "🔧",
        "performance": "📊",
        "maintenance": "🔩",
        "reports": "📋",
        "vehicle_profile": "🚗",
        "ai_assistant": "🤖",
        "obd_connection": "🔌",
        "settings": "⚙️",
    }
    return icon_map.get(page_id, "📄")


def render_top_bar(
    current_page: str,
    obd_status: Dict[str, Any],
    on_mobile_menu: Optional[Callable] = None,
) -> None:
    """
    Render the top bar with breadcrumbs, page title, and global status.

    Args:
        current_page: Currently active page ID
        obd_status: OBD status details
        on_mobile_menu: Callback for mobile menu toggle
    """
    ai_status = get_ai_status()
    sim_status = get_simulation_status(obd_status)

    props = TopBarProps(
        page_title=get_page_title(current_page),
        breadcrumb=get_breadcrumb_for_page(current_page),
        status_indicators=[
            {"label": "OBD", "status": "success" if obd_status.get("connected") else "critical", "key": "topbar_obd"},
            {"label": sim_status["text"].split(" • ")[0], "status": sim_status["status"], "key": "topbar_sim"},
            {"label": "AI", "status": ai_status["status"], "key": "topbar_ai"},
        ],
        on_mobile_menu=on_mobile_menu,
    )
    top_bar(props)


# =============================================================================
# PAGE HEADER & CONTAINER
# =============================================================================

def render_page_header(
    page_id: str,
    subtitle: str = "",
) -> None:
    """
    Render standardized page header using Stage 3 layout helpers.

    Args:
        page_id: Page identifier
        subtitle: Optional subtitle/description
    """
    page_header(
        title=get_page_title(page_id),
        subtitle=subtitle,
        icon=get_page_icon(page_id),
    )


def page_container(content_fn: Callable[[], None]) -> None:
    """
    Render main content area with consistent container styling.

    Args:
        content_fn: Function that renders the page content
    """
    st.markdown('<div class="i20-page-container">', unsafe_allow_html=True)
    content_fn()
    st.markdown('</div>', unsafe_allow_html=True)


# =============================================================================
# SHELL INITIALIZATION
# =============================================================================

def initialize_shell() -> None:
    """
    Initialize the global application shell.
    Call once at application startup.
    """
    # Inject global stylesheet (Stage 3)
    inject_global_css()

    # Inject layout CSS (Stage 3)
    st.markdown(f"<style>{LAYOUT_CSS}</style>", unsafe_allow_html=True)

    # Initialize session state for shell
    if "sidebar_collapsed" not in st.session_state:
        st.session_state.sidebar_collapsed = False
    if "sidebar_mobile_open" not in st.session_state:
        st.session_state.sidebar_mobile_open = False


# =============================================================================
# MAIN SHELL RENDER FUNCTION
# =============================================================================

@dataclass
class ShellRenderResult:
    """Result of shell rendering."""
    current_page: str
    page_changed: bool


def render_shell(
    current_page: str,
    page_renderers: Dict[str, Callable[[], None]],
    on_navigate: Optional[Callable[[str], None]] = None,
) -> ShellRenderResult:
    """
    Render the complete application shell.

    Args:
        current_page: Current page ID
        page_renderers: Dict mapping page IDs to render functions
        on_navigate: Optional navigation callback

    Returns:
        ShellRenderResult with current page and change flag
    """
    # Initialize shell
    initialize_shell()

    # Inject accessibility HTML elements via st.markdown (renders in component containers)
    st.markdown(render_skip_link("main-content"), unsafe_allow_html=True)
    st.markdown(render_persistent_live_regions(), unsafe_allow_html=True)

    # Inject scripts via st.html with unsafe_allow_javascript=True for execution
    st.html(render_reduced_motion_detection_script(), unsafe_allow_javascript=True)
    st.html(render_landmark_fix_script(), unsafe_allow_javascript=True)

    st.markdown(f"<style>{get_touch_target_css()}</style>", unsafe_allow_html=True)

    # Get OBD status once
    obd_status = get_obd_status_details()

    # Handle mobile menu toggle
    def handle_mobile_menu() -> None:
        st.session_state.sidebar_mobile_open = not st.session_state.get("sidebar_mobile_open", False)

    # Handle sidebar collapse toggle
    def handle_sidebar_toggle() -> None:
        st.session_state.sidebar_collapsed = not st.session_state.get("sidebar_collapsed", False)

    # Render sidebar
    def handle_nav(page: str) -> None:
        if on_navigate:
            on_navigate(page)
        else:
            st.session_state.current_page = page
        # Close mobile drawer on navigation
        st.session_state.sidebar_mobile_open = False

    selected_page = render_sidebar(
        current_page=current_page,
        on_navigate=handle_nav,
        collapsed=st.session_state.get("sidebar_collapsed", False),
        mobile_open=st.session_state.get("sidebar_mobile_open", False),
        on_toggle_collapse=handle_sidebar_toggle,
        on_toggle_mobile=handle_mobile_menu,
    )

    # Check for page change
    page_changed = selected_page != current_page
    if page_changed:
        current_page = selected_page

    # Render top bar
    render_top_bar(current_page, obd_status, on_mobile_menu=handle_mobile_menu)

    # Render page header
    page_subtitles = {
        "dashboard": "Real-time vehicle monitoring & telemetry",
        "diagnostics": "DTC scanning, AI diagnosis & rule engine",
        "performance": "Session analytics, comparison & statistics",
        "maintenance": "Service records, intervals & upcoming reminders",
        "reports": "Professional diagnostic, health & performance reports",
        "vehicle_profile": "Vehicle specifications & configuration",
        "ai_assistant": "Local AI chat & diagnostic assistance",
        "obd_connection": "OBD-II hardware setup & connection wizard",
        "settings": "Application configuration & preferences",
    }

    render_page_header(
        page_id=current_page,
        subtitle=page_subtitles.get(current_page, ""),
    )

    # Render main content container
    st.markdown('<div id="debug-before-renderer" style="color: red;">DEBUG: Before renderer</div>', unsafe_allow_html=True)
    renderer = page_renderers.get(current_page)
    if renderer:
        try:
            renderer()
            st.markdown('<div id="debug-renderer-success" style="color: green;">DEBUG: Renderer returned successfully</div>', unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f'<div id="debug-renderer-error" style="color: red;">DEBUG: Renderer error: {e}</div>', unsafe_allow_html=True)
            st.error(f"Renderer error: {e}")
    else:
        st.error(f"Unknown page: {current_page}")
    st.markdown('<div id="debug-after-renderer" style="color: red;">DEBUG: After renderer</div>', unsafe_allow_html=True)

    # Debug: check if we reach here
    st.markdown('<div id="debug-before-footer" style="color: red;">DEBUG: Before footer render</div>', unsafe_allow_html=True)

    # Render footer with contentinfo landmark AFTER page content (at bottom of page)
    st.markdown(render_footer(), unsafe_allow_html=True)

    # Debug: check if footer rendered
    st.markdown('<div id="debug-after-footer" style="color: red;">DEBUG: After footer render</div>', unsafe_allow_html=True)

    return ShellRenderResult(current_page=current_page, page_changed=page_changed)
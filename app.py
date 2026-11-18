"""
i20 AI Garage - Main Application Entry Point

Streamlit application for Hyundai i20 Asta 2023 diagnostic and monitoring.
Run with: streamlit run app.py
"""

import streamlit as st
import time
from datetime import datetime

# Page configuration - must be first Streamlit command
st.set_page_config(
    page_title="i20 AI Garage",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/your-repo/i20-ai-garage",
        "Report a bug": "https://github.com/your-repo/i20-ai-garage/issues",
        "About": "i20 AI Garage - Professional Automotive Diagnostic Platform for Hyundai i20 Asta 2023",
    }
)

# Import configuration
from config import VEHICLE_INFO, SIMULATION_SCENARIOS, THEME
from services import get_database, get_ai_service, get_obd_service

# Import page render functions
from modules.dashboard import render_dashboard, update_telemetry_history as update_dashboard_telemetry
from modules.diagnostics import render_diagnostics
from modules.performance import render_performance
from modules.maintenance import render_maintenance
from modules.vehicle_profile import render_vehicle_profile
from modules.ai_assistant import render_ai_assistant
from modules.obd_connection import render_connection_wizard
from modules.reports import render_reports_page

# Import shell components
from components.shell import (
    render_shell,
    NAVIGATION_ITEMS,
    get_obd_status_details,
    get_ai_status,
    get_simulation_status,
)


def initialize_session_state():
    """Initialize global session state variables."""
    # Navigation state
    if "current_page" not in st.session_state:
        st.session_state.current_page = "dashboard"

    # Simulation state (shared across pages)
    if "sim_running" not in st.session_state:
        st.session_state.sim_running = False
    if "sim_scenario" not in st.session_state:
        st.session_state.sim_scenario = "idle"
    if "telemetry_history" not in st.session_state:
        st.session_state.telemetry_history = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "last_update" not in st.session_state:
        st.session_state.last_update = time.time()

    # OBD/AI connection state
    if "obd_connected" not in st.session_state:
        st.session_state.obd_connected = False
    if "ai_connected" not in st.session_state:
        st.session_state.ai_connected = False

    # Initialize services
    if "services_initialized" not in st.session_state:
        st.session_state.services_initialized = False


def initialize_services():
    """Initialize all backend services on startup."""
    if not st.session_state.services_initialized:
        try:
            # Initialize database
            db = get_database()
            # Initialize AI service
            ai_service = get_ai_service()
            # Initialize OBD service
            obd_service = get_obd_service()

            # Check AI connection
            st.session_state.ai_connected = ai_service.is_available()

            # Check OBD connection
            obd_status = obd_service.get_status()
            st.session_state.obd_connected = obd_status["connection_state"] == "connected"

            st.session_state.services_initialized = True
        except Exception as e:
            st.error(f"Failed to initialize services: {e}")


def handle_navigation(page_id: str):
    """Handle navigation callback from shell."""
    st.session_state.current_page = page_id
    st.rerun()


def auto_update_telemetry():
    """Auto-update telemetry history when simulation is running."""
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


def render_settings():
    """Render the Settings page."""
    from config import (
        OBD_MODE, OBD_PORT, OBD_BAUDRATE, OBD_PROTOCOL,
        LM_STUDIO_BASE_URL, LM_STUDIO_MODEL, LM_STUDIO_TEMPERATURE, LM_STUDIO_TIMEOUT,
        SIMULATION_INTERVAL, TELEMETRY_REFRESH_INTERVAL,
        VEHICLE_INFO
    )
    from services import get_ai_service, get_obd_service

    st.markdown("""
    <div class="custom-card">
        <h2 style="margin-top: 0; color: var(--accent-blue);">⚙️ Settings</h2>
        <p style="color: var(--text-secondary);">Configure application preferences, connections, and simulation parameters.</p>
    </div>
    """, unsafe_allow_html=True)

    ai_service = get_ai_service()
    obd_service = get_obd_service()

    # OBD Settings
    with st.expander("🔌 OBD-II Connection Settings", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            obd_mode = st.selectbox(
                "OBD Mode",
                options=["simulation", "real"],
                index=0 if OBD_MODE == "simulation" else 1,
                help="Simulation mode generates demo data. Real mode connects to actual OBD-II adapter."
            )

            obd_port = st.text_input(
                "Serial Port",
                value=OBD_PORT,
                help="Serial port for OBD-II adapter (e.g., COM3 on Windows, /dev/ttyUSB0 on Linux)"
            )

        with col2:
            obd_baudrate = st.selectbox(
                "Baud Rate",
                options=[9600, 38400, 57600, 115200],
                index=[9600, 38400, 57600, 115200].index(OBD_BAUDRATE),
                help="Communication speed for OBD-II adapter"
            )

            obd_protocol = st.selectbox(
                "Protocol",
                options=["auto", "SAE J1850 PWM", "SAE J1850 VPW", "ISO 9141-2", "ISO 14230-4 (KWP 5baud)", "ISO 14230-4 (KWP fast)", "ISO 15765-4 (CAN 11bit/500k)", "ISO 15765-4 (CAN 29bit/500k)", "ISO 15765-4 (CAN 11bit/250k)", "ISO 15765-4 (CAN 29bit/250k)"],
                index=0,
                help="OBD-II communication protocol (auto-detect recommended)"
            )

        # Connection test
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("🔍 Test Connection", use_container_width=True):
                with st.spinner("Testing OBD connection..."):
                    result = obd_service.connect(obd_port, obd_baudrate, obd_protocol)
                    if result:
                        st.success("✅ OBD connection successful!")
                        st.session_state.obd_connected = True
                    else:
                        st.error("❌ OBD connection failed")
                        st.session_state.obd_connected = False
        with col2:
            if st.button("🔌 Disconnect", use_container_width=True):
                obd_service.disconnect()
                st.session_state.obd_connected = False
                st.success("Disconnected from OBD")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # AI Assistant Settings
    with st.expander("🤖 AI Assistant Settings", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            lm_studio_url = st.text_input(
                "LM Studio Base URL",
                value=LM_STUDIO_BASE_URL,
                help="Base URL for LM Studio OpenAI-compatible API server"
            )

            lm_studio_model = st.text_input(
                "Model Name",
                value=LM_STUDIO_MODEL,
                help="Name of the loaded model in LM Studio"
            )

        with col2:
            lm_studio_temp = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=LM_STUDIO_TEMPERATURE,
                step=0.1,
                help="Controls randomness in AI responses (0 = deterministic, 1 = creative)"
            )

            lm_studio_timeout = st.number_input(
                "Timeout (seconds)",
                min_value=5,
                max_value=120,
                value=LM_STUDIO_TIMEOUT,
                help="Request timeout for AI service"
            )

        # AI connection test
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("🔍 Test AI Connection", use_container_width=True):
                with st.spinner("Testing AI connection..."):
                    ai_service.base_url = lm_studio_url
                    ai_service.model = lm_studio_model
                    ai_service.temperature = lm_studio_temp
                    ai_service.timeout = lm_studio_timeout
                    result = ai_service.is_available()
                    if result:
                        st.success("✅ AI connection successful!")
                        st.session_state.ai_connected = True
                    else:
                        st.error("❌ AI connection failed - check LM Studio is running")
                        st.session_state.ai_connected = False

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Simulation Settings
    with st.expander("⚡ Simulation Settings", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            sim_interval = st.number_input(
                "Simulation Update Interval (seconds)",
                min_value=0.1,
                max_value=5.0,
                value=SIMULATION_INTERVAL,
                step=0.1,
                format="%.1f",
                help="How often simulation generates new data points"
            )

            telemetry_refresh = st.number_input(
                "Telemetry Refresh Interval (seconds)",
                min_value=0.5,
                max_value=10.0,
                value=TELEMETRY_REFRESH_INTERVAL,
                step=0.5,
                format="%.1f",
                help="How often UI refreshes telemetry display"
            )

        with col2:
            st.markdown("**Available Scenarios:**")
            for key, scenario in SIMULATION_SCENARIOS.items():
                st.caption(f"• **{scenario['name']}**: {scenario['description']}")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Vehicle Information (Read-only)
    with st.expander("🚗 Vehicle Profile", expanded=False):
        st.markdown("**Current Vehicle Configuration:**")
        col1, col2 = st.columns(2)
        with col1:
            for key, value in VEHICLE_INFO.items():
                if key != "vin":
                    st.text_input(key.replace("_", " ").title(), value=value, disabled=True)
        with col2:
            st.text_input("VIN", value=VEHICLE_INFO["vin"], disabled=True)
            st.caption("VIN is for display purposes only (demo pattern)")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Data Management
    with st.expander("💾 Data Management", expanded=False):
        db = get_database()

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📊 Export All Data", use_container_width=True):
                st.info("Export functionality coming soon")
        with col2:
            if st.button("🗑️ Clear Telemetry History", use_container_width=True):
                st.session_state.telemetry_history = []
                st.success("Telemetry history cleared")
        with col3:
            if st.button("🔄 Reset All Settings", use_container_width=True):
                st.warning("This will reset all settings to defaults")
                if st.button("⚠️ Confirm Reset", type="primary"):
                    st.success("Settings reset to defaults (restart required)")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # About / Version
    with st.expander("ℹ️ About", expanded=False):
        st.markdown(f"""
        **i20 AI Garage v1.0.0**

        Professional automotive diagnostic platform for the 2023 Hyundai i20 Asta
        1.2L Naturally Aspirated Petrol Manual (India market).

        **Features:**
        - Real-time OBD-II telemetry monitoring
        - DTC scanning and diagnostics
        - Performance analytics and session recording
        - Maintenance tracking and reminders
        - AI-powered diagnostic assistant (LM Studio)
        - Simulation mode for demonstration

        **Technology Stack:**
        - Streamlit (UI Framework)
        - Plotly (Visualizations)
        - python-OBD (OBD-II Communication)
        - LM Studio (Local AI Inference)
        - SQLite (Data Persistence)

        **Disclaimer:** This software is for educational and diagnostic assistance purposes only.
        Always consult a qualified mechanic for vehicle repairs. Simulation data is not real vehicle data.
        """)


def main():
    """Main application entry point."""
    # Initialize session state
    initialize_session_state()

    # Initialize services
    initialize_services()

    # Auto-update telemetry when simulation is running
    auto_update_telemetry()

    # Get current page from session state
    current_page = st.session_state.get("current_page", "dashboard")

    # Get OBD status for top bar
    obd_status = get_obd_status_details()

    # Page renderers dict
    page_renderers = {
        "dashboard": render_dashboard,
        "diagnostics": render_diagnostics,
        "performance": render_performance,
        "maintenance": render_maintenance,
        "reports": render_reports_page,
        "vehicle_profile": render_vehicle_profile,
        "ai_assistant": render_ai_assistant,
        "obd_connection": render_connection_wizard,
        "settings": render_settings,
    }

    # Render the complete shell
    result = render_shell(
        current_page=current_page,
        page_renderers=page_renderers,
        on_navigate=handle_navigation,
    )


if __name__ == "__main__":
    main()
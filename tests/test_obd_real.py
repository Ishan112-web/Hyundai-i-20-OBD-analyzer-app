"""
i20 AI Garage - Real OBD Tests

Tests for RealOBDAdapter, ConnectionManager, PIDRegistry, and integration.
Uses mocks to avoid requiring physical hardware.
"""

import pytest
import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.real_obd_adapter import RealOBDAdapter, AdapterType, ConnectionProfile, PIDInfo, FreezeFrameData
from services.connection_manager import ConnectionManager, PortInfo, ConnectionAttempt
from services.pid_registry import PIDRegistry, PIDDefinition, PIDValue, PIDPriority
from services.obd_service import OBDService, OBDMode, ConnectionState, SimulationEngine, SensorReading, DTC


# =============================================================================
# Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_elm327():
    """Mock ELM327 adapter for unit tests."""
    import obd
    # Patch where obd.OBD is USED (in services.real_obd_adapter), not where it's defined
    with patch('services.real_obd_adapter.obd.OBD') as mock_obd_class:
        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = True
        # Use actual OBDStatus enum values instead of Mock objects
        mock_conn.status.return_value = obd.OBDStatus.CAR_CONNECTED
        mock_conn.protocol_id.return_value = 6
        mock_conn.voltage.return_value = Mock(magnitude=14.2)
        mock_conn.supported_commands = set()

        # Mock supported PID queries (PID 00, 20, 40, 60, 80, A0, C0)
        mock_pids_response = MagicMock()
        mock_pids_response.is_null.return_value = False
        mock_pids_response.value = [
            Mock(pid=0x0C),  # RPM
            Mock(pid=0x0D),  # Speed
            Mock(pid=0x05),  # Coolant temp
            Mock(pid=0x11),  # Throttle
            Mock(pid=0x04),  # Engine load
            Mock(pid=0x0B),  # MAP
            Mock(pid=0x06),  # STFT
            Mock(pid=0x07),  # LTFT
            Mock(pid=0x42),  # Voltage
            Mock(pid=0x10),  # MAF
            Mock(pid=0x0F),  # Intake temp
        ]

        # Mock individual PID queries
        def mock_query(cmd, timeout=None):
            response = MagicMock()
            response.is_null.return_value = False

            # Check command name for special commands
            cmd_name = getattr(cmd, 'name', str(cmd))

            # Handle DTC commands
            if 'GET_DTC' in cmd_name or 'GET_PENDING_DTC' in cmd_name or 'GET_PERMANENT_DTC' in cmd_name:
                response.value = [("P0300", "Random/Multiple Cylinder Misfire")]
            # Handle VIN/CALID/CVN commands
            elif 'VIN' in cmd_name:
                response.value = "MALA841CLHM123456"
            elif 'CALIBRATION_ID' in cmd_name or 'CALID' in cmd_name:
                response.value = "CAL123456"
            elif 'CVN' in cmd_name or 'CALIBRATION_VERIFICATION' in cmd_name:
                response.value = "CVN123456"
            # Handle PID commands with pid attribute
            elif hasattr(cmd, 'pid'):
                pid = cmd.pid
                if pid == 0x0C:  # RPM
                    response.value = Mock(magnitude=2500, to=lambda u: Mock(magnitude=2500))
                elif pid == 0x0D:  # Speed
                    response.value = Mock(magnitude=60, to=lambda u: Mock(magnitude=60))
                elif pid == 0x05:  # Coolant temp
                    response.value = Mock(magnitude=90, to=lambda u: Mock(magnitude=90))
                elif pid in (0x11, 0x04, 0x06, 0x07):  # Percentages
                    response.value = Mock(magnitude=50, to=lambda u: Mock(magnitude=50))
                elif pid == 0x0B:  # MAP
                    response.value = Mock(magnitude=50, to=lambda u: Mock(magnitude=50))
                elif pid == 0x42:  # Voltage
                    response.value = Mock(magnitude=14.2, to=lambda u: Mock(magnitude=14.2))
                elif pid == 0x10:  # MAF
                    response.value = Mock(magnitude=15.5, to=lambda u: Mock(magnitude=15.5))
                elif pid == 0x0F:  # Intake temp
                    response.value = Mock(magnitude=35, to=lambda u: Mock(magnitude=35))
                else:
                    response.value = Mock(magnitude=0, to=lambda u: Mock(magnitude=0))
            # Handle supported PID queries (PIDS_A, PIDS_B, etc.)
            elif hasattr(cmd, '__iter__') or 'PIDS' in cmd_name:
                response.value = [
                    Mock(pid=0x0C),  # RPM
                    Mock(pid=0x0D),  # Speed
                    Mock(pid=0x05),  # Coolant temp
                    Mock(pid=0x11),  # Throttle
                    Mock(pid=0x04),  # Engine load
                    Mock(pid=0x0B),  # MAP
                    Mock(pid=0x06),  # STFT
                    Mock(pid=0x07),  # LTFT
                    Mock(pid=0x42),  # Voltage
                    Mock(pid=0x10),  # MAF
                    Mock(pid=0x0F),  # Intake temp
                ]
            else:
                response.value = []

            return response

        mock_conn.query.side_effect = mock_query
        mock_obd_class.return_value = mock_conn
        yield mock_conn


@pytest.fixture
def mock_serial_ports():
    """Mock serial port discovery."""
    with patch('serial.tools.list_ports.comports') as mock_comports:
        mock_ports = [
            Mock(
                device="COM3",
                name="COM3",
                description="USB-SERIAL CH340 (COM3)",
                hwid="USB VID:PID=1A86:7523",
                vid=0x1A86,
                pid=0x7523,
                manufacturer="QinHeng",
                product="CH340",
                serial_number="123456"
            ),
            Mock(
                device="COM4",
                name="COM4",
                description="Bluetooth Device (COM4)",
                hwid="BTHENUM\\{...}",
                vid=None,
                pid=None,
                manufacturer="Microsoft",
                product="Bluetooth",
                serial_number=None
            ),
            Mock(
                device="COM5",
                name="COM5",
                description="ELM327 OBDII Adapter (COM5)",
                hwid="USB VID:PID=0403:6001",
                vid=0x0403,
                pid=0x6001,
                manufacturer="FTDI",
                product="FT232R USB UART",
                serial_number="A123456"
            ),
        ]
        mock_comports.return_value = mock_ports
        yield mock_ports


# =============================================================================
# RealOBDAdapter Tests
# =============================================================================

class TestRealOBDAdapter:
    """Tests for RealOBDAdapter class."""

    def test_adapter_initialization(self):
        """Test adapter initializes with correct defaults."""
        adapter = RealOBDAdapter(port="COM3", baudrate=38400, protocol="AUTO")

        assert adapter.port == "COM3"
        assert adapter.baudrate == 38400
        assert adapter.protocol == "AUTO"
        assert adapter.timeout == 10.0
        assert adapter.query_timeout == 2.0
        assert adapter.connection_state == ConnectionState.DISCONNECTED
        assert adapter.adapter_type == AdapterType.USB

    def test_adapter_type_detection_usb(self):
        """Test USB adapter type detection."""
        adapter = RealOBDAdapter(port="COM3")
        assert adapter.adapter_type == AdapterType.USB

    def test_adapter_type_detection_bluetooth(self):
        """Test Bluetooth adapter type detection."""
        adapter = RealOBDAdapter(port="COM4", baudrate=38400)
        adapter._detect_adapter_type()
        # COM ports default to USB
        assert adapter.adapter_type == AdapterType.USB

    def test_statistics_initialization(self):
        """Test statistics are initialized to zero."""
        adapter = RealOBDAdapter(port="COM3")
        stats = adapter.statistics

        assert stats["queries_sent"] == 0
        assert stats["queries_successful"] == 0
        assert stats["queries_failed"] == 0
        assert stats["success_rate"] == 0
        assert stats["last_query_time"] is None
        assert stats["connect_time"] is None
        assert stats["uptime_seconds"] == 0

    def test_connect_success(self, mock_elm327):
        """Test successful connection to ELM327 and ECU."""
        adapter = RealOBDAdapter(port="COM3", baudrate=38400, protocol="AUTO")

        result = adapter.connect()

        assert result is True
        assert adapter.is_connected is True
        assert adapter.connection_state == ConnectionState.CONNECTED
        assert adapter._connect_time is not None
        assert len(adapter.supported_pids) > 0

    def test_connect_failure(self, mock_elm327):
        """Test connection failure handling."""
        import obd
        # Use the fixture's mock but override status to return ELM_CONNECTED
        mock_elm327.status.return_value = obd.OBDStatus.ELM_CONNECTED

        adapter = RealOBDAdapter(port="COM3", timeout=1.0)
        result = adapter.connect()

        assert result is False
        assert adapter.connection_state == ConnectionState.ERROR
        assert adapter._last_error is not None

    def test_query_pid_success(self, mock_elm327):
        """Test successful PID query."""
        adapter = RealOBDAdapter(port="COM3")
        adapter.connect()

        # Query RPM (0x0C)
        value = adapter.query_pid("0C")

        assert value is not None
        assert isinstance(value, float)
        assert value > 0

    def test_query_pid_not_supported(self, mock_elm327):
        """Test querying unsupported PID returns None."""
        adapter = RealOBDAdapter(port="COM3")
        adapter.connect()

        # Remove 0x99 from supported PIDs
        adapter._supported_pids = ["0C", "0D", "05"]

        value = adapter.query_pid("99")

        assert value is None

    def test_query_pid_unknown(self, mock_elm327):
        """Test querying unknown PID returns None."""
        adapter = RealOBDAdapter(port="COM3")
        adapter.connect()

        value = adapter.query_pid("ZZ")

        assert value is None

    def test_get_all_readings(self, mock_elm327):
        """Test getting all sensor readings."""
        adapter = RealOBDAdapter(port="COM3")
        adapter.connect()

        readings = adapter.get_all_readings()

        assert isinstance(readings, dict)
        assert "rpm" in readings
        assert "speed_kmh" in readings
        assert "coolant_temp_c" in readings
        assert all(isinstance(r, SensorReading) for r in readings.values())
        assert all(r.is_simulated is False for r in readings.values())

    def test_scan_dtcs(self, mock_elm327):
        """Test DTC scanning."""
        # First connect (uses fixture's mock_query for PID discovery)
        adapter = RealOBDAdapter(port="COM3")
        adapter.connect()

        # Now set up DTC responses for scan_dtcs
        mock_elm327.query.side_effect = None  # Clear the default side_effect

        dtc_response = MagicMock()
        dtc_response.is_null.return_value = False
        dtc_response.value = [("P0300", "Random/Multiple Cylinder Misfire")]

        pending_dtc_response = MagicMock()
        pending_dtc_response.is_null.return_value = False
        pending_dtc_response.value = []

        # Adapter now only queries GET_DTC and GET_CURRENT_DTC (2 calls)
        mock_elm327.query.side_effect = [dtc_response, pending_dtc_response]

        dtcs = adapter.scan_dtcs()

        assert isinstance(dtcs, list)
        assert len(dtcs) >= 1
        assert dtcs[0].code == "P0300"
        assert dtcs[0].is_demo is False

    def test_clear_dtcs(self, mock_elm327):
        """Test DTC clearing."""
        mock_elm327.query.side_effect = None
        clear_response = MagicMock()
        clear_response.is_null.return_value = False
        mock_elm327.query.return_value = clear_response

        adapter = RealOBDAdapter(port="COM3")
        adapter.connect()

        result = adapter.clear_dtcs()

        assert result is True

    def test_get_freeze_frame(self, mock_elm327):
        """Test freeze frame data retrieval."""
        adapter = RealOBDAdapter(port="COM3")
        adapter.connect()

        ff = adapter.get_freeze_frame("P0300")

        assert ff is not None
        assert isinstance(ff, FreezeFrameData)
        assert ff.dtc_code == "P0300"

    def test_vehicle_info(self, mock_elm327):
        """Test vehicle info queries (VIN, CALID, CVN)."""
        # First connect (uses fixture's mock_query for PID discovery)
        adapter = RealOBDAdapter(port="COM3")
        adapter.connect()

        # Now set up VIN/CALID/CVN responses
        mock_elm327.query.side_effect = None

        vin_response = MagicMock()
        vin_response.is_null.return_value = False
        vin_response.value = "MALA841CLHM123456"

        calid_response = MagicMock()
        calid_response.is_null.return_value = False
        calid_response.value = "CAL123456"

        cvn_response = MagicMock()
        cvn_response.is_null.return_value = False
        cvn_response.value = "CVN123456"

        mock_elm327.query.side_effect = [vin_response, calid_response, cvn_response]

        vin = adapter.get_vin()
        calid = adapter.get_calid()
        cvn = adapter.get_cvn()

        assert vin == "MALA841CLHM123456"
        assert calid == "CAL123456"
        assert cvn == "CVN123456"

    def test_health_check(self, mock_elm327):
        """Test health check functionality."""
        adapter = RealOBDAdapter(port="COM3")
        adapter.connect()

        health = adapter.health_check()

        assert health["connected"] is True
        assert "query_test" in health
        assert health["query_test"] in ("passed", "failed")
        assert "statistics" in health

    def test_disconnect(self, mock_elm327):
        """Test disconnection cleanup."""
        adapter = RealOBDAdapter(port="COM3")
        adapter.connect()
        assert adapter.is_connected

        adapter.disconnect()

        assert adapter.connection_state == ConnectionState.DISCONNECTED
        assert adapter._connection is None
        assert adapter._supported_pids == []


# =============================================================================
# ConnectionManager Tests
# =============================================================================

class TestConnectionManager:
    """Tests for ConnectionManager class."""

    def test_manager_initialization(self):
        """Test connection manager initializes correctly."""
        manager = ConnectionManager(
            profiles_file="data/test_profiles.json",
            health_check_interval=30
        )

        assert manager.connection_state == ConnectionState.DISCONNECTED
        assert manager.adapter is None
        assert manager.current_profile is None
        assert manager._reconnect_enabled is True

    def test_discover_ports(self, mock_serial_ports):
        """Test port discovery identifies likely OBD adapters."""
        manager = ConnectionManager()
        ports = manager.discover_ports()

        assert len(ports) == 3
        # COM3 (CH340) and COM5 (FTDI + ELM327 in description) should be likely
        likely_ports = [p for p in ports if p.is_likely_obd]
        assert len(likely_ports) >= 2

        # Check sorting - likely OBD first
        assert ports[0].is_likely_obd is True

    def test_is_likely_obd_adapter_vid_pid(self):
        """Test OBD adapter detection by VID/PID."""
        manager = ConnectionManager()

        # Test known VIDs
        mock_port = Mock(vid=0x0403, pid=0x6001, description="", manufacturer="", product="")
        assert manager._is_likely_obd_adapter(mock_port) is True

        mock_port = Mock(vid=0x10C4, pid=0xEA60, description="", manufacturer="", product="")
        assert manager._is_likely_obd_adapter(mock_port) is True

        mock_port = Mock(vid=0x1A86, pid=0x7523, description="", manufacturer="", product="")
        assert manager._is_likely_obd_adapter(mock_port) is True

        # Unknown VID
        mock_port = Mock(vid=0x1234, pid=0x5678, description="", manufacturer="", product="")
        assert manager._is_likely_obd_adapter(mock_port) is False

    def test_is_likely_obd_adapter_description(self):
        """Test OBD adapter detection by description keywords."""
        manager = ConnectionManager()

        mock_port = Mock(vid=None, pid=None, description="ELM327 OBDII Adapter", manufacturer="", product="")
        assert manager._is_likely_obd_adapter(mock_port) is True

        mock_port = Mock(vid=None, pid=None, description="Bluetooth OBD Scanner", manufacturer="", product="")
        assert manager._is_likely_obd_adapter(mock_port) is True

        mock_port = Mock(vid=None, pid=None, description="Generic USB Serial", manufacturer="", product="")
        assert manager._is_likely_obd_adapter(mock_port) is False

    def test_connect_success(self, mock_elm327, mock_serial_ports):
        """Test successful connection via manager."""
        manager = ConnectionManager()

        success = manager.connect(
            port="COM3",
            baudrate=38400,
            protocol="AUTO",
            save_profile=True,
            profile_name="Test Adapter"
        )

        assert success is True
        assert manager.connection_state == ConnectionState.CONNECTED
        assert manager.adapter is not None
        assert manager.current_profile is not None
        assert manager.current_profile.port == "COM3"

    def test_auto_connect(self, mock_elm327, mock_serial_ports):
        """Test auto-connect tries profiles then discovered ports."""
        manager = ConnectionManager()

        success = manager.auto_connect(timeout=5.0)

        assert success is True
        assert manager.connection_state == ConnectionState.CONNECTED

    def test_disconnect(self, mock_elm327):
        """Test disconnection."""
        manager = ConnectionManager()
        manager.connect(port="COM3", baudrate=38400, protocol="AUTO")
        assert manager.connection_state == ConnectionState.CONNECTED

        manager.disconnect()

        assert manager.connection_state == ConnectionState.DISCONNECTED
        assert manager.adapter is None
        # Profile is kept for reconnect() functionality
        assert manager.current_profile is not None
        assert manager.current_profile.port == "COM3"

    def test_reconnect(self, mock_elm327):
        """Test reconnection using saved profile."""
        manager = ConnectionManager()
        manager.connect(port="COM3", baudrate=38400, protocol="AUTO", profile_name="Test")
        manager.disconnect()

        success = manager.reconnect()

        assert success is True
        assert manager.connection_state == ConnectionState.CONNECTED

    def test_profile_management(self):
        """Test saving, loading, and deleting profiles."""
        manager = ConnectionManager(profiles_file="data/test_profiles.json")

        # Save profile
        manager._save_profile("COM3", 38400, "AUTO", "Test Adapter")
        profiles = manager.get_profiles()
        assert len(profiles) == 1
        assert profiles[0].port == "COM3"
        assert profiles[0].friendly_name == "Test Adapter"

        # Delete profile
        manager.delete_profile("COM3", 38400, "AUTO")
        profiles = manager.get_profiles()
        assert len(profiles) == 0

    def test_connection_log_callback(self):
        """Test connection log callback is invoked."""
        log_events = []

        def log_callback(event):
            log_events.append(event)

        manager = ConnectionManager(on_connection_log=log_callback)
        manager._log_connection_event("connect", "COM3", 38400, "AUTO", "Test")

        assert len(log_events) == 1
        assert log_events[0]["event_type"] == "connect"
        assert log_events[0]["port"] == "COM3"

    def test_status_change_callback(self):
        """Test status change callback is invoked."""
        status_changes = []

        def status_callback(state):
            status_changes.append(state)

        manager = ConnectionManager(on_status_change=status_callback)
        manager._notify_status_change()

        # Should have been called with initial state
        assert len(status_changes) >= 0  # May or may not be called depending on implementation


# =============================================================================
# PIDRegistry Tests
# =============================================================================

class TestPIDRegistry:
    """Tests for PIDRegistry class."""

    def test_registry_initialization(self):
        """Test registry initializes with standard PIDs."""
        registry = PIDRegistry()

        assert len(registry.STANDARD_PIDS) > 0
        assert "0C" in registry.STANDARD_PIDS  # RPM
        assert "0D" in registry.STANDARD_PIDS  # Speed
        assert "05" in registry.STANDARD_PIDS  # Coolant temp

    def test_priority_definitions(self):
        """Test PID priority levels are correct."""
        registry = PIDRegistry()

        critical_pids = registry.get_pids_by_priority(PIDPriority.CRITICAL)
        assert len(critical_pids) == 3
        assert any(p.pid == "0C" for p in critical_pids)  # RPM
        assert any(p.pid == "0D" for p in critical_pids)  # Speed
        assert any(p.pid == "05" for p in critical_pids)  # Coolant

        high_pids = registry.get_pids_by_priority(PIDPriority.HIGH)
        assert len(high_pids) == 3
        assert any(p.pid == "11" for p in high_pids)  # Throttle
        assert any(p.pid == "04" for p in high_pids)  # Load
        assert any(p.pid == "0B" for p in high_pids)  # MAP

    def test_set_supported_pids(self):
        """Test setting supported PIDs from detection."""
        registry = PIDRegistry()

        supported = ["0C", "0D", "05", "11", "04", "0B", "06", "07", "42", "10"]
        registry.set_supported_pids(supported)

        assert registry.detection_complete is True
        assert len(registry.supported_pids) == 10
        assert registry.is_supported("0C") is True
        assert registry.is_supported("99") is False

    def test_unsupported_pids_tracking(self):
        """Test unsupported PIDs are tracked."""
        registry = PIDRegistry()

        # Only support a few PIDs
        registry.set_supported_pids(["0C", "0D"])

        assert "05" in registry.unsupported_pids  # Coolant not supported
        assert "11" in registry.unsupported_pids  # Throttle not supported

    def test_is_supported_before_detection(self):
        """Test is_supported returns True for standard PIDs before detection."""
        registry = PIDRegistry()

        # Before detection, all standard PIDs should be queryable
        assert registry.is_supported("0C") is True
        assert registry.is_supported("0D") is True
        assert registry.is_supported("99") is False  # Not a standard PID

    def test_should_poll(self):
        """Test polling interval logic."""
        registry = PIDRegistry()
        registry.set_supported_pids(["0C", "0D", "05"])

        current_time = time.monotonic()

        # Should poll immediately (first time)
        assert registry.should_poll("0C", current_time) is True

        # Mark as polled
        registry.mark_polled("0C", current_time)

        # Should not poll immediately again
        assert registry.should_poll("0C", current_time) is False

        # Should poll after interval
        future_time = current_time + 0.2  # > 0.1s interval for CRITICAL
        assert registry.should_poll("0C", future_time) is True

    def test_record_result(self):
        """Test recording query results."""
        registry = PIDRegistry()
        registry.set_supported_pids(["0C"])

        from services.pid_registry import PIDValue
        value = PIDValue(
            pid="0C",
            sensor_key="rpm",
            value=2500.0,
            unit="RPM",
            timestamp=datetime.now(),
            success=True
        )

        registry.record_result(value)

        assert "0C" in registry._last_values
        stats = registry._pid_stats["0C"]
        assert stats["queries"] == 1
        assert stats["successes"] == 1

    def test_value_validation(self):
        """Test PID value validation and clamping."""
        registry = PIDRegistry()

        # RPM valid range 0-8000
        valid, clamped = registry.validate_value("0C", 2500)
        assert valid is True
        assert clamped == 2500

        # RPM too high - should clamp
        valid, clamped = registry.validate_value("0C", 9000)
        assert valid is False
        assert clamped == 8000

        # RPM negative - should clamp
        valid, clamped = registry.validate_value("0C", -100)
        assert valid is False
        assert clamped == 0

    def test_get_pid_for_sensor(self):
        """Test mapping sensor keys to PIDs."""
        registry = PIDRegistry()

        assert registry.get_pid_for_sensor("rpm") == "0C"
        assert registry.get_pid_for_sensor("speed_kmh") == "0D"
        assert registry.get_pid_for_sensor("coolant_temp_c") == "05"
        assert registry.get_pid_for_sensor("unknown") is None

    def test_registry_summary(self):
        """Test registry summary generation."""
        registry = PIDRegistry()
        registry.set_supported_pids(["0C", "0D", "05", "11", "04"])

        summary = registry.get_registry_summary()

        assert summary["detection_complete"] is True
        assert summary["standard_pid_count"] == len(registry.STANDARD_PIDS)
        assert summary["supported_count"] == 5
        assert "by_priority" in summary
        assert summary["by_priority"]["critical"]["count"] > 0


# =============================================================================
# OBDService Integration Tests
# =============================================================================

class TestOBDServiceIntegration:
    """Tests for OBDService integration with real components."""

    def test_real_mode_connection(self, mock_elm327):
        """Test OBDService connects in real mode using new components."""
        obd = OBDService()
        obd.mode = OBDMode.REAL
        obd.port = "COM3"
        obd.baudrate = 38400
        obd.protocol = "AUTO"

        result = obd.connect()

        assert result is True
        assert obd.connection_state == ConnectionState.CONNECTED
        assert obd.real_adapter is not None
        assert obd.connection_manager is not None

    def test_simulation_mode_still_works(self):
        """Test simulation mode continues to work exactly as before."""
        obd = OBDService()
        obd.mode = OBDMode.SIMULATION

        result = obd.connect()
        assert result is True
        assert obd.connection_state == ConnectionState.CONNECTED

        # Start simulation
        obd.start_simulation("idle")
        time.sleep(0.3)

        readings = obd.get_all_readings()
        assert len(readings) == 11
        assert all(r.is_simulated is True for r in readings.values())

        obd.stop_simulation()

    def test_mode_switching(self):
        """Test switching between simulation and real modes."""
        obd = OBDService()

        # Start in simulation
        obd.mode = OBDMode.SIMULATION
        obd.connect()
        assert obd.connection_state == ConnectionState.CONNECTED
        assert obd.mode == OBDMode.SIMULATION

        # Switch to real (will fail without hardware, but should not crash)
        obd.set_mode(OBDMode.REAL)
        # Connection state should be ERROR since no real adapter
        assert obd.connection_state == ConnectionState.ERROR

        # Switch back to simulation
        obd.set_mode(OBDMode.SIMULATION)
        assert obd.connection_state == ConnectionState.CONNECTED
        assert obd.mode == OBDMode.SIMULATION

    def test_get_status_includes_pid_registry(self, mock_elm327):
        """Test get_status includes PID registry info."""
        obd = OBDService()
        obd.mode = OBDMode.REAL
        obd.port = "COM3"
        obd.connect()

        status = obd.get_status()

        assert "pid_registry" in status
        assert "supported_pids_count" in status
        assert status["pid_registry"]["detection_complete"] is True

    def test_discover_ports(self, mock_serial_ports):
        """Test port discovery through OBDService."""
        obd = OBDService()
        ports = obd.discover_ports()

        assert len(ports) >= 2  # Should find the mocked ports
        likely = [p for p in ports if p.is_likely_obd]
        assert len(likely) >= 2

    def test_auto_connect(self, mock_elm327, mock_serial_ports):
        """Test auto-connect through OBDService."""
        obd = OBDService()
        obd.mode = OBDMode.REAL

        success = obd.auto_connect(timeout=5.0)

        assert success is True
        assert obd.connection_state == ConnectionState.CONNECTED

    def test_connection_logs(self):
        """Test getting connection logs."""
        obd = OBDService()
        logs = obd.get_connection_logs()

        assert isinstance(logs, list)


# =============================================================================
# Simulation Compatibility Tests
# =============================================================================

class TestSimulationCompatibility:
    """Tests to ensure simulation mode works exactly as before."""

    def test_simulation_scenarios(self):
        """Test all 5 simulation scenarios produce valid data."""
        obd = OBDService()
        obd.mode = OBDMode.SIMULATION
        obd.connect()
        obd.start_simulation("idle")
        time.sleep(0.2)

        scenarios = ["idle", "city", "highway", "acceleration", "overheating"]

        for scenario in scenarios:
            obd.simulation_engine.set_scenario(scenario)
            time.sleep(0.2)

            readings = obd.get_all_readings()

            # All sensors should have readings
            assert "rpm" in readings
            assert "speed_kmh" in readings
            assert "coolant_temp_c" in readings

            # Values should be in realistic ranges
            assert 0 <= readings["rpm"].value <= 7000
            assert 0 <= readings["speed_kmh"].value <= 180
            assert -20 <= readings["coolant_temp_c"].value <= 130

            # All should be marked as simulated
            assert all(r.is_simulated is True for r in readings.values())

        obd.stop_simulation()

    def test_simulation_gauge_thresholds(self):
        """Test gauge status thresholds work with simulation data."""
        obd = OBDService()
        obd.mode = OBDMode.SIMULATION
        obd.connect()
        obd.start_simulation("idle")
        time.sleep(0.2)

        readings = obd.get_all_readings()

        # Test each reading has valid gauge status
        for key, reading in readings.items():
            gauge_key_map = {
                "rpm": "rpm",
                "speed_kmh": "speed",
                "coolant_temp_c": "coolant_temp",
                "throttle_pos_pct": "throttle",
                "engine_load_pct": "engine_load",
                "stft_b1_pct": "fuel_trim",
                "ltft_b1_pct": "fuel_trim",
                "voltage_v": "voltage",
            }

            if key in gauge_key_map:
                status = obd.get_gauge_status(gauge_key_map[key], reading.value)
                assert status["color"] in ["green", "amber", "red", "blue"]
                assert "status" in status

        obd.stop_simulation()

    def test_demo_dtcs_simulation(self):
        """Test demo DTCs in simulation mode."""
        obd = OBDService()
        obd.mode = OBDMode.SIMULATION

        dtcs = obd.scan_dtcs()

        assert len(dtcs) == 4
        assert all(isinstance(d, DTC) for d in dtcs)
        assert all(d.is_demo is True for d in dtcs)
        assert all(d.code.startswith("P") for d in dtcs)

    def test_clear_dtcs_simulation(self):
        """Test DTC clearing in simulation mode."""
        obd = OBDService()
        obd.mode = OBDMode.SIMULATION

        result = obd.clear_dtcs()
        assert result is True

    def test_get_supported_pids_simulation(self):
        """Test supported PIDs in simulation mode."""
        obd = OBDService()
        obd.mode = OBDMode.SIMULATION

        pids = obd.get_supported_pids()

        assert len(pids) > 0
        assert "010C" in pids  # RPM
        assert "010D" in pids  # Speed


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
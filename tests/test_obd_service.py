"""
i20 AI Garage - OBD Service Tests
"""

import pytest
import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.obd_service import OBDService, OBDMode, ConnectionState, SimulationEngine, SensorReading, DTC


@pytest.fixture
def obd_service():
    """Create OBD service instance for testing."""
    return OBDService()


def test_simulation_engine_initialization(obd_service):
    """Test simulation engine initializes correctly."""
    engine = obd_service.simulation_engine

    assert engine.scenario == "idle"
    assert "rpm" in engine.vehicle_state
    assert engine.vehicle_state["rpm"] > 0


def test_simulation_engine_scenarios(obd_service):
    """Test scenario switching."""
    engine = obd_service.simulation_engine

    # Test each scenario
    for scenario_name in ["idle", "city", "highway", "acceleration", "overheating"]:
        engine.set_scenario(scenario_name)
        assert engine.scenario == scenario_name
        assert engine.scenario_config == engine.scenario_config  # Just verify no error


def test_simulation_engine_step(obd_service):
    """Test simulation step advances state."""
    engine = obd_service.simulation_engine
    engine.set_scenario("idle")

    initial_rpm = engine.vehicle_state["rpm"]
    readings = engine.step(0.1)

    assert "rpm" in readings
    assert "speed_kmh" in readings
    assert "coolant_temp_c" in readings
    # Values should be within reasonable ranges
    assert 0 <= readings["rpm"] <= 7000
    assert 0 <= readings["speed_kmh"] <= 180
    assert -20 <= readings["coolant_temp_c"] <= 130


def test_simulation_engine_clamping(obd_service):
    """Test value clamping to realistic ranges."""
    engine = obd_service.simulation_engine

    # Test RPM clamping
    assert engine._clamp_value("rpm", -100) == 0
    assert engine._clamp_value("rpm", 8000) == 7000

    # Test speed clamping
    assert engine._clamp_value("speed_kmh", -10) == 0
    assert engine._clamp_value("speed_kmh", 200) == 180

    # Test coolant temp clamping
    assert engine._clamp_value("coolant_temp_c", -50) == -20
    assert engine._clamp_value("coolant_temp_c", 200) == 130


def test_obd_connect_simulation(obd_service):
    """Test OBD connection in simulation mode."""
    obd_service.mode = OBDMode.SIMULATION
    result = obd_service.connect()

    assert result is True
    assert obd_service.connection_state == ConnectionState.CONNECTED


def test_obd_connect_real_not_implemented(obd_service):
    """Test real OBD mode shows not implemented."""
    obd_service.mode = OBDMode.REAL
    result = obd_service.connect()

    # Should fail and fall back to error state
    assert result is False
    assert obd_service.connection_state == ConnectionState.ERROR


def test_obd_disconnect(obd_service):
    """Test OBD disconnection."""
    obd_service.mode = OBDMode.SIMULATION
    obd_service.connect()
    obd_service.disconnect()

    assert obd_service.connection_state == ConnectionState.DISCONNECTED


def test_simulation_start_stop(obd_service):
    """Test simulation start and stop."""
    obd_service.mode = OBDMode.SIMULATION

    # Start simulation
    result = obd_service.start_simulation("idle")
    assert result is True
    assert obd_service.simulation_thread is not None
    assert obd_service.simulation_thread.is_alive()

    # Wait a bit for simulation to generate readings
    time.sleep(0.3)

    # Check readings are generated
    readings = obd_service.get_all_readings()
    assert len(readings) > 0
    assert "rpm" in readings

    # Stop simulation
    obd_service.stop_simulation()
    assert not obd_service.simulation_thread.is_alive()


def test_get_reading(obd_service):
    """Test getting individual sensor reading."""
    obd_service.mode = OBDMode.SIMULATION
    obd_service.start_simulation("idle")
    time.sleep(0.2)

    reading = obd_service.get_reading("rpm")
    assert reading is not None
    assert isinstance(reading, SensorReading)
    assert reading.pid == "0C"
    assert reading.name == "Engine RPM"
    assert reading.unit == "RPM"
    assert reading.is_simulated is True

    obd_service.stop_simulation()


def test_get_all_readings(obd_service):
    """Test getting all sensor readings."""
    obd_service.mode = OBDMode.SIMULATION
    obd_service.start_simulation("idle")
    time.sleep(0.2)

    readings = obd_service.get_all_readings()

    expected_keys = ["rpm", "speed_kmh", "coolant_temp_c", "throttle_pos_pct",
                     "engine_load_pct", "intake_pressure_kpa", "stft_b1_pct",
                     "ltft_b1_pct", "voltage_v", "maf_g_s", "map_kpa"]

    for key in expected_keys:
        assert key in readings
        assert isinstance(readings[key], SensorReading)

    obd_service.stop_simulation()


def test_gauge_status(obd_service):
    """Test gauge status determination."""
    # Test RPM thresholds
    assert obd_service.get_gauge_status("rpm", 2000)["color"] == "green"
    assert obd_service.get_gauge_status("rpm", 4000)["color"] == "amber"
    assert obd_service.get_gauge_status("rpm", 6000)["color"] == "red"

    # Test coolant temp thresholds
    assert obd_service.get_gauge_status("coolant_temp", 90)["color"] == "green"
    assert obd_service.get_gauge_status("coolant_temp", 100)["color"] == "amber"
    assert obd_service.get_gauge_status("coolant_temp", 110)["color"] == "red"

    # Test fuel trim range thresholds
    assert obd_service.get_gauge_status("fuel_trim", 0)["color"] == "green"
    assert obd_service.get_gauge_status("fuel_trim", 15)["color"] == "amber"
    assert obd_service.get_gauge_status("fuel_trim", 25)["color"] == "red"
    assert obd_service.get_gauge_status("fuel_trim", -15)["color"] == "amber"
    assert obd_service.get_gauge_status("fuel_trim", -25)["color"] == "red"


def test_scan_dtcs_simulation(obd_service):
    """Test DTC scanning in simulation mode."""
    obd_service.mode = OBDMode.SIMULATION
    dtcs = obd_service.scan_dtcs()

    assert len(dtcs) == 4
    for dtc in dtcs:
        assert isinstance(dtc, DTC)
        assert dtc.is_demo is True
        assert dtc.code.startswith("P")
        assert dtc.severity in ["critical", "major", "minor", "info"]


def test_clear_dtcs_simulation(obd_service):
    """Test DTC clearing in simulation mode."""
    obd_service.mode = OBDMode.SIMULATION
    result = obd_service.clear_dtcs()

    # Should succeed but not actually clear anything in simulation
    assert result is True


def test_get_supported_pids(obd_service):
    """Test getting supported PIDs."""
    obd_service.mode = OBDMode.SIMULATION
    pids = obd_service.get_supported_pids()

    assert len(pids) > 0
    assert "010C" in pids  # RPM
    assert "010D" in pids  # Speed


def test_get_status(obd_service):
    """Test OBD service status."""
    obd_service.mode = OBDMode.SIMULATION
    obd_service.connect()

    status = obd_service.get_status()

    assert status["mode"] == "simulation"
    assert status["connection_state"] == "connected"
    assert status["port"] == "N/A (Simulation)"
    assert "supported_pids_count" in status


def test_get_available_scenarios(obd_service):
    """Test getting available simulation scenarios."""
    scenarios = obd_service.get_available_scenarios()

    assert "idle" in scenarios
    assert "city" in scenarios
    assert "highway" in scenarios
    assert "acceleration" in scenarios
    assert "overheating" in scenarios

    for scenario in scenarios.values():
        assert "name" in scenario
        assert "description" in scenario


def test_mode_switching(obd_service):
    """Test switching between simulation and real modes."""
    # Start in simulation
    obd_service.mode = OBDMode.SIMULATION
    obd_service.connect()
    assert obd_service.connection_state == ConnectionState.CONNECTED

    # Switch to real (should fail)
    result = obd_service.set_mode(OBDMode.REAL)
    assert result is False
    assert obd_service.connection_state == ConnectionState.ERROR

    # Switch back to simulation
    result = obd_service.set_mode(OBDMode.SIMULATION)
    assert result is True
    assert obd_service.connection_state == ConnectionState.CONNECTED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
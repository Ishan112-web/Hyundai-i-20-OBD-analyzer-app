"""
i20 AI Garage - Simulation Tests
"""

import pytest
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.obd_service import SimulationEngine, OBDService, OBDMode, ConnectionState
from config import SIMULATION_SCENARIOS, GAUGE_THRESHOLDS


def test_simulation_scenarios_config():
    """Test simulation scenarios are properly configured."""
    for name, config in SIMULATION_SCENARIOS.items():
        assert "name" in config
        assert "description" in config
        assert "rpm_range" in config
        assert "speed_range" in config
        assert "coolant_temp_range" in config
        assert "throttle_range" in config
        assert "load_range" in config

        # Verify ranges are valid
        assert config["rpm_range"][0] < config["rpm_range"][1]
        assert config["speed_range"][0] <= config["speed_range"][1]
        assert config["coolant_temp_range"][0] < config["coolant_temp_range"][1]


def test_idle_scenario_behavior():
    """Test idle scenario produces stable idle values."""
    engine = SimulationEngine()
    engine.set_scenario("idle")

    # Run multiple steps
    rpm_values = []
    speed_values = []
    for _ in range(50):
        readings = engine.step(0.1)
        rpm_values.append(readings["rpm"])
        speed_values.append(readings["speed_kmh"])

    # RPM should stay near idle (700-950)
    avg_rpm = sum(rpm_values) / len(rpm_values)
    assert 650 <= avg_rpm <= 1000

    # Speed should remain near 0 (allow small noise)
    assert all(abs(s) < 1.0 for s in speed_values)


def test_city_scenario_behavior():
    """Test city scenario produces variable speeds."""
    engine = SimulationEngine()
    engine.set_scenario("city")

    speed_values = []
    rpm_values = []
    for _ in range(100):
        readings = engine.step(0.1)
        speed_values.append(readings["speed_kmh"])
        rpm_values.append(readings["rpm"])

    # Should have some variation in speed
    assert max(speed_values) > min(speed_values)
    assert max(speed_values) <= 50
    assert max(rpm_values) <= 3000


def test_highway_scenario_behavior():
    """Test highway scenario produces steady high speeds."""
    engine = SimulationEngine()
    engine.set_scenario("highway")

    speed_values = []
    for _ in range(50):
        readings = engine.step(0.1)
        speed_values.append(readings["speed_kmh"])

    # Speed should be in highway range
    avg_speed = sum(speed_values) / len(speed_values)
    assert 60 <= avg_speed <= 120


def test_acceleration_scenario_behavior():
    """Test acceleration scenario increases speed and RPM."""
    engine = SimulationEngine()
    engine.set_scenario("acceleration")

    initial_speed = engine.vehicle_state["speed_kmh"]
    initial_rpm = engine.vehicle_state["rpm"]

    # Run for simulated 5 seconds
    for _ in range(50):
        engine.step(0.1)

    # Speed and RPM should have increased
    assert engine.vehicle_state["speed_kmh"] > initial_speed
    assert engine.vehicle_state["rpm"] > initial_rpm
    assert engine.vehicle_state["throttle_pos_pct"] > 50


def test_overheating_scenario_behavior():
    """Test overheating scenario increases coolant temperature."""
    engine = SimulationEngine()
    engine.set_scenario("overheating")

    initial_temp = engine.vehicle_state["coolant_temp_c"]

    # Run for simulated 10 seconds
    for _ in range(100):
        engine.step(0.1)

    # Temperature should have risen
    assert engine.vehicle_state["coolant_temp_c"] > initial_temp
    assert engine.vehicle_state["coolant_temp_c"] > 100


def test_gauge_thresholds_config():
    """Test gauge thresholds are properly configured."""
    for gauge, thresholds in GAUGE_THRESHOLDS.items():
        if "green_max" in thresholds:
            # Simple upper threshold
            assert thresholds["green_max"] < thresholds["amber_max"]
            assert thresholds["amber_max"] < thresholds["red_max"]
        elif "green_min" in thresholds:
            # Range threshold
            assert thresholds["green_min"] < thresholds["green_max"]
            assert thresholds["amber_min"] < thresholds["amber_max"]
            # Amber range should extend beyond green
            assert thresholds["amber_min"] <= thresholds["green_min"]
            assert thresholds["amber_max"] >= thresholds["green_max"]


def test_obd_service_simulation_integration():
    """Test full OBD service simulation integration."""
    obd = OBDService()
    obd.mode = OBDMode.SIMULATION

    # Connect
    assert obd.connect() is True
    assert obd.connection_state == ConnectionState.CONNECTED

    # Start simulation
    assert obd.start_simulation("city") is True

    # Wait for readings
    time.sleep(0.5)

    # Verify readings
    readings = obd.get_all_readings()
    assert len(readings) == 11  # All expected sensors

    # Verify reading structure
    for key, reading in readings.items():
        assert reading.is_simulated is True
        assert reading.value is not None
        assert reading.unit != ""
        assert reading.pid != ""

    # Test gauge status for each reading
    for key, reading in readings.items():
        # Map reading key to gauge threshold key
        gauge_map = {
            "rpm": "rpm",
            "speed_kmh": "speed",
            "coolant_temp_c": "coolant_temp",
            "throttle_pos_pct": "throttle",
            "engine_load_pct": "engine_load",
            "stft_b1_pct": "fuel_trim",
            "ltft_b1_pct": "fuel_trim",
            "voltage_v": "voltage",
        }
        if key in gauge_map:
            status = obd.get_gauge_status(gauge_map[key], reading.value)
            assert status["color"] in ["green", "amber", "red", "blue"]
            assert "status" in status

    # Stop simulation
    obd.stop_simulation()
    assert not obd.simulation_thread.is_alive()

    # Disconnect
    obd.disconnect()
    assert obd.connection_state == ConnectionState.DISCONNECTED


def test_simulation_deterministic_ranges():
    """Test simulation values stay within configured ranges."""
    engine = SimulationEngine()

    for scenario_name in SIMULATION_SCENARIOS:
        engine.set_scenario(scenario_name)
        config = SIMULATION_SCENARIOS[scenario_name]

        # Run a few steps to let values transition to new scenario range
        for _ in range(10):
            engine.step(0.1)

        for _ in range(20):
            readings = engine.step(0.1)

            # Check RPM range
            rpm_min, rpm_max = config["rpm_range"]
            # Allow some overshoot due to dynamics - overheating scenario has more variation
            rpm_overshoot = 1000 if scenario_name == "overheating" else 500
            assert rpm_min - 100 <= readings["rpm"] <= rpm_max + rpm_overshoot

            # Check speed range
            speed_min, speed_max = config["speed_range"]
            assert speed_min - 5 <= readings["speed_kmh"] <= speed_max + 10

            # Check coolant temp range
            temp_min, temp_max = config["coolant_temp_range"]
            assert temp_min - 5 <= readings["coolant_temp_c"] <= temp_max + 10


def test_simulation_thread_safety():
    """Test simulation can be started/stopped multiple times."""
    obd = OBDService()
    obd.mode = OBDMode.SIMULATION
    obd.connect()

    for _ in range(3):
        obd.start_simulation("idle")
        time.sleep(0.2)
        assert obd.simulation_thread.is_alive()

        obd.stop_simulation()
        assert not obd.simulation_thread.is_alive()

    obd.disconnect()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
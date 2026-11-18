"""
i20 AI Garage - OBD Service

OBD-II abstraction layer with simulation mode and real adapter support using python-OBD.
Integrates RealOBDAdapter, ConnectionManager, and PIDRegistry for V2 Phase 1.
"""

import random
import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from threading import Thread, Event

from config import (
    OBD_MODE, OBD_PORT, OBD_BAUDRATE, OBD_PROTOCOL,
    SIMULATION_SCENARIOS, ENGINE_SPECS, GAUGE_THRESHOLDS,
    OBD_REAL_CONFIG, PID_POLLING_CONFIG
)

# Import new V2 Phase 1 components
from services.real_obd_adapter import RealOBDAdapter, ConnectionProfile, AdapterType
from services.connection_manager import ConnectionManager, PortInfo
from services.pid_registry import PIDRegistry, PIDPriority
from services.types import OBDMode, ConnectionState, SensorReading, DTC

logger = logging.getLogger(__name__)


class SimulationEngine:
    """Generates realistic simulated vehicle telemetry."""

    def __init__(self):
        self.scenario = "idle"
        self.scenario_config = SIMULATION_SCENARIOS[self.scenario]
        self.time_offset = 0.0
        self.vehicle_state = {
            "rpm": 800.0,
            "speed_kmh": 0.0,
            "coolant_temp_c": 85.0,
            "throttle_pos_pct": 0.0,
            "engine_load_pct": 15.0,
            "intake_pressure_kpa": 30.0,
            "stft_b1_pct": 0.0,
            "ltft_b1_pct": 0.0,
            "voltage_v": 14.2,
            "maf_g_s": 3.5,
            "map_kpa": 30.0,
        }
        self.target_state = self.vehicle_state.copy()
        self.transition_speed = 0.1

    def set_scenario(self, scenario: str):
        """Set simulation scenario."""
        if scenario in SIMULATION_SCENARIOS:
            self.scenario = scenario
            self.scenario_config = SIMULATION_SCENARIOS[scenario]
            self._update_targets()

    def _update_targets(self):
        """Update target values based on scenario."""
        cfg = self.scenario_config
        self.target_state = {
            "rpm": random.uniform(*cfg["rpm_range"]),
            "speed_kmh": random.uniform(*cfg["speed_range"]),
            "coolant_temp_c": random.uniform(*cfg["coolant_temp_range"]),
            "throttle_pos_pct": random.uniform(*cfg["throttle_range"]),
            "engine_load_pct": random.uniform(*cfg["load_range"]),
            "intake_pressure_kpa": random.uniform(20, 100),
            "stft_b1_pct": random.uniform(-5, 5),
            "ltft_b1_pct": random.uniform(-3, 3),
            "voltage_v": random.uniform(13.8, 14.4),
            "maf_g_s": random.uniform(2, 50),
            "map_kpa": random.uniform(20, 100),
        }

        # Correlated adjustments
        # RPM and speed correlation
        if self.target_state["speed_kmh"] > 0:
            self.target_state["rpm"] = max(
                self.target_state["rpm"],
                self.target_state["speed_kmh"] * 30
            )

        # Throttle and load correlation
        self.target_state["engine_load_pct"] = min(
            100,
            self.target_state["engine_load_pct"] + self.target_state["throttle_pos_pct"] * 0.5
        )

        # Intake pressure based on throttle
        self.target_state["intake_pressure_kpa"] = 20 + (self.target_state["throttle_pos_pct"] / 100) * 80
        self.target_state["map_kpa"] = self.target_state["intake_pressure_kpa"]

        # MAF based on RPM and throttle
        self.target_state["maf_g_s"] = (self.target_state["rpm"] / 1000) * (self.target_state["throttle_pos_pct"] / 100) * 10

    def step(self, dt: float = 0.1) -> Dict[str, float]:
        """Advance simulation by dt seconds and return current values."""
        self.time_offset += dt

        # Occasionally update targets for variety
        if random.random() < 0.02:  # 2% chance per step
            self._update_targets()

        # Smooth transition toward targets
        for key in self.vehicle_state:
            if key in self.target_state:
                diff = self.target_state[key] - self.vehicle_state[key]
                self.vehicle_state[key] += diff * self.transition_speed

                # Add small noise
                noise_scale = self._get_noise_scale(key)
                self.vehicle_state[key] += random.uniform(-noise_scale, noise_scale)

                # Clamp to reasonable ranges
                self.vehicle_state[key] = self._clamp_value(key, self.vehicle_state[key])

        # Add scenario-specific behaviors
        self._apply_scenario_behavior(dt)

        return self.vehicle_state.copy()

    def _get_noise_scale(self, key: str) -> float:
        """Get noise scale for a parameter."""
        scales = {
            "rpm": 25.0,
            "speed_kmh": 1.0,
            "coolant_temp_c": 0.2,
            "throttle_pos_pct": 1.0,
            "engine_load_pct": 1.5,
            "intake_pressure_kpa": 1.0,
            "stft_b1_pct": 0.5,
            "ltft_b1_pct": 0.2,
            "voltage_v": 0.05,
            "maf_g_s": 0.5,
            "map_kpa": 1.0,
        }
        return scales.get(key, 0.1)

    def _clamp_value(self, key: str, value: float) -> float:
        """Clamp value to realistic range."""
        clamps = {
            "rpm": (0, 7000),
            "speed_kmh": (0, 180),
            "coolant_temp_c": (-20, 130),
            "throttle_pos_pct": (0, 100),
            "engine_load_pct": (0, 100),
            "intake_pressure_kpa": (0, 250),
            "stft_b1_pct": (-100, 100),
            "ltft_b1_pct": (-100, 100),
            "voltage_v": (10, 16),
            "maf_g_s": (0, 200),
            "map_kpa": (0, 250),
        }
        min_val, max_val = clamps.get(key, (0, 100))
        return max(min_val, min(max_val, value))

    def _apply_scenario_behavior(self, dt: float):
        """Apply scenario-specific dynamic behavior."""
        if self.scenario == "idle":
            # Stable idle with slight variation
            self.vehicle_state["rpm"] += random.uniform(-10, 10)
            self.vehicle_state["rpm"] = max(650, min(950, self.vehicle_state["rpm"]))
            # Speed should remain 0 at idle
            self.vehicle_state["speed_kmh"] = 0.0

        elif self.scenario == "city":
            # Stop-and-go simulation
            if random.random() < 0.01:  # Random stops
                self.target_state["speed_kmh"] = 0
                self.target_state["rpm"] = random.uniform(700, 1000)
                self.target_state["throttle_pos_pct"] = random.uniform(0, 5)
            elif random.random() < 0.01:  # Random acceleration
                self.target_state["speed_kmh"] = random.uniform(20, 50)
                self.target_state["rpm"] = random.uniform(1500, 3000)
                self.target_state["throttle_pos_pct"] = random.uniform(20, 50)

        elif self.scenario == "highway":
            # Steady with minor variations
            self.vehicle_state["speed_kmh"] += random.uniform(-0.5, 0.5)
            self.vehicle_state["speed_kmh"] = max(60, min(120, self.vehicle_state["speed_kmh"]))

        elif self.scenario == "acceleration":
            # Progressive acceleration
            self.vehicle_state["speed_kmh"] += dt * 5  # ~5 km/h per second
            self.vehicle_state["rpm"] += dt * 200  # ~200 RPM per second
            self.vehicle_state["throttle_pos_pct"] = min(100, self.vehicle_state["throttle_pos_pct"] + dt * 10)

            # Shift points simulation (simplified)
            if self.vehicle_state["rpm"] > 6000:
                self.vehicle_state["rpm"] = max(2000, self.vehicle_state["rpm"] - 1500)
                self.vehicle_state["throttle_pos_pct"] = max(30, self.vehicle_state["throttle_pos_pct"] - 20)

        elif self.scenario == "overheating":
            # Gradual temperature rise
            self.vehicle_state["coolant_temp_c"] += dt * 0.5  # 0.5°C per second
            self.vehicle_state["coolant_temp_c"] = min(125, self.vehicle_state["coolant_temp_c"])

            # Engine compensation
            if self.vehicle_state["coolant_temp_c"] > 110:
                self.vehicle_state["engine_load_pct"] = min(100, self.vehicle_state["engine_load_pct"] + dt * 2)
                self.vehicle_state["stft_b1_pct"] += dt * 0.5  # Running richer to cool


class OBDService:
    """OBD-II service with simulation and real adapter support."""

    def __init__(self):
        self.mode = OBDMode(OBD_MODE)
        self.port = OBD_PORT
        self.baudrate = OBD_BAUDRATE
        self.protocol = OBD_PROTOCOL

        self.connection_state = ConnectionState.DISCONNECTED
        self.simulation_engine = SimulationEngine()
        self.simulation_thread: Optional[Thread] = None
        self.simulation_stop_event = Event()
        self.simulation_interval = 0.1  # 100ms = 10Hz

        # Real OBD components (V2 Phase 1)
        self._real_adapter: Optional[RealOBDAdapter] = None
        self._connection_manager: Optional[ConnectionManager] = None
        self._pid_registry = PIDRegistry()

        # Current readings cache
        self.current_readings: Dict[str, SensorReading] = {}
        self.last_update = datetime.now()

        # Demo DTCs for simulation
        self.demo_dtcs = [
            DTC("P0300", "Random/Multiple Cylinder Misfire Detected", "major"),
            DTC("P0171", "System Too Lean (Bank 1)", "major"),
            DTC("P0420", "Catalyst System Efficiency Below Threshold (Bank 1)", "minor"),
            DTC("P0128", "Coolant Thermostat (Coolant Temperature Below Thermostat Regulating Temperature)", "minor"),
        ]

        # Initialize connection manager
        self._init_connection_manager()

    def _init_connection_manager(self):
        """Initialize the connection manager with callbacks."""
        self._connection_manager = ConnectionManager(
            profiles_file="data/connection_profiles.json",
            health_check_interval=OBD_REAL_CONFIG["health_check_interval"],
            on_status_change=self._on_connection_status_change,
            on_connection_log=self._on_connection_log
        )

    def _on_connection_status_change(self, state: ConnectionState):
        """Callback for connection state changes."""
        self.connection_state = state
        logger.info(f"OBD connection state changed: {state.value}")

    def _on_connection_log(self, event: Dict[str, Any]):
        """Callback for connection log events."""
        try:
            from services import get_database
            db = get_database()
            db.log_obd_connection(
                event_type=event.get("event_type", "unknown"),
                port=event.get("port"),
                baudrate=event.get("baudrate"),
                protocol=event.get("protocol"),
                details=event.get("details", "")
            )
        except Exception as e:
            logger.error(f"Failed to log connection event: {e}")

    @property
    def connection_manager(self) -> ConnectionManager:
        """Get the connection manager instance."""
        return self._connection_manager

    @property
    def pid_registry(self) -> PIDRegistry:
        """Get the PID registry instance."""
        return self._pid_registry

    @property
    def real_adapter(self) -> Optional[RealOBDAdapter]:
        """Get the real OBD adapter instance."""
        return self._real_adapter

    def connect(self) -> bool:
        """Establish OBD connection."""
        if self.mode == OBDMode.SIMULATION:
            self.connection_state = ConnectionState.CONNECTED
            logger.info("OBD Simulation mode connected")
            return True
        else:
            return self._connect_real()

    def _connect_real(self) -> bool:
        """Connect to real OBD adapter using ConnectionManager."""
        self.connection_state = ConnectionState.CONNECTING

        try:
            # Use connection manager for connection
            success = self._connection_manager.connect(
                port=self.port,
                baudrate=self.baudrate,
                protocol=self.protocol,
                timeout=OBD_REAL_CONFIG["connection_timeout"],
                query_timeout=OBD_REAL_CONFIG["query_timeout"],
                save_profile=True
            )

            if success:
                self._real_adapter = self._connection_manager.adapter
                # Update PID registry with discovered PIDs
                if self._real_adapter:
                    self._pid_registry.set_supported_pids(self._real_adapter.supported_pids)
                    # Cache supported PIDs to database
                    self._cache_supported_pids()

                self.connection_state = ConnectionState.CONNECTED
                # Start auto-reconnect monitoring
                self._connection_manager.start_auto_reconnect()
                logger.info(f"Real OBD connected on {self.port}")
                return True
            else:
                self.connection_state = ConnectionState.ERROR
                logger.error(f"Real OBD connection failed: {self._connection_manager.adapter._last_error if self._connection_manager.adapter else 'Unknown error'}")
                return False

        except Exception as e:
            logger.error(f"Real OBD connection error: {e}")
            self.connection_state = ConnectionState.ERROR
            return False

    def _cache_supported_pids(self):
        """Cache supported PIDs to database."""
        try:
            from services import get_database
            db = get_database()
            pids_data = []
            for pid in self._pid_registry.supported_pids:
                definition = self._pid_registry.get_definition(pid)
                if definition:
                    pids_data.append({
                        "pid": pid,
                        "name": definition.name,
                        "unit": definition.unit,
                        "description": definition.description,
                        "is_supported": True
                    })
            if pids_data:
                db.save_supported_pids(pids_data)
        except Exception as e:
            logger.error(f"Failed to cache supported PIDs: {e}")

    def disconnect(self):
        """Disconnect from OBD adapter."""
        self.stop_simulation()

        if self._connection_manager:
            self._connection_manager.disconnect()

        if self.mode == OBDMode.REAL and self._real_adapter:
            try:
                self._real_adapter.disconnect()
            except Exception as e:
                logger.error(f"Error closing OBD connection: {e}")

        self._real_adapter = None
        self.connection_state = ConnectionState.DISCONNECTED
        logger.info("OBD disconnected")

    def set_mode(self, mode: OBDMode) -> bool:
        """Change OBD mode (simulation/real)."""
        # Track if we should reconnect - either was connected, or switching to simulation
        was_connected = self.connection_state == ConnectionState.CONNECTED
        should_reconnect = was_connected or mode == OBDMode.SIMULATION

        self.disconnect()
        self.mode = mode

        if should_reconnect:
            return self.connect()
        return True

    def start_simulation(self, scenario: str = "idle") -> bool:
        """Start simulation loop."""
        if self.connection_state != ConnectionState.CONNECTED:
            if not self.connect():
                return False

        if self.simulation_thread and self.simulation_thread.is_alive():
            return True  # Already running

        self.simulation_engine.set_scenario(scenario)
        self.simulation_stop_event.clear()
        self.simulation_thread = Thread(target=self._simulation_loop, daemon=True)
        self.simulation_thread.start()
        logger.info(f"Simulation started: {scenario}")
        return True

    def stop_simulation(self):
        """Stop simulation loop."""
        self.simulation_stop_event.set()
        if self.simulation_thread:
            self.simulation_thread.join(timeout=1.0)
        logger.info("Simulation stopped")

    def _simulation_loop(self):
        """Background simulation loop."""
        while not self.simulation_stop_event.is_set():
            try:
                readings = self.simulation_engine.step(self.simulation_interval)
                self._update_readings_cache(readings, is_simulated=True)
                time.sleep(self.simulation_interval)
            except Exception as e:
                logger.error(f"Simulation loop error: {e}")
                time.sleep(1.0)

    def _update_readings_cache(self, readings: Dict[str, float], is_simulated: bool = True):
        """Update cached sensor readings."""
        timestamp = datetime.now()
        pid_map = {
            "rpm": ("0C", "Engine RPM", "RPM"),
            "speed_kmh": ("0D", "Vehicle Speed", "km/h"),
            "coolant_temp_c": ("05", "Engine Coolant Temperature", "°C"),
            "throttle_pos_pct": ("11", "Throttle Position", "%"),
            "engine_load_pct": ("04", "Calculated Engine Load", "%"),
            "intake_pressure_kpa": ("0B", "Intake Manifold Pressure", "kPa"),
            "stft_b1_pct": ("06", "Short Term Fuel Trim Bank 1", "%"),
            "ltft_b1_pct": ("07", "Long Term Fuel Trim Bank 1", "%"),
            "voltage_v": ("42", "Control Module Voltage", "V"),
            "maf_g_s": ("10", "MAF Air Flow Rate", "g/s"),
            "map_kpa": ("0B", "Manifold Absolute Pressure", "kPa"),
        }

        for key, (pid, name, unit) in pid_map.items():
            if key in readings:
                self.current_readings[key] = SensorReading(
                    pid=pid,
                    name=name,
                    value=readings[key],
                    unit=unit,
                    timestamp=timestamp,
                    is_simulated=is_simulated
                )
        self.last_update = timestamp

    def poll_real_pids(self) -> Dict[str, Optional[float]]:
        """
        Poll real PIDs from the adapter based on priority intervals.
        Returns dictionary of sensor_key -> value.
        """
        if not self._real_adapter or not self._real_adapter.is_connected:
            return {}

        results = {}
        current_time = time.monotonic()

        # Get PIDs that are due for polling
        for priority in PIDPriority:
            pids = self._pid_registry.get_pids_by_priority(priority)
            for definition in pids:
                if self._pid_registry.should_poll(definition.pid, current_time):
                    value = self._real_adapter.query_pid(definition.pid)
                    if value is not None:
                        # Validate value
                        is_valid, clamped_value = self._pid_registry.validate_value(definition.pid, value)
                        if not is_valid:
                            value = clamped_value

                        # Record result
                        from services.pid_registry import PIDValue
                        pid_value = PIDValue(
                            pid=definition.pid,
                            sensor_key=definition.sensor_key,
                            value=value,
                            unit=definition.unit,
                            timestamp=datetime.now(),
                            success=True
                        )
                        self._pid_registry.record_result(pid_value)
                        self._pid_registry.mark_polled(definition.pid, current_time)
                        results[definition.sensor_key] = value
                    else:
                        # Record failure
                        from services.pid_registry import PIDValue
                        pid_value = PIDValue(
                            pid=definition.pid,
                            sensor_key=definition.sensor_key,
                            value=None,
                            unit=definition.unit,
                            timestamp=datetime.now(),
                            success=False,
                            error="Query returned null"
                        )
                        self._pid_registry.record_result(pid_value)
                        self._pid_registry.mark_polled(definition.pid, current_time)

        return results

    def update_real_readings(self):
        """Update readings cache with real OBD data."""
        if self.mode != OBDMode.REAL or not self._real_adapter:
            return

        # Poll PIDs based on priority
        real_values = self.poll_real_pids()

        if real_values:
            timestamp = datetime.now()
            pid_to_sensor = {
                "0C": ("rpm", "Engine RPM", "RPM"),
                "0D": ("speed_kmh", "Vehicle Speed", "km/h"),
                "05": ("coolant_temp_c", "Engine Coolant Temperature", "°C"),
                "11": ("throttle_pos_pct", "Throttle Position", "%"),
                "04": ("engine_load_pct", "Calculated Engine Load", "%"),
                "0B": ("intake_pressure_kpa", "Intake Manifold Pressure", "kPa"),
                "06": ("stft_b1_pct", "Short Term Fuel Trim Bank 1", "%"),
                "07": ("ltft_b1_pct", "Long Term Fuel Trim Bank 1", "%"),
                "42": ("voltage_v", "Control Module Voltage", "V"),
                "10": ("maf_g_s", "MAF Air Flow Rate", "g/s"),
                "0F": ("intake_temp_c", "Intake Air Temperature", "°C"),
            }

            for pid, (key, name, unit) in pid_to_sensor.items():
                if pid in self._real_adapter.supported_pids and key in real_values:
                    self.current_readings[key] = SensorReading(
                        pid=pid,
                        name=name,
                        value=real_values[key],
                        unit=unit,
                        timestamp=timestamp,
                        is_simulated=False
                    )
            self.last_update = timestamp

    def get_reading(self, key: str) -> Optional[SensorReading]:
        """Get latest reading for a sensor."""
        return self.current_readings.get(key)

    def get_all_readings(self) -> Dict[str, SensorReading]:
        """Get all current readings."""
        # If real mode, update readings from adapter first
        if self.mode == OBDMode.REAL:
            self.update_real_readings()
        return self.current_readings.copy()

    def get_gauge_status(self, key: str, value: float) -> Dict[str, Any]:
        """Get gauge status (color, label) based on thresholds."""
        thresholds = GAUGE_THRESHOLDS.get(key, {})

        # Check for range threshold first (both green_min and green_max present)
        # This handles fuel_trim, voltage which have min/max ranges
        if "green_min" in thresholds and "green_max" in thresholds:
            if thresholds["green_min"] <= value <= thresholds["green_max"]:
                return {"color": "green", "status": "Normal"}
            elif thresholds["amber_min"] <= value <= thresholds["amber_max"]:
                return {"color": "amber", "status": "Caution"}
            else:
                return {"color": "red", "status": "Critical"}
        # Simple upper threshold (rpm, speed, coolant_temp, throttle, engine_load)
        elif "green_max" in thresholds:
            if value <= thresholds["green_max"]:
                return {"color": "green", "status": "Normal"}
            elif value <= thresholds["amber_max"]:
                return {"color": "amber", "status": "Caution"}
            else:
                return {"color": "red", "status": "Critical"}
        return {"color": "blue", "status": "Unknown"}

    def scan_dtcs(self) -> List[DTC]:
        """Scan for diagnostic trouble codes."""
        if self.mode == OBDMode.SIMULATION:
            # Return demo DTCs in simulation mode
            return self.demo_dtcs.copy()
        else:
            # Real OBD DTC scanning
            if self._real_adapter and self._real_adapter.is_connected:
                return self._real_adapter.scan_dtcs()
            return []

    def clear_dtcs(self) -> bool:
        """Clear diagnostic trouble codes."""
        if self.mode == OBDMode.SIMULATION:
            logger.info("DTC clear requested (simulation mode - no action)")
            return True
        else:
            if self._real_adapter and self._real_adapter.is_connected:
                return self._real_adapter.clear_dtcs()
            return False

    def get_freeze_frame(self, dtc_code: str) -> Optional[Dict[str, Any]]:
        """Get freeze frame data for a DTC."""
        if self.mode == OBDMode.SIMULATION:
            return None
        else:
            if self._real_adapter and self._real_adapter.is_connected:
                ff = self._real_adapter.get_freeze_frame(dtc_code)
                if ff:
                    return {
                        "dtc_code": ff.dtc_code,
                        "rpm": ff.rpm,
                        "speed_kmh": ff.speed_kmh,
                        "coolant_temp_c": ff.coolant_temp_c,
                        "throttle_pos_pct": ff.throttle_pos_pct,
                        "engine_load_pct": ff.engine_load_pct,
                        "map_kpa": ff.map_kpa,
                        "maf_g_s": ff.maf_g_s,
                        "fuel_system_status": ff.fuel_system_status,
                        "timestamp": ff.timestamp.isoformat()
                    }
            return None

    def get_supported_pids(self) -> List[str]:
        """Get list of supported PIDs."""
        if self.mode == OBDMode.SIMULATION:
            return [
                "0100", "0104", "0105", "0106", "0107", "010B", "010C", "010D",
                "0110", "0111", "0142", "0146", "0147"
            ]
        return self._pid_registry.supported_pids

    def get_vehicle_info(self) -> Dict[str, Optional[str]]:
        """Get vehicle identification info (VIN, CALID, CVN, ECU name)."""
        if self.mode == OBDMode.SIMULATION:
            return {
                "vin": "MALA841CLHM123456",
                "calid": "SIMULATION",
                "cvn": "SIMULATION",
                "ecu_name": "Simulation ECU"
            }
        else:
            if self._real_adapter and self._real_adapter.is_connected:
                return {
                    "vin": self._real_adapter.get_vin(),
                    "calid": self._real_adapter.get_calid(),
                    "cvn": self._real_adapter.get_cvn(),
                    "ecu_name": self._real_adapter.get_ecu_name()
                }
            return {}

    def get_fuel_system_status(self) -> Optional[str]:
        """Get fuel system status."""
        if self.mode == OBDMode.SIMULATION:
            return "Closed Loop"
        else:
            if self._real_adapter and self._real_adapter.is_connected:
                return self._real_adapter.get_fuel_system_status()
            return None

    def get_engine_runtime(self) -> Optional[float]:
        """Get engine runtime in seconds."""
        if self.mode == OBDMode.SIMULATION:
            return 3600.0  # 1 hour
        else:
            if self._real_adapter and self._real_adapter.is_connected:
                return self._real_adapter.get_runtime()
            return None

    def get_status(self) -> Dict[str, Any]:
        """Get OBD service status."""
        status = {
            "mode": self.mode.value,
            "connection_state": self.connection_state.value,
            "port": self.port if self.mode == OBDMode.REAL else "N/A (Simulation)",
            "baudrate": self.baudrate if self.mode == OBDMode.REAL else "N/A",
            "protocol": self.protocol if self.mode == OBDMode.REAL else "N/A",
            "simulation_running": self.simulation_thread is not None and self.simulation_thread.is_alive(),
            "current_scenario": self.simulation_engine.scenario,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "supported_pids_count": len(self.get_supported_pids()),
        }

        # Add real OBD specific info
        if self.mode == OBDMode.REAL and self._connection_manager:
            conn_status = self._connection_manager.get_connection_status()
            status.update({
                "adapter_type": conn_status.get("adapter_type"),
                "health": conn_status.get("health"),
                "statistics": conn_status.get("statistics"),
                "reconnect_enabled": conn_status.get("reconnect_enabled"),
                "reconnect_attempts": conn_status.get("reconnect_attempts"),
            })

        # Add PID registry info
        status["pid_registry"] = self._pid_registry.get_registry_summary()

        return status

    def get_available_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """Get available simulation scenarios."""
        return {
            key: {
                "name": val["name"],
                "description": val["description"],
            }
            for key, val in SIMULATION_SCENARIOS.items()
        }

    def discover_ports(self) -> List[PortInfo]:
        """Discover available serial ports."""
        if self._connection_manager:
            return self._connection_manager.discover_ports()
        return []

    def auto_connect(self, timeout: float = 10.0) -> bool:
        """Auto-discover and connect to OBD adapter."""
        if self._connection_manager:
            success = self._connection_manager.auto_connect(timeout)
            if success:
                self._real_adapter = self._connection_manager.adapter
                if self._real_adapter:
                    self._pid_registry.set_supported_pids(self._real_adapter.supported_pids)
                    self._cache_supported_pids()
            return success
        return False

    def get_connection_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get OBD connection logs from database."""
        try:
            from services import get_database
            db = get_database()
            return db.get_obd_connection_logs(limit)
        except Exception as e:
            logger.error(f"Failed to get connection logs: {e}")
            return []


# Singleton instance
_obd_instance: Optional[OBDService] = None


def get_obd_service() -> OBDService:
    """Get the OBD service singleton."""
    global _obd_instance
    if _obd_instance is None:
        _obd_instance = OBDService()
    return _obd_instance
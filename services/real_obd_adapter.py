"""
i20 AI Garage - Real OBD Adapter

ELM327 communication layer using python-OBD library.
Handles real vehicle connectivity for Hyundai i20 Asta 2023.
"""

import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

import obd
from obd import OBDStatus, Unit

from config import (
    OBD_REAL_CONFIG,
    PID_POLLING_CONFIG,
    ENGINE_SPECS,
    GAUGE_THRESHOLDS
)
from services.types import SensorReading, DTC, OBDMode, ConnectionState

logger = logging.getLogger(__name__)


class AdapterType(Enum):
    """Supported OBD adapter types."""
    USB = "usb"
    BLUETOOTH = "bluetooth"
    WIFI = "wifi"
    UNKNOWN = "unknown"


@dataclass
class ConnectionProfile:
    """OBD connection profile for reuse."""
    port: str
    baudrate: int
    protocol: str
    adapter_type: AdapterType
    friendly_name: str = ""
    last_connected: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0


@dataclass
class PIDInfo:
    """PID information from vehicle."""
    pid: str
    name: str
    unit: str
    description: str
    is_supported: bool = False
    min_value: Optional[float] = None
    max_value: Optional[float] = None


@dataclass
class FreezeFrameData:
    """Freeze frame data for a DTC."""
    dtc_code: str
    rpm: Optional[float] = None
    speed_kmh: Optional[float] = None
    coolant_temp_c: Optional[float] = None
    throttle_pos_pct: Optional[float] = None
    engine_load_pct: Optional[float] = None
    map_kpa: Optional[float] = None
    maf_g_s: Optional[float] = None
    fuel_system_status: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class RealOBDAdapter:
    """
    Real OBD-II adapter using python-OBD library.
    Communicates with ELM327-based adapters via serial/Bluetooth/WiFi.
    """

    # Standard OBD-II PIDs mapping to python-OBD commands
    # Only includes commands that exist in the python-OBD library
    PID_COMMAND_MAP = {
        "0C": obd.commands.RPM,
        "0D": obd.commands.SPEED,
        "05": obd.commands.COOLANT_TEMP,
        "11": obd.commands.THROTTLE_POS,
        "04": obd.commands.ENGINE_LOAD,
        "0B": obd.commands.INTAKE_PRESSURE,
        "06": obd.commands.SHORT_FUEL_TRIM_1,
        "07": obd.commands.LONG_FUEL_TRIM_1,
        "42": obd.commands.CONTROL_MODULE_VOLTAGE,
        "10": obd.commands.MAF,
        "0F": obd.commands.INTAKE_TEMP,
        "14": obd.commands.O2_B1S1,
        "15": obd.commands.O2_B1S2,
        "1C": obd.commands.O2_B2S1,
        "1D": obd.commands.O2_B2S2,
        "1F": obd.commands.RUN_TIME,
        "21": obd.commands.DISTANCE_W_MIL,
        "31": obd.commands.DISTANCE_SINCE_DTC_CLEAR,
        "33": obd.commands.BAROMETRIC_PRESSURE,  # Was ABSOLUTE_BAROMETRIC
        "46": obd.commands.AMBIANT_AIR_TEMP,  # British spelling: AMBIANT
        # "47": obd.commands.ABSOLUTE_THROTTLE_B,  # Not available
        "49": obd.commands.ACCELERATOR_POS_D,
        "4A": obd.commands.ACCELERATOR_POS_E,
        "4B": obd.commands.ACCELERATOR_POS_F,
        "51": obd.commands.FUEL_TYPE,
        "5C": obd.commands.OIL_TEMP,  # Was ENGINE_OIL_TEMP
        # "5D": obd.commands.FUEL_INJECTION_TIMING,  # Not available
        # "5E": obd.commands.ENGINE_FUEL_RATE,  # Not available
        "A2": obd.commands.ETHANOL_PERCENT,
        "A3": obd.commands.HYBRID_BATTERY_REMAINING,
    }

    # PID 0x00, 0x20, 0x40, 0x60, 0x80, 0xA0, 0xC0 for supported PID discovery
    # Only includes commands that exist in the python-OBD library
    SUPPORTED_PID_COMMANDS = [
        obd.commands.PIDS_A,   # PIDs 0x01-0x20
        obd.commands.PIDS_B,   # PIDs 0x21-0x40
        obd.commands.PIDS_C,   # PIDs 0x41-0x60
        obd.commands.PIDS_9A,  # PIDs 0x9A (0x81-0xA0)
    ]

    def __init__(
        self,
        port: str,
        baudrate: int = 38400,
        protocol: str = "AUTO",
        timeout: float = 10.0,
        query_timeout: float = 2.0
    ):
        """
        Initialize real OBD adapter.

        Args:
            port: Serial port (e.g., 'COM3', '/dev/ttyUSB0')
            baudrate: Communication baudrate
            protocol: OBD protocol ('AUTO', '1'-'9', 'A')
            timeout: Connection timeout in seconds
            query_timeout: Query timeout in seconds
        """
        self.port = port
        self.baudrate = baudrate
        self.protocol = protocol
        self.timeout = timeout
        self.query_timeout = query_timeout

        self._connection: Optional[obd.OBD] = None
        self._supported_pids: List[str] = []
        self._pid_info_cache: Dict[str, PIDInfo] = {}
        self._connection_state = ConnectionState.DISCONNECTED
        self._last_error: Optional[str] = None
        self._adapter_type = AdapterType.UNKNOWN

        # Detect adapter type from port name immediately
        self._detect_adapter_type()

        # Statistics
        self._queries_sent = 0
        self._queries_successful = 0
        self._queries_failed = 0
        self._last_query_time: Optional[datetime] = None
        self._connect_time: Optional[datetime] = None

    @property
    def is_connected(self) -> bool:
        """Check if adapter is connected to vehicle."""
        if self._connection is None:
            return False
        return self._connection.status() == OBDStatus.CAR_CONNECTED

    @property
    def connection_state(self) -> ConnectionState:
        """Get current connection state."""
        return self._connection_state

    @property
    def supported_pids(self) -> List[str]:
        """Get list of supported PIDs."""
        return self._supported_pids.copy()

    @property
    def adapter_type(self) -> AdapterType:
        """Get detected adapter type."""
        return self._adapter_type

    @property
    def statistics(self) -> Dict[str, Any]:
        """Get adapter statistics."""
        return {
            "queries_sent": self._queries_sent,
            "queries_successful": self._queries_successful,
            "queries_failed": self._queries_failed,
            "success_rate": (
                self._queries_successful / self._queries_sent
                if self._queries_sent > 0 else 0
            ),
            "last_query_time": self._last_query_time.isoformat() if self._last_query_time else None,
            "connect_time": self._connect_time.isoformat() if self._connect_time else None,
            "uptime_seconds": (
                (datetime.now() - self._connect_time).total_seconds()
                if self._connect_time else 0
            ),
        }

    def connect(self) -> bool:
        """
        Establish connection to ELM327 adapter and vehicle ECU.

        Returns:
            True if connection successful, False otherwise
        """
        self._connection_state = ConnectionState.CONNECTING
        self._last_error = None

        try:
            logger.info(f"Connecting to OBD adapter on {self.port} at {self.baudrate} baud")

            # Create OBD connection
            self._connection = obd.OBD(
                portstr=self.port,
                baudrate=self.baudrate,
                protocol=self.protocol,
                timeout=self.timeout,
                fast=True,  # Use fast mode for better performance
                check_voltage=False,  # Skip voltage check for faster connect
            )

            # Wait for connection to establish
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                status = self._connection.status()
                status_str = str(status)
                if status_str in (str(OBDStatus.CAR_CONNECTED), str(OBDStatus.ELM_CONNECTED)):
                    break
                time.sleep(0.1)

            # Check final status
            status = self._connection.status()
            # OBDStatus values are strings (e.g., "Car Connected", "ELM Connected")
            status_str = str(status)
            if status_str != str(OBDStatus.CAR_CONNECTED):
                self._last_error = f"Failed to connect to vehicle ECU. Status: {status_str}"
                logger.error(self._last_error)
                self._cleanup_connection()
                self._connection_state = ConnectionState.ERROR
                return False

            # Detect adapter type from port
            self._detect_adapter_type()

            # Discover supported PIDs
            self._discover_supported_pids()

            # Cache PID info
            self._cache_pid_info()

            self._connection_state = ConnectionState.CONNECTED
            self._connect_time = datetime.now()
            logger.info(f"Successfully connected to vehicle. Supported PIDs: {len(self._supported_pids)}")
            return True

        except Exception as e:
            self._last_error = f"Connection error: {str(e)}"
            logger.error(self._last_error)
            self._cleanup_connection()
            self._connection_state = ConnectionState.ERROR
            return False

    def _detect_adapter_type(self):
        """Detect adapter type from port name."""
        port_lower = self.port.lower()
        if port_lower.startswith("com"):
            self._adapter_type = AdapterType.USB
        elif "bluetooth" in port_lower or "bt" in port_lower:
            self._adapter_type = AdapterType.BLUETOOTH
        elif "wifi" in port_lower or "tcp" in port_lower:
            self._adapter_type = AdapterType.WIFI
        else:
            self._adapter_type = AdapterType.UNKNOWN

    def _discover_supported_pids(self):
        """Discover which PIDs are supported by the vehicle."""
        self._supported_pids = []

        if self._connection is None:
            return

        # Query supported PID groups (0x00, 0x20, 0x40, 0x60, 0x80, 0xA0, 0xC0)
        for cmd in self.SUPPORTED_PID_COMMANDS:
            try:
                response = self._connection.query(cmd, timeout=self.query_timeout)
                if response and not response.is_null():
                    # Parse supported PIDs from response
                    # python-OBD returns a list of supported command objects
                    if hasattr(response.value, '__iter__'):
                        for supported_cmd in response.value:
                            if hasattr(supported_cmd, 'pid'):
                                pid_hex = f"{supported_cmd.pid:02X}"
                                self._supported_pids.append(pid_hex)
            except Exception as e:
                logger.debug(f"Error querying {cmd.name}: {e}")
                continue

        # Also check individual PIDs we care about
        for pid_hex, cmd in self.PID_COMMAND_MAP.items():
            if pid_hex not in self._supported_pids:
                try:
                    response = self._connection.query(cmd, timeout=self.query_timeout)
                    if response and not response.is_null() and response.value is not None:
                        self._supported_pids.append(pid_hex)
                except Exception:
                    pass

        # Deduplicate
        self._supported_pids = list(set(self._supported_pids))
        logger.info(f"Discovered {len(self._supported_pids)} supported PIDs")

    def _cache_pid_info(self):
        """Cache PID information for supported PIDs."""
        for pid_hex in self._supported_pids:
            if pid_hex in self.PID_COMMAND_MAP:
                cmd = self.PID_COMMAND_MAP[pid_hex]
                # Handle commands that may not have unit/desc attributes
                unit = ""
                if hasattr(cmd, 'unit') and cmd.unit:
                    unit = str(cmd.unit)
                description = ""
                if hasattr(cmd, 'desc') and cmd.desc:
                    description = cmd.desc
                self._pid_info_cache[pid_hex] = PIDInfo(
                    pid=pid_hex,
                    name=getattr(cmd, 'name', pid_hex),
                    unit=unit,
                    description=description,
                    is_supported=True
                )

    def _cleanup_connection(self):
        """Clean up connection resources."""
        if self._connection:
            try:
                self._connection.close()
            except Exception as e:
                logger.debug(f"Error closing connection: {e}")
            self._connection = None
        self._supported_pids = []
        self._pid_info_cache = {}
        self._connect_time = None

    def disconnect(self):
        """Disconnect from adapter."""
        logger.info("Disconnecting from OBD adapter")
        self._cleanup_connection()
        self._connection_state = ConnectionState.DISCONNECTED

    def query_pid(self, pid: str) -> Optional[float]:
        """
        Query a single PID value.

        Args:
            pid: PID in hex format (e.g., '0C' for RPM)

        Returns:
            PID value as float, or None if failed
        """
        if not self.is_connected:
            logger.warning("Cannot query PID - not connected to vehicle")
            return None

        if pid not in self.PID_COMMAND_MAP:
            logger.warning(f"Unknown PID: {pid}")
            return None

        if pid not in self._supported_pids:
            logger.debug(f"PID {pid} not in supported list, attempting anyway")

        self._queries_sent += 1
        self._last_query_time = datetime.now()

        try:
            cmd = self.PID_COMMAND_MAP[pid]
            response = self._connection.query(cmd, timeout=self.query_timeout)

            if response and not response.is_null() and response.value is not None:
                self._queries_successful += 1

                # Convert to float with proper unit handling
                value = self._convert_response_value(response.value, pid)
                return value
            else:
                self._queries_failed += 1
                logger.debug(f"PID {pid} query returned null/empty")
                return None

        except Exception as e:
            self._queries_failed += 1
            logger.error(f"Error querying PID {pid}: {e}")
            return None

    def _convert_response_value(self, value: Any, pid: str) -> float:
        """Convert python-OBD response value to float with correct units."""
        try:
            # python-OBD returns Quantity objects with magnitude and units
            if hasattr(value, 'magnitude'):
                # Convert to standard units
                if pid == "0C":  # RPM
                    return float(value.to(Unit.rpm).magnitude)
                elif pid == "0D":  # Speed
                    return float(value.to(Unit.kph).magnitude)
                elif pid == "05":  # Coolant temp
                    return float(value.to(Unit.celsius).magnitude)
                elif pid in ("11", "04", "06", "07"):  # Percentages
                    return float(value.to(Unit.percent).magnitude)
                elif pid == "0B":  # Intake pressure / MAP
                    return float(value.to(Unit.kpa).magnitude)
                elif pid == "42":  # Voltage
                    return float(value.to(Unit.volt).magnitude)
                elif pid == "10":  # MAF
                    return float(value.to(Unit.gram_per_second).magnitude)
                elif pid == "0F":  # Intake temp
                    return float(value.to(Unit.celsius).magnitude)
                elif pid in ("14", "15", "1C", "1D"):  # O2 sensors
                    return float(value.to(Unit.volt).magnitude)
                elif pid == "1F":  # Run time
                    return float(value.to(Unit.second).magnitude)
                elif pid in ("21", "31"):  # Distance
                    return float(value.to(Unit.kilometer).magnitude)
                elif pid == "33":  # Barometric pressure
                    return float(value.to(Unit.kpa).magnitude)
                elif pid == "46":  # Ambient temp
                    return float(value.to(Unit.celsius).magnitude)
                elif pid in ("47", "49", "4A", "4B"):  # Throttle/accelerator
                    return float(value.to(Unit.percent).magnitude)
                elif pid == "51":  # Fuel type
                    return float(value.magnitude)
                elif pid == "5C":  # Oil temp
                    return float(value.to(Unit.celsius).magnitude)
                elif pid == "5D":  # Injection timing
                    return float(value.to(Unit.degree).magnitude)
                elif pid == "5E":  # Fuel rate
                    return float(value.to(Unit.liter_per_hour).magnitude)
                elif pid == "A2":  # Ethanol %
                    return float(value.to(Unit.percent).magnitude)
                elif pid == "A3":  # Hybrid battery
                    return float(value.to(Unit.percent).magnitude)
                else:
                    return float(value.magnitude)
            else:
                return float(value)
        except Exception as e:
            logger.error(f"Error converting value for PID {pid}: {e}")
            return 0.0

    def query_multiple_pids(self, pids: List[str]) -> Dict[str, Optional[float]]:
        """
        Query multiple PIDs efficiently.

        Args:
            pids: List of PID hex strings

        Returns:
            Dictionary mapping PID to value (or None)
        """
        results = {}
        for pid in pids:
            results[pid] = self.query_pid(pid)
        return results

    def get_all_readings(self) -> Dict[str, SensorReading]:
        """
        Get all current sensor readings as SensorReading objects.

        Returns:
            Dictionary mapping sensor keys to SensorReading objects
        """
        readings = {}
        timestamp = datetime.now()

        # PID to sensor key mapping (matching simulation engine)
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

        # Query all supported PIDs we care about
        pids_to_query = [pid for pid in pid_to_sensor.keys() if pid in self._supported_pids]
        values = self.query_multiple_pids(pids_to_query)

        for pid, (key, name, unit) in pid_to_sensor.items():
            if pid in values and values[pid] is not None:
                readings[key] = SensorReading(
                    pid=pid,
                    name=name,
                    value=values[pid],
                    unit=unit,
                    timestamp=timestamp,
                    is_simulated=False
                )

        return readings

    def scan_dtcs(self) -> List[DTC]:
        """
        Scan for diagnostic trouble codes.

        Returns:
            List of DTC objects
        """
        if not self.is_connected:
            logger.warning("Cannot scan DTCs - not connected to vehicle")
            return []

        dtcs = []

        try:
            # Mode $03 - Current DTCs
            response = self._connection.query(obd.commands.GET_DTC, timeout=self.query_timeout)
            if response and not response.is_null() and response.value:
                for dtc_tuple in response.value:
                    if len(dtc_tuple) >= 2:
                        code, description = dtc_tuple[0], dtc_tuple[1]
                        severity = self._determine_dtc_severity(code)
                        dtcs.append(DTC(
                            code=code,
                            description=description,
                            severity=severity,
                            status="active",
                            is_demo=False
                        ))

            # Mode $07 - Pending DTCs (python-OBD uses GET_CURRENT_DTC for this)
            if hasattr(obd.commands, 'GET_CURRENT_DTC'):
                response = self._connection.query(obd.commands.GET_CURRENT_DTC, timeout=self.query_timeout)
                if response and not response.is_null() and response.value:
                    for dtc_tuple in response.value:
                        if len(dtc_tuple) >= 2:
                            code, description = dtc_tuple[0], dtc_tuple[1]
                            # Check if already in list
                            if not any(d.code == code for d in dtcs):
                                severity = self._determine_dtc_severity(code)
                                dtcs.append(DTC(
                                    code=code,
                                    description=description,
                                    severity=severity,
                                    status="pending",
                                    is_demo=False
                                ))

            # Note: Permanent DTCs (Mode $0A) not available in python-OBD

            logger.info(f"Found {len(dtcs)} DTC(s)")
            return dtcs

        except Exception as e:
            logger.error(f"Error scanning DTCs: {e}")
            return []

    def _determine_dtc_severity(self, code: str) -> str:
        """Determine DTC severity based on code prefix."""
        if code.startswith("P0") or code.startswith("P2"):
            # Powertrain - check specific codes
            critical_codes = ["P0217", "P0300", "P0301", "P0302", "P0303", "P0304"]
            if code in critical_codes:
                return "critical"
            return "major"
        elif code.startswith("B0") or code.startswith("B1"):
            # Body
            return "minor"
        elif code.startswith("C0") or code.startswith("C1"):
            # Chassis
            return "major"
        elif code.startswith("U0") or code.startswith("U1"):
            # Network
            return "major"
        return "info"

    def clear_dtcs(self) -> bool:
        """
        Clear diagnostic trouble codes.

        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected:
            logger.warning("Cannot clear DTCs - not connected to vehicle")
            return False

        try:
            response = self._connection.query(obd.commands.CLEAR_DTC, timeout=self.query_timeout)
            if response and not response.is_null():
                logger.info("DTCs cleared successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Error clearing DTCs: {e}")
            return False

    def get_freeze_frame(self, dtc_code: str) -> Optional[FreezeFrameData]:
        """
        Get freeze frame data for a specific DTC.

        Args:
            dtc_code: DTC code (e.g., 'P0300')

        Returns:
            FreezeFrameData object or None
        """
        if not self.is_connected:
            return None

        try:
            # Mode $02 - Freeze frame data
            # Note: python-OBD doesn't have a direct freeze frame command for specific DTC
            # This would require raw mode $02 queries which vary by manufacturer
            # For now, return current readings as proxy
            readings = self.get_all_readings()

            return FreezeFrameData(
                dtc_code=dtc_code,
                rpm=readings.get("rpm", SensorReading("", "", 0, "", timestamp=datetime.now())).value,
                speed_kmh=readings.get("speed_kmh", SensorReading("", "", 0, "", timestamp=datetime.now())).value,
                coolant_temp_c=readings.get("coolant_temp_c", SensorReading("", "", 0, "", timestamp=datetime.now())).value,
                throttle_pos_pct=readings.get("throttle_pos_pct", SensorReading("", "", 0, "", timestamp=datetime.now())).value,
                engine_load_pct=readings.get("engine_load_pct", SensorReading("", "", 0, "", timestamp=datetime.now())).value,
                map_kpa=readings.get("intake_pressure_kpa", SensorReading("", "", 0, "", timestamp=datetime.now())).value,
                maf_g_s=readings.get("maf_g_s", SensorReading("", "", 0, "", timestamp=datetime.now())).value,
            )
        except Exception as e:
            logger.error(f"Error getting freeze frame for {dtc_code}: {e}")
            return None

    def get_vin(self) -> Optional[str]:
        """Get Vehicle Identification Number."""
        if not self.is_connected:
            return None
        try:
            response = self._connection.query(obd.commands.VIN, timeout=self.query_timeout)
            if response and not response.is_null() and response.value:
                return str(response.value).strip()
        except Exception as e:
            logger.debug(f"VIN not available: {e}")
        return None

    def get_calid(self) -> Optional[str]:
        """Get Calibration ID."""
        if not self.is_connected:
            return None
        try:
            response = self._connection.query(obd.commands.CALIBRATION_ID, timeout=self.query_timeout)
            if response and not response.is_null() and response.value:
                return str(response.value).strip()
        except Exception as e:
            logger.debug(f"CALID not available: {e}")
        return None

    def get_cvn(self) -> Optional[str]:
        """Get Calibration Verification Number."""
        if not self.is_connected:
            return None
        try:
            response = self._connection.query(obd.commands.CVN, timeout=self.query_timeout)
            if response and not response.is_null() and response.value:
                return str(response.value).strip()
        except Exception as e:
            logger.debug(f"CVN not available: {e}")
        return None

    def get_ecu_name(self) -> Optional[str]:
        """Get ECU name."""
        if not self.is_connected:
            return None
        try:
            response = self._connection.query(obd.commands.ECU_NAME, timeout=self.query_timeout)
            if response and not response.is_null() and response.value:
                return str(response.value).strip()
        except Exception as e:
            logger.debug(f"ECU name not available: {e}")
        return None

    def get_fuel_system_status(self) -> Optional[str]:
        """Get fuel system status."""
        if not self.is_connected:
            return None
        try:
            response = self._connection.query(obd.commands.FUEL_STATUS, timeout=self.query_timeout)
            if response and not response.is_null() and response.value:
                return str(response.value)
        except Exception as e:
            logger.debug(f"Fuel status not available: {e}")
        return None

    def get_runtime(self) -> Optional[float]:
        """Get engine runtime in seconds."""
        if not self.is_connected:
            return None
        try:
            response = self._connection.query(obd.commands.RUN_TIME, timeout=self.query_timeout)
            if response and not response.is_null() and response.value:
                return float(response.value.to(Unit.second).magnitude)
        except Exception as e:
            logger.debug(f"Runtime not available: {e}")
        return None

    def health_check(self) -> Dict[str, Any]:
        """
        Perform connection health check.

        Returns:
            Dictionary with health status
        """
        # OBDStatus values are strings (e.g., "Car Connected", "ELM Connected")
        status_str = str(self._connection.status()) if self._connection else "NO_CONNECTION"
        health = {
            "connected": self.is_connected,
            "status": status_str,
            "port": self.port,
            "baudrate": self.baudrate,
            "protocol": self.protocol,
            "supported_pids_count": len(self._supported_pids),
            "statistics": self.statistics,
            "timestamp": datetime.now().isoformat()
        }

        if self.is_connected:
            # Test a simple query
            test_value = self.query_pid("0C")  # RPM
            health["query_test"] = "passed" if test_value is not None else "failed"
        else:
            health["query_test"] = "not_connected"

        return health

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False
"""
i20 AI Garage - PID Registry

Standard OBD-II PID definitions with supported PID detection,
units, descriptions, query priorities, and polling intervals.
"""

import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class PIDPriority(Enum):
    """PID polling priority levels."""
    CRITICAL = "critical"   # 10 Hz - RPM, Speed, Coolant
    HIGH = "high"           # 5 Hz  - Throttle, Load, MAP
    MEDIUM = "medium"       # 2 Hz  - Fuel trims, Voltage, MAF
    LOW = "low"             # 1 Hz  - O2, catalyst, EVAP


@dataclass
class PIDDefinition:
    """Standard OBD-II PID definition."""
    pid: str                 # Hex PID (e.g., "0C")
    sensor_key: str          # Internal sensor key (e.g., "rpm")
    name: str                # Display name
    unit: str                # Display unit
    description: str         # Full description
    priority: PIDPriority    # Polling priority
    min_value: float         # Minimum expected value
    max_value: float         # Maximum expected value
    formula: str = ""        # Human-readable conversion formula
    is_active: bool = True   # Whether actively polled


@dataclass
class PIDValue:
    """A PID reading with metadata."""
    pid: str
    sensor_key: str
    value: Optional[float]
    unit: str
    timestamp: datetime
    success: bool
    error: Optional[str] = None


class PIDRegistry:
    """
    Registry of standard OBD-II PIDs with:
    - Standard PID definitions (mode 01)
    - Supported PID detection from bit-encoded responses
    - Query priority groups with polling intervals
    - Per-PID statistics and last-known values
    """

    # Standard PID definitions for Hyundai i20 (Kappa 1.2L petrol)
    STANDARD_PIDS = {
        "0C": PIDDefinition(
            pid="0C", sensor_key="rpm", name="Engine RPM", unit="RPM",
            description="Engine crankshaft rotational speed",
            priority=PIDPriority.CRITICAL,
            min_value=0, max_value=8000,
            formula="((A*256)+B)/4"
        ),
        "0D": PIDDefinition(
            pid="0D", sensor_key="speed_kmh", name="Vehicle Speed", unit="km/h",
            description="Vehicle road speed",
            priority=PIDPriority.CRITICAL,
            min_value=0, max_value=255,
            formula="A"
        ),
        "05": PIDDefinition(
            pid="05", sensor_key="coolant_temp_c", name="Coolant Temperature", unit="°C",
            description="Engine coolant temperature",
            priority=PIDPriority.CRITICAL,
            min_value=-40, max_value=215,
            formula="A-40"
        ),
        "11": PIDDefinition(
            pid="11", sensor_key="throttle_pos_pct", name="Throttle Position", unit="%",
            description="Absolute throttle position",
            priority=PIDPriority.HIGH,
            min_value=0, max_value=100,
            formula="A*100/255"
        ),
        "04": PIDDefinition(
            pid="04", sensor_key="engine_load_pct", name="Engine Load", unit="%",
            description="Calculated engine load",
            priority=PIDPriority.HIGH,
            min_value=0, max_value=100,
            formula="A*100/255"
        ),
        "0B": PIDDefinition(
            pid="0B", sensor_key="intake_pressure_kpa", name="Intake Manifold Pressure", unit="kPa",
            description="Intake manifold absolute pressure (MAP)",
            priority=PIDPriority.HIGH,
            min_value=0, max_value=255,
            formula="A"
        ),
        "06": PIDDefinition(
            pid="06", sensor_key="stft_b1_pct", name="Short Term Fuel Trim B1", unit="%",
            description="Short term fuel trim, bank 1",
            priority=PIDPriority.MEDIUM,
            min_value=-100, max_value=99.2,
            formula="(A-128)*100/128"
        ),
        "07": PIDDefinition(
            pid="07", sensor_key="ltft_b1_pct", name="Long Term Fuel Trim B1", unit="%",
            description="Long term fuel trim, bank 1",
            priority=PIDPriority.MEDIUM,
            min_value=-100, max_value=99.2,
            formula="(A-128)*100/128"
        ),
        "42": PIDDefinition(
            pid="42", sensor_key="voltage_v", name="Control Module Voltage", unit="V",
            description="ECU supply voltage",
            priority=PIDPriority.MEDIUM,
            min_value=0, max_value=65.535,
            formula="((A*256)+B)/1000"
        ),
        "10": PIDDefinition(
            pid="10", sensor_key="maf_g_s", name="MAF Air Flow", unit="g/s",
            description="Mass air flow sensor rate",
            priority=PIDPriority.MEDIUM,
            min_value=0, max_value=655.35,
            formula="((A*256)+B)/100"
        ),
        "0F": PIDDefinition(
            pid="0F", sensor_key="intake_temp_c", name="Intake Air Temperature", unit="°C",
            description="Intake air temperature",
            priority=PIDPriority.MEDIUM,
            min_value=-40, max_value=215,
            formula="A-40"
        ),
        "14": PIDDefinition(
            pid="14", sensor_key="o2_b1s1_v", name="O2 Sensor B1S1", unit="V",
            description="Oxygen sensor bank 1 sensor 1 voltage",
            priority=PIDPriority.LOW,
            min_value=0, max_value=1.275,
            formula="A/200"
        ),
        "15": PIDDefinition(
            pid="15", sensor_key="o2_b1s2_v", name="O2 Sensor B1S2", unit="V",
            description="Oxygen sensor bank 1 sensor 2 voltage",
            priority=PIDPriority.LOW,
            min_value=0, max_value=1.275,
            formula="A/200"
        ),
        "1F": PIDDefinition(
            pid="1F", sensor_key="runtime_s", name="Engine Runtime", unit="s",
            description="Time since engine start",
            priority=PIDPriority.LOW,
            min_value=0, max_value=65535,
            formula="(A*256)+B"
        ),
        "21": PIDDefinition(
            pid="21", sensor_key="distance_with_mil_km", name="Distance with MIL", unit="km",
            description="Distance traveled with MIL on",
            priority=PIDPriority.LOW,
            min_value=0, max_value=65535,
            formula="(A*256)+B"
        ),
        "31": PIDDefinition(
            pid="31", sensor_key="distance_since_clear_km", name="Distance Since DTC Clear", unit="km",
            description="Distance since trouble codes cleared",
            priority=PIDPriority.LOW,
            min_value=0, max_value=65535,
            formula="(A*256)+B"
        ),
        "33": PIDDefinition(
            pid="33", sensor_key="barometric_kpa", name="Barometric Pressure", unit="kPa",
            description="Absolute barometric pressure",
            priority=PIDPriority.LOW,
            min_value=0, max_value=255,
            formula="A"
        ),
        "46": PIDDefinition(
            pid="46", sensor_key="ambient_temp_c", name="Ambient Air Temperature", unit="°C",
            description="Outside air temperature",
            priority=PIDPriority.LOW,
            min_value=-40, max_value=215,
            formula="A-40"
        ),
        "5C": PIDDefinition(
            pid="5C", sensor_key="oil_temp_c", name="Engine Oil Temperature", unit="°C",
            description="Engine oil temperature",
            priority=PIDPriority.LOW,
            min_value=-40, max_value=210,
            formula="A-40"
        ),
    }

    # Polling intervals per priority (seconds)
    PRIORITY_INTERVALS = {
        PIDPriority.CRITICAL: 0.1,   # 10 Hz
        PIDPriority.HIGH: 0.2,       # 5 Hz
        PIDPriority.MEDIUM: 0.5,     # 2 Hz
        PIDPriority.LOW: 1.0,        # 1 Hz
    }

    def __init__(self):
        """Initialize PID registry."""
        self._supported_pids: List[str] = []
        self._unsupported_pids: List[str] = []
        self._last_values: Dict[str, PIDValue] = {}
        self._last_poll_times: Dict[str, float] = {}
        self._pid_stats: Dict[str, Dict[str, Any]] = {}
        self._detection_time: Optional[datetime] = None

        # Initialize stats for all standard PIDs
        for pid, definition in self.STANDARD_PIDS.items():
            self._pid_stats[pid] = {
                "queries": 0,
                "successes": 0,
                "failures": 0,
                "last_success": None,
                "last_failure": None,
            }

    @property
    def supported_pids(self) -> List[str]:
        """Get list of supported PIDs."""
        return self._supported_pids.copy()

    @property
    def unsupported_pids(self) -> List[str]:
        """Get list of standard PIDs NOT supported by the vehicle."""
        return self._unsupported_pids.copy()

    @property
    def detection_complete(self) -> bool:
        """Check if PID detection has been performed."""
        return self._detection_time is not None

    @property
    def detection_time(self) -> Optional[datetime]:
        """Get when PID detection was last performed."""
        return self._detection_time

    def get_definition(self, pid: str) -> Optional[PIDDefinition]:
        """Get PID definition by hex PID."""
        return self.STANDARD_PIDS.get(pid)

    def get_definition_by_sensor_key(self, sensor_key: str) -> Optional[PIDDefinition]:
        """Get PID definition by internal sensor key."""
        for definition in self.STANDARD_PIDS.values():
            if definition.sensor_key == sensor_key:
                return definition
        return None

    def get_pid_for_sensor(self, sensor_key: str) -> Optional[str]:
        """Get PID hex for an internal sensor key."""
        definition = self.get_definition_by_sensor_key(sensor_key)
        return definition.pid if definition else None

    def set_supported_pids(self, pids: List[str]):
        """
        Set the supported PID list from detection results.

        Args:
            pids: List of supported PID hex strings
        """
        self._supported_pids = [p.upper() for p in pids]
        self._unsupported_pids = [
            pid for pid in self.STANDARD_PIDS
            if pid not in self._supported_pids
        ]
        self._detection_time = datetime.now()
        logger.info(
            f"PID registry updated: {len(self._supported_pids)} supported, "
            f"{len(self._unsupported_pids)} unsupported"
        )

    def is_supported(self, pid: str) -> bool:
        """Check if a PID is supported (after detection)."""
        if not self.detection_complete:
            # Before detection, assume all standard PIDs are queryable
            return pid in self.STANDARD_PIDS
        return pid in self._supported_pids

    def is_sensor_supported(self, sensor_key: str) -> bool:
        """Check if a sensor's PID is supported."""
        pid = self.get_pid_for_sensor(sensor_key)
        return pid is not None and self.is_supported(pid)

    def get_pids_by_priority(self, priority: PIDPriority) -> List[PIDDefinition]:
        """Get all supported PID definitions for a priority level."""
        return [
            d for d in self.STANDARD_PIDS.values()
            if d.priority == priority and self.is_supported(d.pid) and d.is_active
        ]

    def get_active_pids(self) -> List[PIDDefinition]:
        """Get all supported, active PID definitions."""
        return [
            d for d in self.STANDARD_PIDS.values()
            if self.is_supported(d.pid) and d.is_active
        ]

    def should_poll(self, pid: str, current_time: Optional[float] = None) -> bool:
        """
        Check if a PID is due for polling based on its priority interval.

        Args:
            pid: PID hex string
            current_time: Current monotonic time (defaults to time.monotonic())

        Returns:
            True if the PID should be polled now
        """
        if not self.is_supported(pid):
            return False

        definition = self.STANDARD_PIDS.get(pid)
        if not definition or not definition.is_active:
            return False

        now = current_time if current_time is not None else time.monotonic()
        interval = self.PRIORITY_INTERVALS[definition.priority]
        last_poll = self._last_poll_times.get(pid, 0.0)
        return (now - last_poll) >= interval

    def mark_polled(self, pid: str, current_time: Optional[float] = None):
        """Mark a PID as polled at the current time."""
        now = current_time if current_time is not None else time.monotonic()
        self._last_poll_times[pid] = now

    def record_result(self, value: PIDValue):
        """
        Record a PID query result.

        Args:
            value: PIDValue with result metadata
        """
        self._last_values[value.pid] = value

        stats = self._pid_stats.get(value.pid)
        if stats:
            stats["queries"] += 1
            if value.success:
                stats["successes"] += 1
                stats["last_success"] = value.timestamp.isoformat()
            else:
                stats["failures"] += 1
                stats["last_failure"] = value.timestamp.isoformat()

    def get_last_value(self, pid: str) -> Optional[PIDValue]:
        """Get last recorded value for a PID."""
        return self._last_values.get(pid)

    def get_last_value_by_sensor(self, sensor_key: str) -> Optional[PIDValue]:
        """Get last recorded value for a sensor key."""
        pid = self.get_pid_for_sensor(sensor_key)
        return self._last_values.get(pid) if pid else None

    def get_pid_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get per-PID query statistics."""
        return {
            pid: stats.copy() for pid, stats in self._pid_stats.items()
        }

    def get_registry_summary(self) -> Dict[str, Any]:
        """Get summary of registry state."""
        by_priority = {}
        for priority in PIDPriority:
            pids = self.get_pids_by_priority(priority)
            by_priority[priority.value] = {
                "count": len(pids),
                "interval_s": self.PRIORITY_INTERVALS[priority],
                "pids": [d.pid for d in pids],
                "sensor_keys": [d.sensor_key for d in pids],
            }

        total_queries = sum(s["queries"] for s in self._pid_stats.values())
        total_successes = sum(s["successes"] for s in self._pid_stats.values())

        return {
            "detection_complete": self.detection_complete,
            "detection_time": self.detection_time.isoformat() if self.detection_time else None,
            "standard_pid_count": len(self.STANDARD_PIDS),
            "supported_count": len(self._supported_pids),
            "unsupported_count": len(self._unsupported_pids),
            "unsupported_pids": self._unsupported_pids,
            "by_priority": by_priority,
            "total_queries": total_queries,
            "overall_success_rate": (
                total_successes / total_queries if total_queries > 0 else 0.0
            ),
        }

    def validate_value(self, pid: str, value: float) -> Tuple[bool, Optional[float]]:
        """
        Validate a PID value against expected range.

        Args:
            pid: PID hex string
            value: Value to validate

        Returns:
            Tuple of (is_valid, clamped_value)
        """
        definition = self.STANDARD_PIDS.get(pid)
        if not definition:
            return True, value

        if definition.min_value <= value <= definition.max_value:
            return True, value

        # Clamp to range
        clamped = max(definition.min_value, min(definition.max_value, value))
        logger.debug(
            f"PID {pid} value {value} out of range "
            f"[{definition.min_value}, {definition.max_value}], clamped to {clamped}"
        )
        return False, clamped

    def set_pid_active(self, pid: str, active: bool):
        """Enable or disable polling for a PID."""
        definition = self.STANDARD_PIDS.get(pid)
        if definition:
            definition.is_active = active
            logger.info(f"PID {pid} ({definition.name}) {'enabled' if active else 'disabled'}")

    def reset_statistics(self):
        """Reset all PID statistics."""
        for stats in self._pid_stats.values():
            stats["queries"] = 0
            stats["successes"] = 0
            stats["failures"] = 0
            stats["last_success"] = None
            stats["last_failure"] = None
        self._last_values.clear()
        self._last_poll_times.clear()

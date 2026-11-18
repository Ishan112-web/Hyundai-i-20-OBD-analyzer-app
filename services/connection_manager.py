"""
i20 AI Garage - Connection Manager

Manages OBD adapter connections with auto-detection, reconnection,
and connection lifecycle management.
"""

import logging
import time
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from pathlib import Path
from queue import Queue, Empty
import json

import serial.tools.list_ports

from config import OBD_REAL_CONFIG
from services.real_obd_adapter import RealOBDAdapter, ConnectionProfile, AdapterType
from services.types import ConnectionState, OBDMode

logger = logging.getLogger(__name__)


@dataclass
class ConnectionAttempt:
    """Record of a connection attempt."""
    timestamp: datetime
    port: str
    baudrate: int
    protocol: str
    success: bool
    error_message: Optional[str] = None
    duration_ms: float = 0.0


@dataclass
class PortInfo:
    """Serial port information."""
    device: str
    name: str
    description: str
    hwid: str
    vid: Optional[int] = None
    pid: Optional[int] = None
    manufacturer: Optional[str] = None
    product: Optional[str] = None
    serial_number: Optional[str] = None
    is_likely_obd: bool = False


class ConnectionManager:
    """
    Manages OBD connections with:
    - Auto port detection
    - Multi-baudrate/protocol trial
    - Connection pooling/profiles
    - Background health monitoring
    - Exponential backoff reconnection
    - Connection event logging
    """

    def __init__(
        self,
        profiles_file: Optional[str] = None,
        health_check_interval: int = 30,
        on_status_change: Optional[Callable[[ConnectionState], None]] = None,
        on_connection_log: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        """
        Initialize connection manager.

        Args:
            profiles_file: Path to JSON file for saving connection profiles
            health_check_interval: Health check interval in seconds
            on_status_change: Callback when connection state changes
            on_connection_log: Callback for connection events
        """
        self.profiles_file = profiles_file or "data/connection_profiles.json"
        self.health_check_interval = health_check_interval
        self.on_status_change = on_status_change
        self.on_connection_log = on_connection_log

        # Current connection
        self._adapter: Optional[RealOBDAdapter] = None
        self._connection_state = ConnectionState.DISCONNECTED
        self._current_profile: Optional[ConnectionProfile] = None

        # Saved profiles
        self._profiles: Dict[str, ConnectionProfile] = {}

        # Reconnection state
        self._reconnect_enabled = True
        self._reconnect_thread: Optional[threading.Thread] = None
        self._reconnect_stop_event = threading.Event()
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        self._reconnect_backoff = [1, 2, 5, 10, 30]  # seconds

        # Health monitoring
        self._health_thread: Optional[threading.Thread] = None
        self._health_stop_event = threading.Event()
        self._last_health_check: Optional[datetime] = None
        self._health_history: List[Dict[str, Any]] = []
        self._max_health_history = 100

        # Connection attempt history
        self._attempt_history: List[ConnectionAttempt] = []
        self._max_attempt_history = 50

        # Thread safety
        self._lock = threading.RLock()

        # Load saved profiles
        self._load_profiles()

        logger.info("ConnectionManager initialized")

    @property
    def connection_state(self) -> ConnectionState:
        """Get current connection state."""
        with self._lock:
            if self._adapter and self._adapter.is_connected:
                return ConnectionState.CONNECTED
            return self._connection_state

    @property
    def adapter(self) -> Optional[RealOBDAdapter]:
        """Get current adapter instance."""
        with self._lock:
            return self._adapter

    @property
    def current_profile(self) -> Optional[ConnectionProfile]:
        """Get current connection profile."""
        with self._lock:
            return self._current_profile

    def discover_ports(self) -> List[PortInfo]:
        """
        Discover available serial ports and identify likely OBD adapters.

        Returns:
            List of PortInfo objects
        """
        ports = []

        for port in serial.tools.list_ports.comports():
            # Determine if likely OBD adapter
            is_likely = self._is_likely_obd_adapter(port)

            port_info = PortInfo(
                device=port.device,
                name=port.name or port.device,
                description=port.description or "",
                hwid=port.hwid or "",
                vid=port.vid,
                pid=port.pid,
                manufacturer=port.manufacturer,
                product=port.product,
                serial_number=port.serial_number,
                is_likely_obd=is_likely
            )
            ports.append(port_info)

        # Sort: likely OBD adapters first
        ports.sort(key=lambda p: (not p.is_likely_obd, p.device))

        logger.info(f"Discovered {len(ports)} serial ports, {sum(1 for p in ports if p.is_likely_obd)} likely OBD")
        return ports

    def _is_likely_obd_adapter(self, port) -> bool:
        """Check if a serial port is likely an OBD adapter."""
        # Common ELM327 VID/PID combinations
        known_vids = {
            0x0403: "FTDI",       # FTDI chips (common in ELM327)
            0x10C4: "Silicon Labs",  # CP210x
            0x1A86: "QinHeng",    # CH340
            0x067B: "Prolific",   # PL2303
            0x04D8: "Microchip",  # MCP2200
        }

        # Check VID/PID
        if port.vid and port.vid in known_vids:
            return True

        # Check description for keywords
        desc = (port.description or "").lower()
        obd_keywords = [
            "elm327", "obd", "obdii", "obd-ii",
            "elm", "diagnostic", "scan", "obd2",
            "bluetooth", "bt", "ble", "wifi", "tcp"
        ]
        if any(kw in desc for kw in obd_keywords):
            return True

        # Check manufacturer/product
        mfr = (port.manufacturer or "").lower()
        prod = (port.product or "").lower()
        if any(kw in mfr for kw in obd_keywords):
            return True
        if any(kw in prod for kw in obd_keywords):
            return True

        return False

    def connect(
        self,
        port: str,
        baudrate: int = 38400,
        protocol: str = "AUTO",
        timeout: float = 10.0,
        query_timeout: float = 2.0,
        save_profile: bool = True,
        profile_name: str = ""
    ) -> bool:
        """
        Connect to OBD adapter.

        Args:
            port: Serial port
            baudrate: Baud rate
            protocol: OBD protocol
            timeout: Connection timeout
            query_timeout: Query timeout
            save_profile: Whether to save as profile
            profile_name: Friendly name for profile

        Returns:
            True if connection successful
        """
        with self._lock:
            # Disconnect existing if any
            if self._adapter:
                self.disconnect()

            self._connection_state = ConnectionState.CONNECTING
            self._notify_status_change()
            start_time = time.time()

            # Create adapter
            self._adapter = RealOBDAdapter(
                port=port,
                baudrate=baudrate,
                protocol=protocol,
                timeout=timeout,
                query_timeout=query_timeout
            )

            # Attempt connection
            success = self._adapter.connect()
            duration_ms = (time.time() - start_time) * 1000

            # Record attempt
            attempt = ConnectionAttempt(
                timestamp=datetime.now(),
                port=port,
                baudrate=baudrate,
                protocol=protocol,
                success=success,
                error_message=self._adapter._last_error if not success else None,
                duration_ms=duration_ms
            )
            self._add_attempt(attempt)

            if success:
                self._connection_state = ConnectionState.CONNECTED
                self._reconnect_attempts = 0

                # Save/update profile
                if save_profile:
                    self._save_profile(port, baudrate, protocol, profile_name)

                # Start health monitoring
                self._start_health_monitoring()

                logger.info(f"Connected to {port} at {baudrate} baud")
            else:
                self._connection_state = ConnectionState.ERROR
                logger.error(f"Failed to connect: {attempt.error_message}")

            self._notify_status_change()
            self._log_connection_event(
                "connect" if success else "error",
                port, baudrate, protocol,
                attempt.error_message or "Connected successfully"
            )

            return success

    def auto_connect(self, timeout: float = 10.0) -> bool:
        """
        Automatically discover and connect to OBD adapter.
        Tries saved profiles first, then discovered ports.

        Args:
            timeout: Connection timeout per attempt

        Returns:
            True if connected successfully
        """
        logger.info("Starting auto-connect sequence")

        # Try saved profiles first (most recent first)
        sorted_profiles = sorted(
            self._profiles.values(),
            key=lambda p: p.last_connected or datetime.min,
            reverse=True
        )

        for profile in sorted_profiles:
            if profile.success_count > profile.failure_count:
                logger.info(f"Trying saved profile: {profile.port} at {profile.baudrate} baud")
                if self.connect(
                    port=profile.port,
                    baudrate=profile.baudrate,
                    protocol=profile.protocol,
                    timeout=timeout,
                    save_profile=False
                ):
                    return True

        # Try discovered ports with common baudrates
        ports = self.discover_ports()
        likely_ports = [p for p in ports if p.is_likely_obd]
        other_ports = [p for p in ports if not p.is_likely_obd]

        for port in likely_ports + other_ports:
            for baudrate in OBD_REAL_CONFIG["preferred_baudrates"]:
                for protocol in OBD_REAL_CONFIG["preferred_protocols"]:
                    logger.info(f"Trying {port.device} at {baudrate} baud, protocol {protocol}")
                    if self.connect(
                        port=port.device,
                        baudrate=baudrate,
                        protocol=protocol,
                        timeout=timeout,
                        save_profile=True,
                        profile_name=f"Auto: {port.description}"
                    ):
                        return True

        logger.warning("Auto-connect failed - no working adapter found")
        return False

    def disconnect(self):
        """Disconnect from current adapter."""
        with self._lock:
            self._stop_health_monitoring()
            self._stop_reconnection()

            if self._adapter:
                self._adapter.disconnect()
                self._adapter = None

            self._connection_state = ConnectionState.DISCONNECTED
            self._reconnect_attempts = 0
            # Keep _current_profile for reconnect() - profile represents saved config, not active connection

            self._notify_status_change()
            self._log_connection_event("disconnect", "", 0, "", "User disconnected")

            logger.info("Disconnected from OBD adapter")

    def reconnect(self) -> bool:
        """
        Attempt to reconnect using current profile.

        Returns:
            True if reconnection successful
        """
        with self._lock:
            if not self._current_profile:
                logger.warning("No profile to reconnect with")
                return False

            profile = self._current_profile
            logger.info(f"Reconnecting to {profile.port}...")

            return self.connect(
                port=profile.port,
                baudrate=profile.baudrate,
                protocol=profile.protocol,
                save_profile=False
            )

    def start_auto_reconnect(self):
        """Start automatic reconnection background thread."""
        with self._lock:
            if self._reconnect_thread and self._reconnect_thread.is_alive():
                return  # Already running

            self._reconnect_enabled = True
            self._reconnect_stop_event.clear()
            self._reconnect_thread = threading.Thread(
                target=self._reconnect_loop,
                daemon=True,
                name="OBD-Reconnect"
            )
            self._reconnect_thread.start()
            logger.info("Auto-reconnect started")

    def stop_auto_reconnect(self):
        """Stop automatic reconnection."""
        with self._lock:
            self._stop_reconnection()

    def _stop_reconnection(self):
        """Stop reconnection thread."""
        self._reconnect_enabled = False
        self._reconnect_stop_event.set()
        if self._reconnect_thread:
            self._reconnect_thread.join(timeout=2.0)
            self._reconnect_thread = None

    def _reconnect_loop(self):
        """Background reconnection loop with exponential backoff."""
        while not self._reconnect_stop_event.is_set():
            # Wait for disconnect
            while (self.connection_state == ConnectionState.CONNECTED
                   and not self._reconnect_stop_event.is_set()):
                time.sleep(1.0)

            if self._reconnect_stop_event.is_set():
                break

            if not self._reconnect_enabled:
                break

            # Check if we should attempt reconnection
            if self._reconnect_attempts >= self._max_reconnect_attempts:
                logger.error("Max reconnection attempts reached")
                self._log_connection_event(
                    "error", "", 0, "",
                    "Max reconnection attempts reached"
                )
                break

            # Calculate backoff
            backoff_idx = min(self._reconnect_attempts, len(self._reconnect_backoff) - 1)
            wait_time = self._reconnect_backoff[backoff_idx]

            logger.info(f"Reconnection attempt {self._reconnect_attempts + 1} in {wait_time}s")

            # Wait with periodic check
            for _ in range(wait_time):
                if self._reconnect_stop_event.is_set():
                    break
                time.sleep(1.0)

            if self._reconnect_stop_event.is_set():
                break

            # Attempt reconnection
            self._reconnect_attempts += 1
            if self.reconnect():
                logger.info("Reconnection successful")
                self._reconnect_attempts = 0
                self._log_connection_event(
                    "reconnect",
                    self._current_profile.port if self._current_profile else "",
                    self._current_profile.baudrate if self._current_profile else 0,
                    self._current_profile.protocol if self._current_profile else "",
                    "Reconnected successfully"
                )
                break
            else:
                logger.warning(f"Reconnection attempt {self._reconnect_attempts} failed")

    def _start_health_monitoring(self):
        """Start background health monitoring."""
        self._stop_health_monitoring()
        self._health_stop_event.clear()
        self._health_thread = threading.Thread(
            target=self._health_monitor_loop,
            daemon=True,
            name="OBD-HealthMonitor"
        )
        self._health_thread.start()
        logger.debug("Health monitoring started")

    def _stop_health_monitoring(self):
        """Stop health monitoring thread."""
        self._health_stop_event.set()
        if self._health_thread:
            self._health_thread.join(timeout=2.0)
            self._health_thread = None

    def _health_monitor_loop(self):
        """Background health check loop."""
        while not self._health_stop_event.is_set():
            time.sleep(self.health_check_interval)

            if self._health_stop_event.is_set():
                break

            if self.connection_state != ConnectionState.CONNECTED:
                continue

            # Perform health check
            health = self._perform_health_check()
            self._last_health_check = datetime.now()
            self._add_health_record(health)

            # If health check fails, trigger reconnection
            if not health.get("connected", False) or health.get("query_test") == "failed":
                logger.warning(f"Health check failed: {health}")
                self._log_connection_event(
                    "error",
                    self._current_profile.port if self._current_profile else "",
                    self._current_profile.baudrate if self._current_profile else 0,
                    self._current_profile.protocol if self._current_profile else "",
                    f"Health check failed: {health.get('status', 'Unknown')}"
                )

                # Disconnect to trigger reconnection
                with self._lock:
                    if self._adapter:
                        self._adapter.disconnect()
                    self._connection_state = ConnectionState.ERROR
                    self._notify_status_change()

                # Reconnection will be handled by reconnect loop if enabled
                break

    def _perform_health_check(self) -> Dict[str, Any]:
        """Perform a health check on current connection."""
        if not self._adapter:
            return {"connected": False, "status": "NO_ADAPTER"}

        return self._adapter.health_check()

    def get_health_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get health check history."""
        with self._lock:
            return self._health_history[-limit:]

    def get_connection_status(self) -> Dict[str, Any]:
        """Get comprehensive connection status."""
        with self._lock:
            status = {
                "state": self.connection_state.value,
                "connected": self.connection_state == ConnectionState.CONNECTED,
                "port": self._current_profile.port if self._current_profile else None,
                "baudrate": self._current_profile.baudrate if self._current_profile else None,
                "protocol": self._current_profile.protocol if self._current_profile else None,
                "adapter_type": self._adapter.adapter_type.value if self._adapter else None,
                "supported_pids_count": len(self._adapter.supported_pids) if self._adapter else 0,
                "last_health_check": self._last_health_check.isoformat() if self._last_health_check else None,
                "reconnect_enabled": self._reconnect_enabled,
                "reconnect_attempts": self._reconnect_attempts,
                "statistics": self._adapter.statistics if self._adapter else None,
            }

            if self._adapter and self._adapter.is_connected:
                status["health"] = self._adapter.health_check()

            return status

    def _save_profile(self, port: str, baudrate: int, protocol: str, friendly_name: str = ""):
        """Save or update connection profile."""
        key = f"{port}:{baudrate}:{protocol}"

        if key in self._profiles:
            profile = self._profiles[key]
            profile.last_connected = datetime.now()
            profile.success_count += 1
            if friendly_name:
                profile.friendly_name = friendly_name
        else:
            profile = ConnectionProfile(
                port=port,
                baudrate=baudrate,
                protocol=protocol,
                adapter_type=AdapterType.USB if port.upper().startswith("COM") else AdapterType.UNKNOWN,
                friendly_name=friendly_name or f"{port} @ {baudrate}",
                last_connected=datetime.now(),
                success_count=1,
                failure_count=0
            )
            self._profiles[key] = profile

        self._current_profile = profile
        self._save_profiles_to_file()

    def _add_attempt(self, attempt: ConnectionAttempt):
        """Record connection attempt."""
        with self._lock:
            self._attempt_history.append(attempt)
            if len(self._attempt_history) > self._max_attempt_history:
                self._attempt_history = self._attempt_history[-self._max_attempt_history:]

            # Update profile failure count on failure
            if not attempt.success and self._current_profile:
                key = f"{attempt.port}:{attempt.baudrate}:{attempt.protocol}"
                if key in self._profiles:
                    self._profiles[key].failure_count += 1
                    self._save_profiles_to_file()

    def _add_health_record(self, health: Dict[str, Any]):
        """Add health check record to history."""
        with self._lock:
            record = {
                "timestamp": datetime.now().isoformat(),
                **health
            }
            self._health_history.append(record)
            if len(self._health_history) > self._max_health_history:
                self._health_history = self._health_history[-self._max_health_history:]

    def _notify_status_change(self):
        """Notify status change callback."""
        if self.on_status_change:
            try:
                self.on_status_change(self.connection_state)
            except Exception as e:
                logger.error(f"Error in status change callback: {e}")

    def _log_connection_event(
        self,
        event_type: str,
        port: str,
        baudrate: int,
        protocol: str,
        details: str
    ):
        """Log connection event."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "port": port,
            "baudrate": baudrate,
            "protocol": protocol,
            "details": details,
            "state": self.connection_state.value
        }

        if self.on_connection_log:
            try:
                self.on_connection_log(event)
            except Exception as e:
                logger.error(f"Error in connection log callback: {e}")

    def _load_profiles(self):
        """Load saved profiles from file."""
        try:
            path = Path(self.profiles_file)
            if path.exists():
                with open(path, 'r') as f:
                    data = json.load(f)

                for key, profile_data in data.items():
                    profile = ConnectionProfile(
                        port=profile_data["port"],
                        baudrate=profile_data["baudrate"],
                        protocol=profile_data["protocol"],
                        adapter_type=AdapterType(profile_data.get("adapter_type", "unknown")),
                        friendly_name=profile_data.get("friendly_name", ""),
                        last_connected=(
                            datetime.fromisoformat(profile_data["last_connected"])
                            if profile_data.get("last_connected") else None
                        ),
                        success_count=profile_data.get("success_count", 0),
                        failure_count=profile_data.get("failure_count", 0)
                    )
                    self._profiles[key] = profile

                logger.info(f"Loaded {len(self._profiles)} connection profiles")
        except Exception as e:
            logger.warning(f"Could not load connection profiles: {e}")

    def _save_profiles_to_file(self):
        """Save profiles to file."""
        try:
            path = Path(self.profiles_file)
            path.parent.mkdir(parents=True, exist_ok=True)

            data = {}
            for key, profile in self._profiles.items():
                data[key] = {
                    "port": profile.port,
                    "baudrate": profile.baudrate,
                    "protocol": profile.protocol,
                    "adapter_type": profile.adapter_type.value,
                    "friendly_name": profile.friendly_name,
                    "last_connected": profile.last_connected.isoformat() if profile.last_connected else None,
                    "success_count": profile.success_count,
                    "failure_count": profile.failure_count
                }

            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save connection profiles: {e}")

    def get_profiles(self) -> List[ConnectionProfile]:
        """Get all saved profiles, sorted by last connected."""
        with self._lock:
            profiles = list(self._profiles.values())
            profiles.sort(key=lambda p: p.last_connected or datetime.min, reverse=True)
            return profiles

    def delete_profile(self, port: str, baudrate: int, protocol: str) -> bool:
        """Delete a saved profile."""
        with self._lock:
            key = f"{port}:{baudrate}:{protocol}"
            if key in self._profiles:
                del self._profiles[key]
                self._save_profiles_to_file()
                return True
            return False

    def clear_profiles(self):
        """Clear all saved profiles."""
        with self._lock:
            self._profiles.clear()
            self._save_profiles_to_file()

    def get_attempt_history(self, limit: int = 20) -> List[ConnectionAttempt]:
        """Get connection attempt history."""
        with self._lock:
            return self._attempt_history[-limit:]

    def set_mode(self, mode: OBDMode):
        """Set OBD mode (simulation/real)."""
        if mode == OBDMode.SIMULATION:
            self.disconnect()
            self.stop_auto_reconnect()
        # Real mode will be handled by connect()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        self.stop_auto_reconnect()
        return False
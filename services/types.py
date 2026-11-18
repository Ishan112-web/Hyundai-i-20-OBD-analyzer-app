"""
i20 AI Garage - Shared Types

Common type definitions used across services to avoid circular imports.
"""

from datetime import datetime
from typing import Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class OBDMode(Enum):
    """OBD operation modes."""
    SIMULATION = "simulation"
    REAL = "real"


class ConnectionState(Enum):
    """OBD connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class SensorReading:
    """Single sensor reading."""
    pid: str
    name: str
    value: Any
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    is_simulated: bool = True


@dataclass
class DTC:
    """Diagnostic Trouble Code."""
    code: str
    description: str
    severity: str
    status: str = "active"  # active, pending, history, permanent
    is_demo: bool = True
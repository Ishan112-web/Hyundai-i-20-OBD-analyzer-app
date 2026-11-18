"""
i20 AI Garage - Configuration Module

Centralized configuration management using environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# Database
DATABASE_PATH = DATA_DIR / "i20_garage.db"

# LM Studio Configuration
LM_STUDIO_BASE_URL = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "qwen2.5-3b-instruct")
LM_STUDIO_TEMPERATURE = float(os.getenv("LM_STUDIO_TEMPERATURE", "0.7"))
LM_STUDIO_TIMEOUT = int(os.getenv("LM_STUDIO_TIMEOUT", "30"))

# OBD Configuration
OBD_MODE = os.getenv("OBD_MODE", "simulation")  # "simulation" or "real"
OBD_PORT = os.getenv("OBD_PORT", "COM3")
OBD_BAUDRATE = int(os.getenv("OBD_BAUDRATE", "38400"))
OBD_PROTOCOL = os.getenv("OBD_PROTOCOL", "auto")

# Simulation Configuration
SIMULATION_INTERVAL = float(os.getenv("SIMULATION_INTERVAL", "0.5"))  # seconds
TELEMETRY_REFRESH_INTERVAL = float(os.getenv("TELEMETRY_REFRESH_INTERVAL", "1.0"))  # seconds

# Vehicle Profile (Hyundai i20 Asta 2023)
VEHICLE_INFO = {
    "make": "Hyundai",
    "model": "i20 Asta",
    "year": 2023,
    "engine": "1.2L Naturally Aspirated Petrol",
    "transmission": "Manual",
    "fuel_type": "Petrol",
    "market": "India",
    "ecu_tuning": "Stock",
    "diagnostic_mode": "Simulation",
    "vin": "MALA841CLHM123456",  # Example VIN pattern for India
}

# Engine Specifications
ENGINE_SPECS = {
    "displacement_cc": 1197,
    "cylinders": 4,
    "max_power_ps": 83,
    "max_power_rpm": 6000,
    "max_torque_nm": 115,
    "max_torque_rpm": 4000,
    "compression_ratio": "10.5:1",
    "fuel_system": "Multi-Point Injection",
    "emission_standard": "BS6",
    "redline_rpm": 6500,
    "idle_rpm": 750,
}

# Simulation Scenarios
SIMULATION_SCENARIOS = {
    "idle": {
        "name": "Idle",
        "description": "Engine idling at operating temperature",
        "rpm_range": (700, 900),
        "speed_range": (0, 0),
        "coolant_temp_range": (85, 95),
        "throttle_range": (0, 5),
        "load_range": (10, 20),
    },
    "city": {
        "name": "City Driving",
        "description": "Stop-and-go city traffic simulation",
        "rpm_range": (1000, 3000),
        "speed_range": (0, 50),
        "coolant_temp_range": (85, 100),
        "throttle_range": (5, 40),
        "load_range": (15, 50),
    },
    "highway": {
        "name": "Highway Driving",
        "description": "Steady highway cruising",
        "rpm_range": (2000, 3500),
        "speed_range": (60, 120),
        "coolant_temp_range": (90, 98),
        "throttle_range": (20, 35),
        "load_range": (30, 55),
    },
    "acceleration": {
        "name": "Hard Acceleration",
        "description": "Full throttle acceleration run",
        "rpm_range": (2000, 6200),
        "speed_range": (0, 140),
        "coolant_temp_range": (90, 105),
        "throttle_range": (60, 100),
        "load_range": (60, 100),
    },
    "overheating": {
        "name": "Engine Overheating Demo",
        "description": "Simulated overheating scenario (SOFTWARE DEMO ONLY)",
        "rpm_range": (1500, 4000),
        "speed_range": (20, 80),
        "coolant_temp_range": (105, 125),
        "throttle_range": (25, 50),
        "load_range": (35, 70),
    },
}

# AI System Prompt
AI_SYSTEM_PROMPT = """You are i20 AI Garage, an automotive diagnostic assistant for a 2023 Hyundai i20 Asta 1.2L naturally aspirated petrol manual in India.

Explain automotive concepts clearly.
Distinguish measured values from simulated values.
Never invent diagnostic readings.
Never claim a fault is confirmed without sufficient evidence.
Explain possible causes and recommend appropriate verification.
Prioritize safety and manufacturer specifications.
Never recommend disabling emissions systems or safety systems.
Do not generate ECU flashing instructions or unsafe calibration changes.
Do not pretend to access the vehicle unless actual data is supplied.

Current Vehicle Context:
- Vehicle: 2023 Hyundai i20 Asta
- Engine: 1.2L Naturally Aspirated Petrol (4-cylinder, 1197cc)
- Transmission: Manual 5-speed
- Fuel: Petrol (BS6)
- Market: India
- ECU: Stock tuning
- Diagnostic Mode: Simulation (no real OBD connection)

When discussing telemetry, always clarify if values are simulated or from real OBD data."""

# UI Theme Colors
THEME = {
    "bg_primary": "#1a1d21",      # Dark graphite
    "bg_secondary": "#23272e",    # Slightly lighter
    "bg_card": "#2a2e36",         # Card background
    "border": "#3a3f4a",          # Subtle borders
    "text_primary": "#e8eaed",    # Main text
    "text_secondary": "#9aa3ad",  # Secondary text
    "accent_blue": "#00b4d8",     # Telemetry cyan
    "accent_green": "#2ecc71",    # Healthy/OK
    "accent_amber": "#f39c12",    # Warning
    "accent_red": "#e74c3c",      # Critical/Error
    "accent_purple": "#9b59b6",   # AI/Assistant
}

# Gauge Thresholds
GAUGE_THRESHOLDS = {
    "rpm": {
        "green_max": 3000,
        "amber_max": 5000,
        "red_max": 6500,
    },
    "speed": {
        "green_max": 60,
        "amber_max": 100,
        "red_max": 140,
    },
    "coolant_temp": {
        "green_max": 95,
        "amber_max": 105,
        "red_max": 115,
    },
    "throttle": {
        "green_max": 40,
        "amber_max": 70,
        "red_max": 100,
    },
    "engine_load": {
        "green_max": 50,
        "amber_max": 80,
        "red_max": 100,
    },
    "fuel_trim": {
        "green_min": -10,
        "green_max": 10,
        "amber_min": -20,
        "amber_max": 20,
        "red_min": -30,
        "red_max": 30,
    },
    "voltage": {
        "green_min": 13.5,
        "green_max": 14.5,
        "amber_min": 12.5,
        "amber_max": 15.5,
        "red_min": 11.5,
        "red_max": 16.0,
    },
}

# DTC Severity Levels
DTC_SEVERITY = {
    "critical": {"color": "#e74c3c", "label": "Critical", "description": "Immediate attention required - safety or severe damage risk"},
    "major": {"color": "#f39c12", "label": "Major", "description": "Significant issue - should be addressed soon"},
    "minor": {"color": "#3498db", "label": "Minor", "description": "Minor issue - monitor and schedule service"},
    "info": {"color": "#9b59b6", "label": "Information", "description": "Informational - no immediate action needed"},
}

# Demo DTCs for simulation mode
DEMO_DTCS = [
    {
        "code": "P0300",
        "description": "Random/Multiple Cylinder Misfire Detected",
        "severity": "major",
        "possible_causes": [
            "Faulty spark plugs or ignition coils",
            "Fuel injector issues",
            "Vacuum leaks",
            "Low fuel pressure",
            "ECM/PCM software issue",
        ],
        "recommended_verification": [
            "Check spark plug condition and gap",
            "Inspect ignition coil resistance",
            "Verify fuel pressure",
            "Check for vacuum leaks with smoke test",
            "Scan for additional codes",
        ],
        "is_demo": True,
    },
    {
        "code": "P0171",
        "description": "System Too Lean (Bank 1)",
        "severity": "major",
        "possible_causes": [
            "Vacuum leak downstream of MAF",
            "Faulty MAF sensor",
            "Fuel filter clogged",
            "Weak fuel pump",
            "Exhaust leak before O2 sensor",
        ],
        "recommended_verification": [
            "Inspect intake system for leaks",
            "Clean or test MAF sensor",
            "Check fuel pressure and flow",
            "Inspect exhaust for leaks",
            "Monitor short and long term fuel trims",
        ],
        "is_demo": True,
    },
    {
        "code": "P0420",
        "description": "Catalyst System Efficiency Below Threshold (Bank 1)",
        "severity": "minor",
        "possible_causes": [
            "Aged catalytic converter",
            "Exhaust leak",
            "Faulty downstream O2 sensor",
            "Engine running rich/lean",
            "PCM software needs update",
        ],
        "recommended_verification": [
            "Check for exhaust leaks",
            "Monitor O2 sensor switching frequency",
            "Verify fuel trim values",
            "Check for related TSBs",
            "Perform catalytic converter efficiency test",
        ],
        "is_demo": True,
    },
    {
        "code": "P0128",
        "description": "Coolant Thermostat (Coolant Temperature Below Thermostat Regulating Temperature)",
        "severity": "minor",
        "possible_causes": [
            "Thermostat stuck open",
            "Faulty ECT sensor",
            "Low coolant level",
            "Cooling fan stuck on",
            "PCM calibration issue",
        ],
        "recommended_verification": [
            "Verify coolant level and condition",
            "Test thermostat operation",
            "Check ECT sensor resistance",
            "Monitor warm-up cycle",
            "Inspect cooling fan operation",
        ],
        "is_demo": True,
    },
]

# Maintenance intervals (km)
MAINTENANCE_INTERVALS = {
    "engine_oil": {"interval_km": 10000, "description": "Engine Oil Change"},
    "oil_filter": {"interval_km": 10000, "description": "Oil Filter Replacement"},
    "air_filter": {"interval_km": 20000, "description": "Air Filter Replacement"},
    "cabin_filter": {"interval_km": 15000, "description": "Cabin Air Filter Replacement"},
    "spark_plugs": {"interval_km": 40000, "description": "Spark Plug Replacement"},
    "coolant": {"interval_km": 60000, "description": "Coolant Replacement"},
    "brake_fluid": {"interval_km": 40000, "description": "Brake Fluid Replacement"},
    "transmission_oil": {"interval_km": 60000, "description": "Manual Transmission Oil"},
    "brake_pads_front": {"interval_km": 30000, "description": "Front Brake Pads Inspection"},
    "brake_pads_rear": {"interval_km": 40000, "description": "Rear Brake Pads Inspection"},
    "tyre_rotation": {"interval_km": 10000, "description": "Tyre Rotation"},
    "battery": {"interval_km": 40000, "description": "Battery Health Check"},
}

# =============================================================================
# V2 Phase 1: Real OBD Connectivity Configuration
# =============================================================================

# Real OBD Configuration
OBD_REAL_CONFIG = {
    "auto_detect_ports": True,
    "preferred_baudrates": [38400, 115200, 9600, 57600],
    "preferred_protocols": ["AUTO", "6", "5", "4", "3", "2", "1"],
    "connection_timeout": 10,
    "query_timeout": 2,
    "health_check_interval": 30,
    "reconnect_attempts": 5,
    "reconnect_backoff": [1, 2, 5, 10, 30],
}

# PID Polling Configuration
PID_POLLING_CONFIG = {
    "critical": {"pids": ["0C", "0D", "05"], "interval_ms": 100},
    "high": {"pids": ["11", "04", "0B"], "interval_ms": 200},
    "medium": {"pids": ["06", "07", "42", "10"], "interval_ms": 500},
    "low": {"pids": ["14", "15", "16", "17", "1C", "1D", "1E", "1F"], "interval_ms": 1000},
}

# AI Diagnostic Configuration (Phase 2 placeholder)
AI_DIAGNOSTIC_CONFIG = {
    "model": "qwen2.5-3b-instruct",
    "temperature": 0.1,
    "max_tokens": 2048,
    "structured_output": True,
    "rag_enabled": True,
    "rag_top_k": 5,
    "confidence_threshold": 0.7,
    "fallback_to_rules": True,
}

# Rule Engine Configuration (Phase 3 placeholder)
RULE_ENGINE_CONFIG = {
    "enabled": True,
    "rules_dir": "services/rules",
    "evaluation_interval_ms": 1000,
    "trend_window_seconds": 60,
    "min_confidence": 0.6,
}

# Reporting Configuration (Phase 4 placeholder)
REPORT_CONFIG = {
    "templates_dir": "services/report_templates",
    "output_dir": "reports",
    "pdf_enabled": True,
    "default_format": "html",
    "include_oem_data": True,
    "cost_currency": "INR",
    "cost_region": "India",
}

# Migration Configuration (Phase 5 placeholder)
MIGRATION_CONFIG = {
    "migrations_dir": "migrations",
    "backup_before_migrate": True,
    "backup_dir": "backups/migrations",
}
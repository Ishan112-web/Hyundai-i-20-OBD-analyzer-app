# i20 AI Garage

**A complete automotive intelligence application for the 2023 Hyundai i20 Asta 1.2L Petrol**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.67+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey.svg)](https://github.com)

---

## Overview

i20 AI Garage is a locally-running automotive diagnostics and intelligence application built for the **2023 Hyundai i20 Asta 1.2L naturally aspirated petrol manual (India market)**. It provides a professional-grade dashboard, AI-powered diagnostic assistance, simulated vehicle telemetry, and comprehensive maintenance tracking — all running entirely on your local machine with **no cloud dependencies**.

### Key Features

| Feature | Description |
|---------|-------------|
| 🏁 **Dashboard** | Real-time gauges (RPM, Speed, Coolant, Load), live telemetry charts, simulation controls |
| 🔧 **Diagnostics** | DTC scanning with descriptions, severity classification, possible causes, verification steps, **AI-powered diagnosis with structured output** |
| 📊 **Performance** | Session recording, historical charts, statistics (peak RPM, max speed, avg speed, duration) |
| 🛠️ **Maintenance** | Service records (oil, filters, plugs, coolant, battery, tyres), upcoming maintenance alerts |
| 🤖 **AI Assistant** | Local LM Studio integration (Qwen2.5 3B) with **Chat mode** and **Diagnostic mode** |
| 🧠 **AI Diagnostic Engine** | Structured JSON diagnosis with probable causes, confidence scores, verification steps, repair recommendations (INR estimates), RAG knowledge base |
| 📐 **Deterministic Rule Engine** | YAML-based diagnostic rules with 4 evaluator types (Threshold, Trend, Correlation, Composite), sensor history for trend analysis, cooldown mechanism, missing data policies, SQLite persistence |
| 📄 **Professional Reports** | **NEW** — 4 report types (Diagnostic, Vehicle Health, Performance, Maintenance) with HTML/PDF output, Jinja2 templates with autoescaping, ReportLab PDF generation, data provenance tracking |
| 🚗 **Vehicle Profile** | Complete vehicle specs, engine parameters, connection status monitoring |
| ⚙️ **Settings** | LM Studio, OBD, simulation, and application configuration |
| 💾 **Persistence** | SQLite database for all data (sessions, diagnostics, maintenance, conversations, AI diagnoses, RAG documents) |

---

## Screenshots

> **Note**: The application runs in **SIMULATION MODE** by default. All telemetry values are software-generated for demonstration. Connect a real ELM327 OBD-II adapter for live vehicle data.

---

## Requirements

### Hardware
- Windows 10/11 or Linux
- NVIDIA GPU (RTX 3050 Ti or better recommended for LM Studio)
- 8GB+ RAM (16GB recommended)
- ELM327 OBD-II adapter (optional, for real vehicle data)

### Software
- Python 3.11+
- LM Studio with **Qwen2.5 3B Instruct GGUF** model loaded
- Python packages (see `requirements.txt`) — includes `jinja2` and `reportlab` for reporting

---

## Installation

### 1. Clone / Download
```powershell
git clone <repository-url>
cd i20-AI
```

### 2. Set Up Virtual Environment
```powershell
# Windows
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure LM Studio
1. Install [LM Studio](https://lmstudio.ai/)
2. Download **Qwen2.5 3B Instruct GGUF** (q4_k_m or similar quantization)
3. Load the model in LM Studio
4. Go to **Developer → Start Server** (default: `http://localhost:1234/v1`)
5. Verify the model appears in **Developer → API Endpoints**

### 4. Configure Environment (Optional)
```powershell
# Copy example and modify if needed
copy .env.example .env
```
Edit `.env` to change:
- LM Studio URL/model/temperature
- OBD port (COM3 on Windows, /dev/ttyUSB0 on Linux)
- Simulation intervals

---

## Quick Start

### Windows (PowerShell) - Recommended
```powershell
.\run.ps1
```

### Windows (Command Prompt)
```cmd
run.bat
```

### Manual Start
```powershell
.venv\Scripts\activate
streamlit run app.py
```

### Access the Application
Open your browser to: **http://localhost:8501**

---

## Application Pages

### 🏁 Dashboard
- **Primary Gauges**: RPM (0-7000), Speed (0-160 km/h), Coolant Temp (-20-130°C), Engine Load (0-100%)
- **Telemetry Cards**: 10 detailed sensor readings with status indicators
- **Live Charts**: 6-panel time-series (RPM, Speed, Coolant, Throttle, Load, Fuel Trims)
- **Simulation Controls**: 5 scenarios (Idle, City, Highway, Acceleration, Overheating Demo)
- **Session Recording**: Start/Stop/Save telemetry sessions to database

### 🔧 Diagnostics
- **DTC Scan**: One-click diagnostic scan (simulation mode uses demo codes)
- **Code Details**: Description, severity (Critical/Major/Minor/Info), possible causes, verification steps
- **Freeze Frame**: Simulated snapshot data at time of fault
- **Reports**: Save diagnostic reports to database, download as text
- **History**: View all past scans with timestamps and DTC counts
- **🧠 AI Diagnosis**: One-click AI-powered structured diagnosis with probable causes, confidence scores, verification steps, repair recommendations (INR estimates), and safety warnings
- **AI Diagnosis History**: Persisted AI diagnostic sessions with full structured output
- **📐 Rule Engine Panel**: One-click deterministic rule evaluation with 4 rule types (Threshold, Trend, Correlation, Composite), findings with severity badges, statistics, and evaluation history

### 📊 Performance Analytics
- **Session List**: All recorded sessions with statistics
- **Session Detail**: Interactive charts for RPM, Speed, Coolant, Throttle, Load, Fuel Trims
- **Statistics**: Peak RPM, Max/Avg Speed, Max Coolant Temp, Max Load, Duration, Distance
- **Comparison**: Overlay multiple sessions for analysis
- **Export**: Download session data as CSV

### 🛠️ Maintenance Tracker
- **Records**: Complete service history with filters and statistics
- **Add/Edit**: Professional form with 12 predefined service types
- **Quick Add**: One-click buttons for common services (Oil Change, Air Filter, etc.)
- **Upcoming**: Automatic calculation based on odometer and service intervals
- **Reminders**: Visual status (Overdue/Due Soon/OK) with km/days remaining

### 🚗 Vehicle Profile
- **Vehicle Info**: Editable vehicle details (Make, Model, Year, Engine, Transmission, etc.)
- **Engine Specs**: 1.2L Kappa specs (83 PS @ 6000 RPM, 115 Nm @ 4000 RPM, 10.5:1 compression)
- **Connections**: OBD-II and AI/LM Studio connection status with test buttons
- **Diagnostics**: Current DTCs with severity badges and recommended actions

### 🤖 AI Assistant
- **Chat Mode**: Natural language automotive Q&A with vehicle context awareness
- **Diagnostic Mode**: Structured AI diagnosis for specific DTCs and symptoms with detailed probable causes, confidence scores, and repair recommendations
- **Vehicle Context**: AI receives live simulated/real telemetry when available
- **Quick Prompts**: Pre-built questions for common diagnostic scenarios
- **Conversation History**: Persisted to database, survives restarts
- **Model Status**: Real-time LM Studio connection and model availability

### 📄 Reports (NEW - Phase 4)
- **Report Types**: Comprehensive Diagnostic, Vehicle Health, Performance, Maintenance
- **Formats**: Professional HTML (offline-capable, print-optimized) and PDF (ReportLab)
- **Source Selection**: Choose simulation, real, or mixed data sources per report
- **Data Provenance**: Every report includes data source badges (SIMULATION/REAL/MIXED)
- **HTML Preview**: In-browser preview with print-to-PDF capability
- **Downloads**: One-click HTML/PDF download with unique report IDs
- **Batch Generation**: Generate all 4 report types at once
- **Security**: Jinja2 autoescaping prevents XSS — all user content HTML-escaped

### ⚙️ Settings
- **OBD-II**: Mode (Simulation/Real), Port, Baudrate, Protocol, Connection Test
- **AI Assistant**: LM Studio URL, Model, Temperature, Timeout, Model Discovery Test
- **Simulation**: Update intervals, scenario list
- **Data Management**: Export all data, clear history, database backup
- **About**: Version info, license, links

---

## Simulation Scenarios

| Scenario | Description | RPM Range | Speed Range | Coolant Temp |
|----------|-------------|-----------|-------------|--------------|
| **Idle** | Engine idling at operating temp | 700-900 | 0 | 85-95°C |
| **City** | Stop-and-go traffic | 1000-3000 | 0-50 km/h | 85-100°C |
| **Highway** | Steady cruising | 2000-3500 | 60-120 km/h | 90-98°C |
| **Acceleration** | Full throttle run | 2000-6200 | 0-140 km/h | 90-105°C |
| **Overheating** | **DEMO ONLY** - Coolant overheat | 1500-4000 | 20-80 km/h | 105-125°C |

> ⚠️ **Overheating scenario is a software demonstration only.** It does not affect any real vehicle.

---

## Architecture

```
i20-AI/
├── app.py                 # Main Streamlit application
├── config.py              # All configuration constants (incl. OBD_REAL_CONFIG, PID_POLLING_CONFIG)
├── requirements.txt       # Python dependencies
├── .env                   # Local environment overrides
├── .env.example           # Environment template
├── run.ps1 / run.bat      # Startup scripts
├── README.md              # This file
│
├── services/
│   ├── __init__.py        # Service exports (incl. RealOBDAdapter, ConnectionManager, PIDRegistry, DiagnosticEngine, RuleEngine, ReportGenerator)
│   ├── database.py        # SQLite database service (9 tables + 2 new: ai_diagnostic_sessions, rag_documents)
│   ├── ai_service.py      # LM Studio API client (NEW: structured JSON output support)
│   ├── obd_service.py     # OBD-II abstraction (SimulationEngine + RealOBDAdapter integration)
│   ├── real_obd_adapter.py # ELM327 communication layer (python-OBD wrapper)
│   ├── connection_manager.py # Auto-detect, multi-baud/protocol, reconnection, profiles
│   ├── pid_registry.py    # PID discovery, prioritization, validation, polling intervals
│   ├── types.py           # Shared types (OBDMode, ConnectionState, SensorReading, DTC)
│   ├── diagnostic_models.py  # NEW: Pydantic models for structured AI diagnosis output
│   ├── diagnostic_engine.py  # NEW: AI Diagnostic Engine (ContextBuilder, KnowledgeBase, Orchestrator)
│   ├── rule_models.py     # NEW: Pydantic models for deterministic rule engine
│   ├── rule_loader.py     # NEW: YAML rule loader with validation
│   ├── rule_evaluator.py  # NEW: 4 evaluator types (Threshold, Trend, Correlation, Composite)
│   ├── rule_context.py    # NEW: AI context builder for rule findings
│   ├── rule_history.py    # NEW: SQLite persistence for rule evaluation history
│   ├── rule_engine.py     # NEW: Rule Engine orchestrator (singleton, loads/evaluates/persists)
│   ├── report_models.py   # NEW: Pydantic models for all 4 report types (Phase 4)
│   ├── report_data_builder.py # NEW: Data assembly from existing services (Phase 4)
│   ├── report_generator.py # NEW: Report orchestrator (Phase 4)
│   └── report_renderers/  # NEW: HTML (Jinja2) and PDF (ReportLab) renderers (Phase 4)
│       ├── __init__.py
│       ├── html_renderer.py
│       └── pdf_renderer.py
│   └── report_templates/  # NEW: Jinja2 templates for 4 report types (Phase 4)
│       ├── base.html
│       ├── diagnostic_report.html
│       ├── vehicle_health_report.html
│       ├── performance_report.html
│       └── maintenance_report.html
│
├── modules/
│   ├── __init__.py        # Module exports
│   ├── dashboard.py       # Main dashboard (Real/Sim toggle, live PID badges)
│   ├── diagnostics.py     # Diagnostic scanner (DTC workflow, freeze frame, AI diagnosis panel, Rule Engine panel)
│   ├── performance.py     # Performance analytics
│   ├── maintenance.py     # Maintenance tracker
│   ├── vehicle_profile.py # Vehicle profile (OBD info: VIN, CALID, CVN, supported PIDs)
│   ├── ai_assistant.py    # AI chat interface (Chat mode + Diagnostic mode)
│   ├── obd_connection.py  # Connection wizard UI
│   └── reports.py         # NEW: Reports UI with 3 tabs (Generate, Preview, Download) (Phase 4)
│
├── components/
│   ├── __init__.py        # Component exports
│   ├── sidebar.py         # Navigation sidebar (Real OBD status indicators)
│   ├── status_cards.py    # KPI/Connection/Alert cards
│   └── charts.py          # Reusable chart components
│
├── data/
│   └── i20_garage.db      # SQLite database (auto-created, V2 schema)
│
├── reports/
│   └── *.csv/*.txt        # Exported reports
│
├── rules/                 # NEW: YAML rule definition files
│   ├── example_rules.yaml
│   ├── cooling_rules.yaml
│   ├── fuel_rules.yaml
│   ├── ignition_rules.yaml
│   ├── emissions_rules.yaml
│   ├── electrical_rules.yaml
│   └── transmission_rules.yaml
│
├── tests/
    ├── test_database.py
    ├── test_ai_service.py
    ├── test_obd_service.py
    ├── test_simulation.py
    ├── test_obd_real.py   # 49 tests for Real OBD components
    ├── test_diagnostic_engine.py  # 37 tests for AI Diagnostic Engine
    ├── test_rule_loader.py        # 32 tests for rule loading/validation
    ├── test_rule_evaluator.py     # 44 tests for rule evaluation logic
    └── test_rule_engine.py        # 32 tests for RuleEngine orchestrator
```

---

## Configuration

### Environment Variables (`.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `LM_STUDIO_BASE_URL` | `http://localhost:1234/v1` | LM Studio API endpoint |
| `LM_STUDIO_MODEL` | `qwen2.5-3b-instruct` | Model identifier |
| `LM_STUDIO_TEMPERATURE` | `0.7` | Sampling temperature |
| `LM_STUDIO_TIMEOUT` | `30` | Request timeout (seconds) |
| `OBD_MODE` | `simulation` | `simulation` or `real` |
| `OBD_PORT` | `COM3` | Serial port for ELM327 |
| `OBD_BAUDRATE` | `38400` | Serial baud rate |
| `OBD_PROTOCOL` | `AUTO` | OBD protocol (AUTO, 1-9, A) |
| `SIMULATION_INTERVAL` | `0.5` | Simulation update interval (seconds) |
| `TELEMETRY_REFRESH_INTERVAL` | `1.0` | UI refresh interval (seconds) |

### V2 Configuration (config.py)

The following configuration dictionaries are defined in `config.py` and can be customized:

**OBD_REAL_CONFIG** — Connection behavior:
```python
{
    "auto_detect_ports": True,
    "preferred_baudrates": [38400, 115200, 9600, 57600],
    "preferred_protocols": ["AUTO", "6", "5", "4", "3", "2", "1"],
    "connection_timeout": 10,
    "query_timeout": 2,
    "health_check_interval": 30,
    "reconnect_attempts": 5,
    "reconnect_backoff": [1, 2, 5, 10, 30],
}
```

**PID_POLLING_CONFIG** — Priority-based polling intervals:
```python
{
    "critical": {"pids": ["0C", "0D", "05"], "interval_ms": 100},      # 10 Hz
    "high": {"pids": ["11", "04", "0B"], "interval_ms": 200},         # 5 Hz
    "medium": {"pids": ["06", "07", "42", "10"], "interval_ms": 500}, # 2 Hz
    "low": {"pids": ["14", "15", "16", "17", "1C", "1D", "1E", "1F"], "interval_ms": 1000}, # 1 Hz
}
```

**ENGINE_SPECS** — Hyundai i20 Asta 2023 1.2L Kappa:
```python
{
    "displacement_cc": 1197,
    "cylinders": 4,
    "max_power_ps": 83,
    "max_power_rpm": 6000,
    "max_torque_nm": 115,
    "max_torque_rpm": 4000,
    "compression_ratio": "10.5:1",
    "fuel_system": "MPi",
    "redline_rpm": 6500,
    "idle_rpm": 750,
}
```

**GAUGE_THRESHOLDS** — Visual status thresholds (green/amber/red):
```python
{
    "rpm": {"green_max": 3000, "amber_max": 5500},
    "speed": {"green_max": 100, "amber_max": 140},
    "coolant_temp": {"green_min": 80, "green_max": 100, "amber_min": 70, "amber_max": 110},
    "throttle": {"green_max": 80, "amber_max": 100},
    "engine_load": {"green_max": 80, "amber_max": 95},
    "fuel_trim": {"green_min": -10, "green_max": 10, "amber_min": -20, "amber_max": 20},
    "voltage": {"green_min": 13.5, "green_max": 14.7, "amber_min": 12.5, "amber_max": 15.5},
}
```

---

## Testing

Run the test suite:
```powershell
.venv\Scripts\activate
pytest tests/ -v
```

### Test Coverage
- **Database**: CRUD operations, sessions, diagnostics, maintenance, AI conversations, CSV export, backup, AI diagnostic sessions, RAG documents
- **AI Service**: Connection check, model discovery, chat completion, structured JSON output, error handling, context creation
- **OBD Service**: Simulation engine, scenarios, gauge thresholds, DTC scanning, mode switching
- **Simulation**: Scenario behavior, value ranges, thread safety, integration
- **AI Diagnostic Engine**: Pydantic models, KnowledgeBase, ContextBuilder, PromptBuilder, Engine orchestration, database integration (37 tests)
- **Rule Engine**: YAML loader validation (32 tests), 4 evaluator types (44 tests), engine orchestration (32 tests)
- **Reporting Engine**: Pydantic models (50+ tests), data builder (12 tests), HTML/PDF renderers (16 tests), generator orchestration (20 tests), integration tests

---

## OBD-II Real Vehicle Connectivity (V2 Phase 1)

The application now supports **real OBD-II connectivity** via ELM327-based adapters using the python-OBD library. This enables live telemetry acquisition, real DTC scanning, and freeze frame data from your actual vehicle.

### Supported Adapters

| Type | Examples | Interface | Notes |
|------|----------|-----------|-------|
| **USB** | VGate vLinker, OBDLink MX, BAFX, Generic ELM327 USB | COM port (Windows) / ttyUSB (Linux) | Most reliable, no pairing needed |
| **Bluetooth** | VGate vLinker BT, OBDLink LX, ELM327 BT 2.1/4.0 | COM port after pairing | Requires Windows Bluetooth pairing first |
| **WiFi** | VGate vLinker WiFi, OBDLink MX WiFi, Generic ELM327 WiFi | TCP/IP (IP:Port) | Connect to adapter's WiFi network first |

> **Tested Adapters**: VGate vLinker FS USB, OBDLink MX+ Bluetooth, Generic ELM327 v1.5 USB

### Windows COM Port Selection

1. **Connect adapter** to OBD-II port (under dashboard, driver's side)
2. **Turn ignition ON** (engine running for live data, ACC for DTCs)
3. **Open Device Manager** → Ports (COM & LPT)
4. **Identify the adapter**:
   - USB: "USB-SERIAL CH340 (COM3)" or "FT232R USB UART (COM4)"
   - Bluetooth: "Standard Serial over Bluetooth link (COM5)" — pair in Settings first
   - Note the COM number (e.g., COM3)
5. **Configure in Settings** → OBD-II tab → Port: `COM3` (or your detected port)

> **Tip**: The Settings page has an auto-discovery feature that lists likely OBD adapters with ✓ indicators.

### Linux/macOS Device Path

```bash
# USB adapters typically appear as:
ls /dev/ttyUSB*   # CH340, FTDI, CP210x
ls /dev/ttyACM*   # Some CDC-ACM devices

# Bluetooth (after pairing with bluetoothctl):
ls /dev/rfcomm*   # RFCOMM serial port
```

### Supported PIDs (Real-Time Telemetry)

| PID | Name | Unit | Priority | Poll Rate |
|-----|------|------|----------|-----------|
| 0C | Engine RPM | RPM | Critical | 10 Hz |
| 0D | Vehicle Speed | km/h | Critical | 10 Hz |
| 05 | Engine Coolant Temp | °C | Critical | 10 Hz |
| 11 | Throttle Position | % | High | 5 Hz |
| 04 | Calculated Engine Load | % | High | 5 Hz |
| 0B | Intake Manifold Pressure | kPa | High | 5 Hz |
| 06 | Short Term Fuel Trim B1 | % | Medium | 2 Hz |
| 07 | Long Term Fuel Trim B1 | % | Medium | 2 Hz |
| 42 | Control Module Voltage | V | Medium | 2 Hz |
| 10 | MAF Air Flow Rate | g/s | Medium | 2 Hz |
| 0F | Intake Air Temperature | °C | Low | 1 Hz |

> Additional PIDs (O2 sensors, runtime, distance, etc.) are discovered automatically at connection.

### DTC Scanning Capabilities

| Mode | Description | Status |
|------|-------------|--------|
| **$03** | Current/Active DTCs | ✅ Supported |
| **$07** | Pending DTCs (GET_CURRENT_DTC) | ✅ Supported |
| **$0A** | Permanent DTCs | ⚠️ Not in python-OBD |
| **$02** | Freeze Frame Data | ✅ Proxy via live readings |

### Connection Wizard (Settings → OBD-II Tab)

1. **Auto-Detect** — Scans all serial ports, identifies likely ELM327 adapters
2. **Port Selection** — Choose from discovered ports or enter manually
3. **Baudrate Test** — Tries 38400, 115200, 9600, 57600 automatically
4. **Protocol Test** — Tries AUTO, CAN 11-bit (6), CAN 29-bit (7), KWP2000, ISO9141
5. **PID Discovery** — Queries supported PID groups (0x00, 0x20, 0x40, 0x60, 0x80, 0xA0, 0xC0)
6. **Connected** — Shows supported PID count, adapter type, protocol ID

### Auto-Reconnection

- **Health Check**: Every 30 seconds (configurable)
- **Exponential Backoff**: 1s → 2s → 5s → 10s → 30s between attempts
- **Max Attempts**: 5 (configurable)
- **Profile Persistence**: Successful connections saved for instant reconnect

### Safety Limitations

- ✅ **Read-only operations only** — No ECU writing/flashing
- ✅ **Standard PIDs and DTCs** — No manufacturer-specific commands
- ✅ **No actuator tests** — No bidirectional controls
- ✅ **No emissions tampering** — Cannot disable systems
- ✅ **Graceful degradation** — Falls back to simulation if adapter disconnected

---

## Deterministic Rule Engine (V2 Phase 3)

The application now includes a complete **Deterministic Rule Engine** that provides fast, explainable, rule-based diagnostics alongside the AI engine. Rules are defined in YAML, validated via Pydantic, and evaluated against live or historical sensor data with full audit trail.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    RULE ENGINE                                  │
├─────────────────────────────────────────────────────────────────┤
│  RuleLoader (YAML)  →  RuleEvaluator (4 Types)                 │
│  (Validation)           - Threshold                            │
│                        - Trend                                 │
│                        - Correlation                           │
│                        - Composite                             │
│                          ↓                                      │
│              SensorHistory (trend analysis)                    │
│                          ↓                                      │
│              RuleEngine (Orchestrator)                         │
│  - Load/reload rules                                           │
│  - Evaluate against readings                                   │
│  - Cooldown management                                         │
│  - AI Context Building                                         │
│  - History Persistence (RuleHistoryStore)                      │
└─────────────────────────────────────────────────────────────────┘
```

### Core Components

| Component | Purpose |
|-----------|---------|
| **RuleLoader** | Loads and validates YAML rule files with Pydantic models |
| **RuleEvaluator** | 4 evaluator types: Threshold, Trend, Correlation, Composite |
| **SensorHistory** | Maintains time-series sensor readings for trend analysis |
| **RuleContextBuilder** | Builds structured AI context from rule findings |
| **RuleHistoryStore** | SQLite persistence for evaluation history and findings |
| **RuleEngine (Orchestrator)** | Coordinates loading → evaluation → context → persistence |

### Rule Types

| Type | Description | Use Cases |
|------|-------------|-----------|
| **Threshold** | Compare sensor value against threshold(s) | Overheat, low voltage, high RPM, lean/rich conditions |
| **Trend** | Analyze rate of change over time window | Coolant rising, fuel trim trending, RPM dropping |
| **Correlation** | Check relationship between multiple sensors | RPM vs Speed mismatch, MAP vs Throttle correlation |
| **Composite** | Combine other rule findings with AND/OR logic | Multi-system failure detection, confirmation rules |

### Key Features

| Feature | Description |
|---------|-------------|
| **YAML Configuration** | Human-readable rule definitions with full validation |
| **Pydantic Validation** | Type-safe, validated rule models with clear errors |
| **4 Evaluator Types** | Threshold, Trend, Correlation, Composite |
| **Sensor History** | Time-windowed readings for trend analysis (configurable retention) |
| **Cooldown Mechanism** | Prevents duplicate findings (per-rule configurable) |
| **Missing Data Policies** | SKIP_RULE, TREAT_AS_NORMAL, TREAT_AS_ABNORMAL, USE_DEFAULT |
| **Confidence Scoring** | Multi-factor confidence (sensor validity, freshness, samples, evidence) |
| **Severity Escalation** | Auto-escalate based on related findings |
| **AI Context Integration** | Rule findings included in AI diagnostic prompt |
| **History Persistence** | SQLite storage for audit trail and trend analysis |
| **Test Coverage** | 108 tests (loader: 32, evaluator: 44, engine: 32) |

### Example Rule Definition (YAML)

```yaml
rules:
  - rule_id: "RULE_COOLANT_OVERHEAT"
    name: "Coolant Overheat Detection"
    description: "Detects engine coolant temperature exceeding safe threshold"
    category: "cooling"
    rule_type: "threshold"
    enabled: true
    severity: "high"
    priority: 2
    confidence: 0.9
    conditions:
      - sensor_name: "coolant_temp_c"
        sensor_unit: "°C"
        operator: "greater_than"
        threshold: 105.0
    explanation_template: "Coolant temperature at {coolant_temp_c}°C exceeds 105°C threshold"
    recommended_checks:
      - "Check coolant level and condition"
      - "Inspect radiator for blockage"
      - "Verify thermostat operation"
    recommended_actions:
      - "Replace thermostat"
      - "Flush and refill coolant system"
    safety_notes:
      - "Hot coolant can cause severe burns - allow engine to cool before opening system"
    source: "generic_obd"
    dtc_hints: ["P0217"]
    cooldown_seconds: 300
```

### Trend Rule Example

```yaml
  - rule_id: "RULE_COOLANT_RISING_TREND"
    name: "Coolant Temperature Rising Trend"
    category: "cooling"
    rule_type: "trend"
    severity: "medium"
    conditions:
      - sensor_name: "coolant_temp_c"
        trend_operator: "rate_above"
        trend_window_seconds: 120
        min_samples: 10
        rate_threshold: 0.5  # °C per second
```

### Correlation Rule Example

```yaml
  - rule_id: "RULE_RPM_SPEED_MISMATCH"
    name: "RPM vs Speed Mismatch (Possible Transmission Slip)"
    category: "transmission"
    rule_type: "correlation"
    severity: "high"
    conditions:
      - sensor_name: "engine_rpm"
        condition_group: "rpm_speed"
        logical_operator: "and"
      - sensor_name: "vehicle_speed_kmh"
        condition_group: "rpm_speed"
        logical_operator: "and"
    # Custom logic: RPM high but speed low = potential slip
```

### Composite Rule Example

```yaml
  - rule_id: "RULE_COOLING_SYSTEM_FAILURE"
    name: "Cooling System Failure (Composite)"
    category: "cooling"
    rule_type: "composite"
    severity: "critical"
    referenced_rule_ids:
      - "RULE_COOLANT_OVERHEAT"
      - "RULE_COOLANT_RISING_TREND"
    composite_logic: "and"
```

### Missing Data Policies

| Policy | Behavior |
|--------|----------|
| `skip_rule` | Skip entire rule if any required sensor missing |
| `treat_as_normal` | Assume missing sensor reads normal value |
| `treat_as_abnormal` | Assume missing sensor reads abnormal (conservative) |
| `use_default` | Use configured `default_value` for missing sensor |

### Confidence Calculation

```python
calculate_confidence(
    sensor_valid=True,      # Sensor reading is valid
    data_fresh=True,        # Data within freshness window
    sample_count=10,        # Number of historical samples
    min_samples=5,          # Minimum required samples
    condition_complete=True,# All conditions evaluated
    rule_reliability=0.8,   # Rule base confidence
    evidence_quality=0.8    # Quality of supporting evidence
)
# Factors: sensor_valid(25%), data_fresh(10%), samples(30%), condition(15%), rule(10%), evidence(10%)
```

### Severity Escalation

- **2+ HIGH findings** → Escalate base severity by one level
- **3+ MEDIUM findings** → Escalate base severity by one level  
- **1+ CRITICAL finding** → Escalate to CRITICAL

### Integration with AI Diagnostic Engine

Rule findings are automatically included in the AI diagnostic context:

```
Rule Engine Findings → AI Context Builder → Diagnostic Prompt → LM Studio
```

The AI receives:
- List of triggered rule IDs
- Finding summaries with severity and confidence
- Observed vs expected values
- Recommended checks and actions from rules

This provides deterministic, explainable evidence alongside AI reasoning.

### Diagnostics Page - Rule Engine Panel

**3-Column Layout** (DTC Scan | AI Diagnosis | Rule Engine):

1. **Run Rule Evaluation Button** - One-click evaluation against current sensor data
2. **Findings Display** - Color-coded severity badges (Critical/High/Medium/Low/Info)
3. **Finding Details** - Explanation, observed values, evidence, recommendations
4. **Statistics Panel** - Rules evaluated, triggered, skipped, execution time, data quality
5. **History Panel** - Past evaluations with findings (from database)

### Configuration

```python
# config.py - Rule Engine Configuration
RULE_ENGINE_CONFIG = {
    "rules_dir": "rules",              # Directory with YAML rule files
    "max_history_age_seconds": 300,    # Sensor history retention (5 min)
    "default_cooldown_seconds": 300,   # Default finding cooldown
    "data_quality_thresholds": {       # For data quality assessment
        "excellent": 0.9,
        "good": 0.7,
        "fair": 0.5
    }
}
```

### Programmatic Usage

```python
from services import get_rule_engine
from services.types import SensorReading
from datetime import datetime

engine = get_rule_engine()

# Add sensor readings for trend analysis
readings = [
    SensorReading(pid="coolant_temp_c", name="coolant_temp_c", value=95.0, unit="°C",
                 timestamp=datetime.now(), is_simulated=True),
    SensorReading(pid="engine_rpm", name="engine_rpm", value=800, unit="RPM",
                 timestamp=datetime.now(), is_simulated=True)
]
engine.add_sensor_readings(readings)

# Evaluate rules against current readings
current = {
    "coolant_temp_c": SensorReading(pid="coolant_temp_c", name="coolant_temp_c", value=108.0, unit="°C",
                                   timestamp=datetime.now(), is_simulated=True)
}
result = engine.evaluate(current)

# Access findings
for finding in result.findings:
    print(f"{finding.severity.value.upper()}: {finding.rule_id} - {finding.explanation}")

# Get AI context for diagnostic engine
ai_context = engine.get_ai_context_text()
# Includes: "DETERMINISTIC RULE ENGINE FINDINGS" section

# Get statistics
stats = engine.get_statistics()
print(f"Loaded: {stats['total_rules_loaded']}, Enabled: {stats['enabled_rules']}")

# Get history
history = engine.get_evaluation_history(limit=20)
```

### Testing

```bash
# All rule engine tests
pytest tests/test_rule_loader.py tests/test_rule_evaluator.py tests/test_rule_engine.py -v

# Specific component
pytest tests/test_rule_loader.py -v      # 32 tests
pytest tests/test_rule_evaluator.py -v   # 44 tests
pytest tests/test_rule_engine.py -v      # 32 tests

# Full test suite
pytest tests/ -v                         # 241 tests total
```

### Rule Files Location

Rules are stored in the `rules/` directory:
- `example_rules.yaml` - Template with all rule types
- `cooling_rules.yaml` - Cooling system rules
- `fuel_rules.yaml` - Fuel system rules
- `ignition_rules.yaml` - Ignition system rules
- `emissions_rules.yaml` - Emissions rules
- `electrical_rules.yaml` - Electrical system rules
- `transmission_rules.yaml` - Transmission rules

### Safety & Limitations

- **Deterministic only** - No ML/ML randomness, fully reproducible
- **Explainable** - Every finding shows rule, condition, threshold, observed value
- **No code clearing** - Read-only diagnostic operations
- **Simulation data labeled** - All demo findings show data source
- **Cooldown prevents spam** - Configurable per-rule
- **Local only** - No cloud dependencies

---

## Professional Reporting Engine (V2 Phase 4)

The application now includes a complete **Professional Reporting Engine** that transforms vehicle, diagnostic, rule evaluation, telemetry, performance, and maintenance data into professional, downloadable PDF and HTML reports.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    REPORTING ENGINE                             │
├─────────────────────────────────────────────────────────────────┤
│  ReportDataBuilder  →  ReportGenerator  →  Renderers           │
│  (Data Assembly)        (Orchestrator)      - HTML (Jinja2)    │
│                          ↓              - PDF (ReportLab)      │
│              ReportModels (Pydantic)                         │
│  - ReportMetadata      - VehicleInfo                         │
│  - DiagnosticReportData   - VehicleHealthReportData          │
│  - PerformanceReportData  - MaintenanceReportData            │
│  - Enums: ReportType, ReportFormat, DataSource              │
└─────────────────────────────────────────────────────────────────┘
```

### Core Components

| Component | Purpose |
|-----------|---------|
| **ReportModels** | Pydantic models for type-safe report data structures (4 report types + enums) |
| **ReportDataBuilder** | Assembles report data from existing services (Database, DiagnosticEngine, RuleEngine, OBD) |
| **HTMLRenderer** | Jinja2-based HTML generation with autoescaping, offline-capable, print-optimized |
| **PDFRenderer** | ReportLab-based PDF generation (pure Python, Windows-compatible) |
| **ReportGenerator** | Orchestrator combining data building + rendering, batch generation, file output |

### Report Types

| Report Type | Description | Data Sources |
|-------------|-------------|--------------|
| **Comprehensive Diagnostic** | Full diagnostic scan with DTCs, AI diagnosis, rule findings, telemetry summary | Diagnostic DB, AI sessions, Rule engine, Telemetry |
| **Vehicle Health** | Overall condition, component statuses, DTC summary, maintenance history, safety observations | Diagnostic DB, Maintenance DB, Rule findings, Telemetry |
| **Performance** | Session statistics, sensor min/max/avg/std, charts, driving patterns | Telemetry sessions, Telemetry records |
| **Maintenance** | Service history, upcoming/overdue items, cost analysis (INR), manufacturer intervals | Maintenance records, Vehicle profile |

### Key Features

| Feature | Description |
|---------|-------------|
| **4 Report Types** | Diagnostic, Vehicle Health, Performance, Maintenance |
| **Dual Format Output** | HTML (Jinja2) and PDF (ReportLab) |
| **Data Provenance** | Every report shows data source: REAL, SIMULATION, MIXED, UNKNOWN |
| **HTML Escaping** | Jinja2 autoescape prevents XSS — no manual sanitization needed |
| **Offline HTML** | Embedded CSS, no external dependencies, print-optimized |
| **Windows PDF** | Pure Python ReportLab — no LaTeX, no wkhtmltopdf, no external tools |
| **INR Cost Estimates** | Maintenance costs labeled as estimates in Indian Rupees |
| **Unique Report IDs** | 8-character unique identifiers for traceability |
| **Safe File Naming** | Atomic writes, no overwrites, timestamped filenames |
| **Batch Generation** | Generate all 4 reports at once in HTML or PDF |
| **Streamlit UI** | 3-tab interface: Generate, Preview, Download with source/format selection |

### Data Provenance (Transparency)

Each report includes a **Data Provenance** section showing:
- **REAL** — Data from actual OBD-II connection
- **SIMULATION** — Data from software simulation
- **MIXED** — Combination of real and simulated data
- **UNKNOWN** — Source indeterminate

This ensures users always know the origin of the data they're reading.

### HTML Templates (Jinja2)

Located in `services/report_templates/`:
- `base.html` — Base template with CSS, fonts, print styles, header/footer
- `diagnostic_report.html` — DTCs, AI diagnosis, rule findings, telemetry, recommendations
- `vehicle_health_report.html` — Overall conclusion, components, maintenance, safety
- `performance_report.html` — Session summary, sensor statistics, charts placeholder
- `maintenance_report.html` — History, upcoming/overdue, cost analysis, intervals

**Security**: All templates use `{{ variable }}` with Jinja2's `select_autoescape(['html', 'xml'])` — no `|safe` filters, no manual HTML construction.

### PDF Generation (ReportLab)

- **Title Page**: Report type, vehicle info, report ID, generation timestamp, data source badge
- **Table of Contents**: Auto-generated from section headings
- **Professional Tables**: Styled tables with alternating rows, headers, page breaks
- **Page Numbers**: Bottom center on every page
- **Headers/Footers**: Report title, page X of Y, generation date
- **Unicode Support**: DejaVu fonts for international characters
- **INR Currency**: ₹ symbol support in maintenance reports

### Streamlit Reports Page

Accessible from sidebar navigation:

**Tab 1 — Generate**: 
- 4 report cards with descriptions and data source info
- Source selector per report (Simulation / Real / Mixed)
- Format selector (HTML / PDF)
- Batch "Generate All" button

**Tab 2 — Preview**:
- In-browser HTML preview (iframe)
- Works for both HTML and PDF (PDF shows first page as image if available)

**Tab 3 — Download**:
- List of generated reports with unique IDs
- One-click HTML/PDF download
- File size and generation timestamp

### Programmatic Usage

```python
from services import ReportGenerator
from services.report_models import ReportFormat, ReportType

# Single report
generator = ReportGenerator()
html = generator.generate_diagnostic_report(format_type=ReportFormat.HTML)
pdf_bytes = generator.generate_diagnostic_report(format_type=ReportFormat.PDF)

# Save to file
generator.generate_diagnostic_report(
    format_type=ReportFormat.HTML,
    output_path=Path("reports/diagnostic_report.html")
)

# Batch generate all 4 reports
results = generator.generate_all_reports(
    format_type=ReportFormat.PDF,
    output_dir=Path("reports/batch")
)
# Returns: {ReportType.DIAGNOSTIC: Path, ...}
```

### Convenience Functions

```python
from services.report_generator import (
    generate_diagnostic_report,
    generate_vehicle_health_report,
    generate_performance_report,
    generate_maintenance_report,
)

# Direct function calls
html = generate_diagnostic_report(format_type=ReportFormat.HTML)
pdf_path = generate_maintenance_report(
    format_type=ReportFormat.PDF,
    output_path=Path("maintenance.pdf")
)
```

### Configuration

```python
# No additional config required — uses existing DatabaseService
# Templates auto-located at services/report_templates/
# Output directory defaults to reports/
```

### Dependencies Added (requirements.txt)

- `jinja2>=3.1.0` — HTML template engine with autoescaping
- `reportlab>=4.0.0` — Pure Python PDF generation

### Testing

```bash
# All reporting tests
pytest tests/test_report_models.py tests/test_report_data_builder.py tests/test_report_renderers.py tests/test_report_generator.py -v

# Specific component
pytest tests/test_report_models.py -v        # 50+ tests
pytest tests/test_report_data_builder.py -v  # 12 tests
pytest tests/test_report_renderers.py -v     # 16 tests
pytest tests/test_report_generator.py -v     # 20 tests

# Full test suite (326 tests)
pytest tests/ -v
```

### Safety & Limitations

- **No fabricated health scores** — Reports show actual data, not computed "health percentages"
- **Simulation data clearly labeled** — Every report shows data source badge
- **INR costs are estimates** — Maintenance costs labeled as "Estimated (INR)"
- **Charts in PDF** — Currently table-based summaries (static chart images require kaleido)
- **Large telemetry** — Reports summarize; full data available via CSV export
- **Read-only** — No database modifications during report generation
- **No cloud dependencies** — All rendering runs locally

---

## AI Diagnostic Engine (V2 Phase 2)

The application now includes a complete **AI-powered diagnostic engine** that transforms vehicle telemetry and DTC data into structured, evidence-based diagnostic reports using local LM Studio inference.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    DIAGNOSTIC ENGINE                            │
├─────────────────────────────────────────────────────────────────┤
│  DiagnosticContextBuilder  →  DiagnosticPromptBuilder          │
│  (OBD + DB + Knowledge)      (System Prompt + Context + Schema)│
│                          ↓                                       │
│              LM Studio (Qwen2.5 3B Instruct)                   │
│                          ↓                                       │
│              JSON Response Validation (Pydantic)               │
│                          ↓                                       │
│  DiagnosticResult ←  DiagnosticOrchestrator  →  Database       │
│  (Structured Output)       (Retry + Reconcile)    (Persistence) │
└─────────────────────────────────────────────────────────────────┘
```

### Core Components

| Component | Purpose |
|-----------|---------|
| **DiagnosticContextBuilder** | Gathers vehicle profile, live sensor readings, DTCs, freeze frame, telemetry trends, diagnostic history, unsupported PIDs, and knowledge passages |
| **KnowledgeBase** | Lightweight local RAG with built-in automotive knowledge (DTC explanations, diagnostic principles, i20-specific issues) |
| **DiagnosticPromptBuilder** | Constructs detailed system prompt with JSON schema, vehicle context, and diagnostic instructions |
| **DiagnosticEngine (Orchestrator)** | Coordinates context building → AI call → response parsing → validation → reconciliation → persistence |
| **Pydantic Models** | Type-safe, validated structured output (DiagnosticResult, ProbableCause, Recommendations, etc.) |

### Structured Diagnostic Output

The AI produces a complete **DiagnosticResult** JSON with:

```json
{
  "diagnosis_id": "diag_20240115_143022_abc123",
  "diagnostic_status": "complete",
  "severity": "major",
  "confidence": 0.85,
  "summary": "Engine misfire with lean condition - likely ignition/fuel issue",
  "detected_symptoms": ["Rough idle", "Check engine light"],
  "confirmed_faults": ["P0300", "P0171"],
  "primary_diagnosis": {
    "code": "P0300",
    "description": "Random/Multiple Cylinder Misfire",
    "probable_causes": [
      {
        "cause": "Faulty ignition coil(s)",
        "explanation": "Common on Kappa 1.2L cylinders 2&3",
        "confidence": 0.80,
        "supporting_evidence": ["P0300 present", "Rough idle"],
        "contradictory_evidence": [],
        "verification_steps": ["Swap coil test", "Check coil resistance"],
        "urgency": "soon"
      }
    ],
    "confidence": 0.85,
    "severity": "major"
  },
  "secondary_diagnoses": [...],
  "recommended_actions": [
    {
      "recommendation": "Replace faulty ignition coil(s)",
      "rationale": "High probability cause on this engine",
      "priority": 2,
      "safety_level": "professional",
      "requires_professional": true,
      "estimated_cost_inr": "₹2,000-₹4,000"
    }
  ],
  "safety_warnings": [],
  "missing_information": ["Freeze frame data", "Compression test"],
  "data_quality": "good",
  "dtc_references": ["P0300", "P0171"],
  "rule_engine_findings": ["RULE_MISFIRE_DETECTED"],
  "rag_sources": ["builtin:P0300", "builtin:hyundai_i20_kappa"]
}
```

### Key Features

| Feature | Description |
|---------|-------------|
| **Structured JSON Output** | Validated against Pydantic schema with confidence scores (0.0-1.0) |
| **Probable Causes Ranking** | Multiple causes per diagnosis, ranked by probability with evidence |
| **Verification Steps** | Specific actionable steps to confirm each probable cause |
| **Repair Recommendations** | Prioritized actions with safety levels (Safe/Caution/Professional) |
| **Cost Estimates (INR)** | Indian market repair cost estimates for each recommendation |
| **Safety Warnings** | Critical safety issues flagged prominently |
| **Data Source Labeling** | Clear SIMULATION vs REAL data distinction |
| **RAG Knowledge Integration** | Local knowledge base (DTC explanations, diagnostic principles, i20 specifics) |
| **History Persistence** | All AI diagnoses saved to SQLite with full structured output |
| **Contradictory Evidence** | AI must list evidence against each probable cause |
| **Missing Information** | Identifies what additional data would improve diagnosis |

### Knowledge Base

The local RAG knowledge base includes:

- **DTC Explanations**: P0300, P0171, P0420, P0128 with causes and verification
- **Diagnostic Principles**: Fuel trim analysis, cooling system, ignition system
- **Vehicle-Specific**: Hyundai i20 Asta 2023 1.2L Kappa common issues
- **Extensible**: Add custom documents via database (`rag_documents` table)

### Integration Points

**Diagnostics Page** → "🧠 Run AI Diagnosis" button → Structured result panel with:
- Overall severity, confidence, data source badge
- Primary/secondary diagnoses with probable causes
- Evidence (supporting/contradictory)
- Verification steps with urgency badges
- Prioritized recommendations with safety levels and INR costs
- Safety warnings and missing information

**AI Assistant Page** → "Diagnostic Mode" tab → DTC/Symptom input → Full analysis

### Configuration (config.py)

```python
AI_DIAGNOSTIC_CONFIG = {
    "model": "qwen2.5-3b-instruct",
    "temperature": 0.1,           # Low for consistent structured output
    "max_tokens": 4096,
    "structured_output": True,    # Enable JSON schema validation
    "rag_enabled": True,          # Enable knowledge retrieval
    "confidence_threshold": 0.5,  # Minimum confidence for conclusive
}
```

### Data Quality Assessment

The engine assesses input data quality automatically:

| Quality | Criteria |
|---------|----------|
| **Excellent** | Complete telemetry + DTCs + key sensors (RPM, coolant, load) + fresh data |
| **Good** | Good telemetry coverage + DTCs |
| **Fair** | Partial telemetry |
| **Poor** | Minimal data |
| **None** | No usable data |

### Safety & Limitations

- **Simulation data clearly labeled** — All demo diagnoses show "SIMULATION DATA — NOT ACTUAL VEHICLE DATA"
- **No code clearing** — Read-only diagnostic operations only
- **Professional verification required** — Safety-critical recommendations flagged as `requires_professional: true`
- **Confidence scoring** — Low confidence diagnoses marked as `inconclusive` or `insufficient_data`
- **Local only** — No cloud dependencies, all inference runs on your LM Studio

---

## Troubleshooting

### LM Studio Connection Issues
| Problem | Solution |
|---------|----------|
| "Cannot connect to LM Studio" | Ensure LM Studio is running and **Developer → Start Server** is clicked |
| "Model not found" | Load Qwen2.5 3B Instruct in LM Studio; check exact model name in Developer tab |
| "Request timeout" | Increase `LM_STUDIO_TIMEOUT` in `.env` (try 60-120s for slower GPUs) |
| Slow responses | Use smaller quantization (q4_k_m vs q8_0), ensure GPU acceleration is enabled |

### OBD-II Connection Issues
| Problem | Solution |
|---------|----------|
| "Connection failed" | Verify adapter is paired/connected, correct COM port, ignition ON |
| "No data / timeout" | Some vehicles require specific protocol — try setting `OBD_PROTOCOL` (6=CAN 11bit 500kbps, 7=CAN 29bit 500kbps, 5=ISO 14230 KWP fast, 4=ISO 14230 KWP 5 baud init) |
| "Unsupported PIDs" | Not all PIDs are supported by all ECUs — this is normal; check PID discovery results |
| "ELM327 not responding" | Try different baudrate (38400, 115200, 9600, 57600); check adapter LED activity |
| "Bluetooth paired but no COM port" | In Windows Settings → Bluetooth → More Bluetooth options → COM Ports tab → Add incoming port |
| "Adapter works in other apps but not here" | Close other OBD apps; only one can hold the serial port; restart adapter |
| "Intermittent disconnections" | Enable auto-reconnect in Settings; check USB cable/Bluetooth range; increase health check interval |
| "Wrong vehicle data" | Ensure correct protocol; some Hyundai/Kia need protocol 6 (CAN 11-bit 500kbps) |

### Windows-Specific Issues
| Problem | Solution |
|---------|----------|
| "Access denied / COM port busy" | Close Device Manager, PuTTY, other terminal apps; restart adapter |
| "CH340 driver missing" | Install CH340 driver from manufacturer; Windows Update usually provides it |
| "FTDI driver conflict" | Uninstall old FTDI drivers; use Windows built-in driver |
| "Bluetooth COM port changes" | Use Settings → OBD-II → Auto-Detect each time; or set fixed COM port in Bluetooth settings |

### Adapter Compatibility Notes

**Known Working Configurations (Hyundai i20 Asta 2023):**
- VGate vLinker FS USB @ 38400 baud, Protocol AUTO (negotiates to 6)
- OBDLink MX+ Bluetooth @ 38400 baud, Protocol 6
- Generic ELM327 v1.5 USB @ 38400 baud, Protocol 6

**Adapters with Known Issues:**
- Very cheap ELM327 clones (< $10) — often have firmware bugs, slow response
- ELM327 v2.1+ Bluetooth — may need specific pairing sequence
- WiFi adapters — ensure phone/laptop connected to adapter's WiFi network first

**Protocol Selection for Hyundai/Kia:**
- **Protocol 6 (AUTO usually picks this)**: ISO 15765-4 CAN 11-bit 500 kbps — **Recommended for i20**
- Protocol 7: ISO 15765-4 CAN 29-bit 500 kbps — Some newer models
- Protocol AUTO: Let adapter negotiate — works in most cases

### Streamlit Issues
| Problem | Solution |
|---------|----------|
| Port 8501 in use | Change port: `streamlit run app.py --server.port=8502` |
| Theme not applying | Restart Streamlit; hard refresh browser (Ctrl+F5) |
| Module import errors | Ensure virtual environment is activated and `pip install -r requirements.txt` ran |

### Database Issues
| Problem | Solution |
|---------|----------|
| "Database locked" | Close other instances; check file permissions on `data/i20_garage.db` |
| "Corrupt database" | Delete `data/i20_garage.db` — it will be recreated on next start |

---

## Development

### Adding New Features
1. Create module in `modules/` with `render_<feature>()`
2. Add navigation item in `components/sidebar.py`
3. Register in `app.py` page routing
4. Add tests in `tests/`

### Code Style
- Type hints for all public functions
- Google-style docstrings
- Custom exceptions for service errors
- Singleton pattern for services (`get_<service>()`)

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- **LM Studio** — Local LLM inference server
- **Qwen2.5** — Alibaba Cloud's open-weight model
- **Streamlit** — Rapid data app framework
- **Plotly** — Interactive visualizations
- **python-OBD** — OBD-II communication library
- **Hyundai Motor India** — Vehicle specifications reference

---

## Support

For issues, feature requests, or contributions:
- Check [Troubleshooting](#troubleshooting) first
- Review existing issues
- Create detailed bug reports with:
  - OS / Python version
  - LM Studio version
  - Steps to reproduce
  - Error messages / logs

---

**Built with ❤️ for the automotive enthusiast community**

*Drive safe. Diagnose smart.*
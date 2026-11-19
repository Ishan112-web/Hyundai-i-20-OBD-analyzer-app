# i20 AI Garage

**A complete automotive intelligence application for the 2023 Hyundai i20 Asta 1.2L Petrol**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.67+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey.svg)](https://github.com)

---

## Current Development Phase: **Phase 6 Complete** ✅

> **Phases 1–6 fully implemented.** The application includes: real-time dashboard, AI-powered diagnostics, deterministic rule engine, professional reporting (HTML/PDF), maintenance tracking, performance analytics, vehicle profile, AI assistant, and a complete design system with responsive UI. All core features are production-ready.

---

## Overview

i20 AI Garage is a **locally-running** automotive diagnostics and intelligence application built for the **2023 Hyundai i20 Asta 1.2L naturally aspirated petrol manual (India market)**. It provides:

- Professional-grade real-time dashboard
- AI-powered diagnostic assistance (local LM Studio)
- Deterministic rule-based diagnostics (YAML + Pydantic)
- Professional reports (HTML/PDF) with data provenance
- Maintenance tracking & performance analytics
- Real OBD-II connectivity (ELM327) or simulation mode

**No cloud dependencies** — everything runs on your machine.

---

## Key Features

| Feature | Description |
|---------|-------------|
| 🏁 **Dashboard** | Real-time gauges, live telemetry charts, 5 simulation scenarios, session recording |
| 🔧 **Diagnostics** | DTC scanning, AI diagnosis (structured JSON), deterministic rule engine, history |
| 📊 **Performance** | Session recording, historical charts, statistics, CSV export, session comparison |
| 🛠️ **Maintenance** | Service records (12 types), upcoming alerts, cost estimates (INR), filters |
| 🤖 **AI Assistant** | Chat + Diagnostic modes, LM Studio (Qwen2.5 3B), conversation history |
| 🧠 **AI Diagnostic Engine** | Structured JSON output, probable causes with confidence, verification steps, INR cost estimates, RAG knowledge base |
| 📐 **Rule Engine** | 4 evaluator types (Threshold, Trend, Correlation, Composite), YAML rules, sensor history, cooldown, SQLite persistence |
| 📄 **Reports** | 4 types (Diagnostic, Vehicle Health, Performance, Maintenance) → HTML/PDF, data provenance, Jinja2 + ReportLab |
| 🚗 **Vehicle Profile** | Complete specs, OBD connection status, supported PIDs, VIN/CALID/CVN |
| ⚙️ **Settings** | OBD, AI, simulation, data management, backup/export |

---

## Quick Start

### Prerequisites
- Python 3.11+
- LM Studio with **Qwen2.5 3B Instruct GGUF** loaded and server running (`http://localhost:1234/v1`)
- (Optional) ELM327 OBD-II adapter for real vehicle data

### Installation

```powershell
# 1. Clone
git clone https://github.com/Ishan112-web/Hyundai-i-20-OBD-analyzer-app.git
cd Hyundai-i-20-OBD-analyzer-app

# 2. Virtual environment
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure LM Studio (optional - uses defaults)
copy .env.example .env
# Edit .env if needed

# 4. Run
.\run.ps1          # Windows PowerShell (recommended)
# OR
streamlit run app.py
```

**Open http://localhost:8501**

---

## Project Structure

```
i20-AI/
├── app.py                 # Main Streamlit app
├── config.py              # All configuration (OBD, PID polling, engine specs, thresholds)
├── requirements.txt
├── .env.example           # Environment template
├── run.ps1 / run.bat      # Startup scripts
│
├── services/              # Core business logic
│   ├── database.py        # SQLite (9 tables + AI diagnoses, RAG docs)
│   ├── ai_service.py      # LM Studio client with structured JSON
│   ├── obd_service.py     # OBD abstraction (sim + real)
│   ├── real_obd_adapter.py # ELM327 communication
│   ├── connection_manager.py # Auto-detect, reconnection, profiles
│   ├── diagnostic_engine.py # AI Diagnostic Engine (Context + RAG + Orchestrator)
│   ├── rule_engine.py     # Deterministic Rule Engine (4 evaluators)
│   ├── report_generator.py # Professional Reporting (HTML/PDF)
│   └── report_templates/  # Jinja2 templates (4 report types)
│
├── modules/               # Streamlit page modules
│   ├── dashboard.py
│   ├── diagnostics.py     # DTC + AI Diagnosis + Rule Engine (3-column)
│   ├── performance.py
│   ├── maintenance.py
│   ├── vehicle_profile.py
│   ├── ai_assistant.py
│   ├── obd_connection.py
│   └── reports.py         # 3 tabs: Generate, Preview, Download
│
├── components/            # Reusable UI components
│   ├── sidebar.py         # Navigation + OBD status
│   ├── status_cards.py
│   └── charts.py
│
├── rules/                 # YAML rule definitions (7 categories)
├── tests/                 # 326 tests (database, AI, OBD, rules, reports)
├── data/                  # SQLite database (auto-created)
└── reports/               # Exported reports
```

---

## Configuration

### Environment Variables (`.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `LM_STUDIO_BASE_URL` | `http://localhost:1234/v1` | LM Studio API endpoint |
| `LM_STUDIO_MODEL` | `qwen2.5-3b-instruct` | Model identifier |
| `LM_STUDIO_TEMPERATURE` | `0.7` | Sampling temperature |
| `OBD_MODE` | `simulation` | `simulation` or `real` |
| `OBD_PORT` | `COM3` | Serial port (Windows) |
| `OBD_BAUDRATE` | `38400` | Serial baud rate |
| `OBD_PROTOCOL` | `AUTO` | OBD protocol (6=CAN 11-bit 500kbps for Hyundai) |

### Key Config Objects (`config.py`)

- **ENGINE_SPECS** — i20 1.2L Kappa (83 PS @ 6000 RPM, 115 Nm @ 4000 RPM)
- **PID_POLLING_CONFIG** — Priority-based polling (10Hz critical, 1Hz low)
- **GAUGE_THRESHOLDS** — Visual status thresholds (green/amber/red)
- **RULE_ENGINE_CONFIG** — Rules dir, history retention, cooldown

---

## Simulation Scenarios

| Scenario | RPM Range | Speed Range | Coolant Temp |
|----------|-----------|-------------|--------------|
| **Idle** | 700–900 | 0 | 85–95°C |
| **City** | 1000–3000 | 0–50 km/h | 85–100°C |
| **Highway** | 2000–3500 | 60–120 km/h | 90–98°C |
| **Acceleration** | 2000–6200 | 0–140 km/h | 90–105°C |
| **Overheating** | 1500–4000 | 20–80 km/h | 105–125°C |

> ⚠️ Overheating is a **software demo only** — does not affect real vehicle.

---

## OBD-II Real Vehicle Support

- **Adapters**: USB, Bluetooth, WiFi ELM327
- **Protocols**: Auto-detect, CAN 11-bit (6), CAN 29-bit (7), KWP2000
- **PIDs**: 10+ real-time sensors with priority polling
- **DTC Modes**: $03 (current), $07 (pending), $02 (freeze frame proxy)
- **Auto-reconnect**: Health check + exponential backoff (1s→30s, 5 attempts)
- **Profile persistence**: Save successful connections for instant reconnect

> **Safety**: Read-only operations only. No ECU flashing, actuator tests, or emissions tampering.

---

## Testing

```powershell
.venv\Scripts\activate
pytest tests/ -v              # All 326 tests
pytest tests/test_rule_engine.py -v      # Rule engine (32 tests)
pytest tests/test_diagnostic_engine.py -v # AI diagnostics (37 tests)
pytest tests/test_report_generator.py -v  # Reports (20 tests)
```

---

## Development Phases

| Phase | Status | Deliverables |
|-------|--------|--------------|
| **1** | ✅ Complete | Dashboard, simulation, basic OBD, Streamlit UI |
| **2** | ✅ Complete | AI Diagnostic Engine (structured JSON, RAG, Pydantic) |
| **3** | ✅ Complete | Deterministic Rule Engine (4 evaluators, YAML, history) |
| **4** | ✅ Complete | Professional Reports (4 types, HTML/PDF, provenance) |
| **5** | ✅ Complete | Vehicle Profile, Maintenance, Performance, AI Assistant |
| **6** | ✅ Complete | Design System, Responsive UI, Cross-page review, Settings audit |

---

## License

MIT License — see [LICENSE](LICENSE)

---

## Acknowledgments

- **LM Studio** — Local LLM inference
- **Qwen2.5** — Alibaba Cloud open-weight model
- **Streamlit** — Data app framework
- **Plotly** — Visualizations
- **python-OBD** — OBD-II communication
- **ReportLab / Jinja2** — PDF & HTML rendering

---

**Built for automotive enthusiasts** · *Drive safe. Diagnose smart.*
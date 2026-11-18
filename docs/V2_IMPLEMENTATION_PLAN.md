# i20 AI Garage V2 - Implementation Plan

## Executive Summary

This document outlines the implementation plan for upgrading i20 AI Garage from V1 (simulation-only dashboard) to V2 (real vehicle connectivity with AI-powered diagnostics). The audit reveals a solid V1 foundation with 7-page Streamlit app, SQLite persistence, LM Studio integration, and 47 passing tests.

---

## 1. Current V1 Architecture Summary

### 1.1 Project Structure

```
C:/i20-AI/
├── app.py                      # Main entry point (24KB, 7-page navigation)
├── config.py                   # All configuration (310 lines)
├── components/
│   └── sidebar.py              # Navigation, vehicle status, connection indicators
├── services/
│   ├── __init__.py
│   ├── database.py             # SQLite with 7 tables, CRUD operations
│   ├── ai_service.py           # LM Studio client (OpenAI-compatible API)
│   └── obd_service.py          # OBD abstraction + SimulationEngine (470 lines)
├── modules/
│   ├── dashboard.py            # Real-time gauges, telemetry, live charts
│   ├── diagnostics.py          # DTC scanner, detail view, reports
│   ├── performance.py          # Session stats, charts, export
│   ├── vehicle_profile.py      # Vehicle info, specs, connection status
│   ├── settings.py             # 6-tab settings UI
│   ├── ai_assistant.py         # Chat interface with streaming
│   └── maintenance.py          # Service records, upcoming maintenance
├── tests/
│   ├── test_database.py        # 12 tests
│   ├── test_ai_service.py      # 9 tests
│   ├── test_obd_service.py     # 16 tests
│   └── test_simulation.py      # 10 tests
├── requirements.txt            # Dependencies
└── docs/
    └── V2_IMPLEMENTATION_PLAN.md  # This document
```

### 1.2 Core Services (Singleton Pattern)

| Service | File | Key Features |
|---------|------|--------------|
| **Database** | `services/database.py` | 7 tables, parameterized SQL, indexes, backup/export |
| **AI Service** | `services/ai_service.py` | LM Studio client, streaming, vehicle context, model caching |
| **OBD Service** | `services/obd_service.py` | SimulationEngine (5 scenarios), SensorReading/DTC dataclasses, gauge thresholds |

### 1.3 Data Flow (V1)

```
User Interaction → Module UI → Service Layer → SQLite / SimulationEngine
                              ↓
                         LM Studio API (AI Assistant)
```

### 1.4 Key Dataclasses

```python
# SensorReading - telemetry data point
pid: str, name: str, value: Any, unit: str, timestamp: datetime, is_simulated: bool

# DTC - diagnostic trouble code
code: str, description: str, severity: str, status: str, is_demo: bool
```

### 1.5 Simulation Engine (5 Scenarios)

| Scenario | RPM Range | Speed Range | Coolant Range | Key Behavior |
|----------|-----------|-------------|---------------|--------------|
| idle | 700-950 | 0 | 85-95 | Stable, speed clamped to 0 |
| city | 700-3000 | 0-50 | 85-100 | Stop-and-go, random stops/accel |
| highway | 2000-3500 | 60-120 | 90-100 | Steady with minor variation |
| acceleration | 1000-6500 | 0-180 | 90-105 | Progressive accel, shift points |
| overheating | 800-2500 | 0-60 | 90-125 | Gradual temp rise, enrichment |

---

## 2. V2 Specification Gap Analysis

### 2.1 V2 Requirements (from specification)

| Category | V1 Status | V2 Requirement | Gap Severity |
|----------|-----------|----------------|--------------|
| **Real OBD Connectivity** | ❌ Placeholder only | ELM327 via python-OBD, auto-detect ports/protocols, PID discovery, reconnection | **Critical** |
| **Real Telemetry Acquisition** | ❌ Simulated only | Background polling thread, rate limiting, PID prioritization, unit conversion | **Critical** |
| **Real DTC Scanning** | ❌ Demo DTCs only | Mode $03 (current), $07 (pending), $0A (permanent), freeze frame data | **Critical** |
| **AI Diagnostic Engine** | ✅ Basic chat | Structured JSON output, confidence scores, severity classification, RAG with service manual | **High** |
| **Rule-Based Diagnostics** | ❌ None | Drools-like engine, threshold rules, trend rules, correlation rules, explainability | **High** |
| **Professional Reporting** | ❌ Basic text | PDF/HTML templates, DTC descriptions with OEM data, repair procedures, parts/labor estimates | **High** |
| **Database Migrations** | ❌ None | Alembic, versioned schema, V1→V2 migration, seed data | **Medium** |
| **Enhanced UI** | ✅ Functional | Real-time WebSocket, connection wizard, diagnostic workflow wizard | **Medium** |

---

## 3. Proposed V2 Architecture

### 3.1 New Service Structure

```
services/
├── __init__.py
├── database.py              # Enhanced with migrations
├── ai_service.py            # Enhanced with structured output
├── obd_service.py           # Real OBD + Simulation (refactored)
├── diagnostic_engine.py     # NEW: AI + Rule-based diagnostics
├── report_generator.py      # NEW: Professional reports
└── migration_runner.py      # NEW: Alembic wrapper
```

### 3.2 New Module Structure

```
modules/
├── dashboard.py             # Enhanced with real/live toggle
├── diagnostics.py           # Enhanced with real DTC workflow
├── performance.py           # Enhanced with real data
├── vehicle_profile.py       # Enhanced with OBD info
├── settings.py              # Enhanced with OBD config wizard
├── ai_assistant.py          # Enhanced with diagnostic mode
├── maintenance.py           # Enhanced with predictions
└── obd_connection.py        # NEW: Connection wizard & monitor
```

---

## 4. Implementation Phases

### Phase 1: Real OBD Connectivity (Week 1-2) ⭐ **CRITICAL PATH**

#### 4.1.1 Files to Modify/Create

| File | Action | Description |
|------|--------|-------------|
| `services/obd_service.py` | **Major Refactor** | Integrate python-OBD, add real connection logic |
| `services/obd_service.py` | **Add** | `RealOBDAdapter` class for ELM327 communication |
| `services/obd_service.py` | **Add** | `PIDRegistry` for supported PID discovery |
| `services/obd_service.py` | **Add** | `ConnectionManager` for auto-reconnect, port detection |
| `modules/obd_connection.py` | **Create** | Connection wizard UI |
| `components/sidebar.py` | **Modify** | Real OBD status indicators |
| `config.py` | **Modify** | Add real OBD config options |

#### 4.1.2 Key Implementation Details

**Real OBD Adapter (`RealOBDAdapter` class):**
```python
class RealOBDAdapter:
    def __init__(self, port: str, baudrate: int, protocol: str):
        self.connection = obd.OBD(portstr=port, baudrate=baudrate, protocol=protocol)
        self.supported_pids = []
    
    def discover_supported_pids(self) -> List[str]:
        # Query PID 0x00, 0x20, 0x40, 0x60, 0x80, 0xA0, 0xC0
        pass
    
    def query_pid(self, pid: str) -> Optional[float]:
        # Use python-OBD command mapping
        pass
    
    def scan_dtcs(self) -> List[DTC]:
        # Mode $03, $07, $0A
        pass
    
    def get_freeze_frame(self, dtc_code: str) -> Dict:
        # Mode $02
        pass
```

**Connection Manager:**
- Auto-detect serial ports (`pyserial.tools.list_ports`)
- Test common baudrates (38400, 115200, 9600)
- Test protocols (Auto, ISO 15765-4 CAN, ISO 14230-4 KWP, etc.)
- Background health check thread (30s interval)
- Exponential backoff reconnection

**PID Prioritization:**
| Priority | PIDs | Poll Rate |
|----------|------|-----------|
| Critical | RPM (0x0C), Speed (0x0D), Coolant (0x05) | 10 Hz |
| High | Throttle (0x11), Load (0x04), MAP (0x0B) | 5 Hz |
| Medium | Fuel trims (0x06, 0x07), Voltage (0x42), MAF (0x10) | 2 Hz |
| Low | O2 sensors, catalyst, EVAP | 1 Hz |

#### 4.1.3 Database Changes

```sql
-- Add to telemetry_records
ALTER TABLE telemetry_records ADD COLUMN is_real BOOLEAN DEFAULT 0;
ALTER TABLE telemetry_records ADD COLUMN pid_source TEXT; -- 'simulation' | 'real'

-- New table for OBD connection logs
CREATE TABLE obd_connection_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT, -- 'connect', 'disconnect', 'error', 'reconnect'
    port TEXT,
    baudrate INTEGER,
    protocol TEXT,
    details TEXT
);

-- New table for supported PIDs cache
CREATE TABLE obd_supported_pids (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pid TEXT UNIQUE,
    name TEXT,
    unit TEXT,
    description TEXT,
    is_supported BOOLEAN DEFAULT 1
);
```

#### 4.1.4 Tests to Add

| Test File | Tests |
|-----------|-------|
| `tests/test_obd_real.py` | Port detection, connection, PID discovery, DTC scanning, freeze frame, reconnection |

---

### Phase 2: AI Diagnostic Engine (Week 2-3) ⭐ **HIGH VALUE**

#### 4.2.1 Files to Modify/Create

| File | Action | Description |
|------|--------|-------------|
| `services/ai_service.py` | **Major Enhancement** | Structured output, diagnostic prompts, RAG |
| `services/diagnostic_engine.py` | **Create** | Orchestrates AI + Rules |
| `modules/ai_assistant.py` | **Enhance** | Diagnostic mode, structured responses |
| `modules/diagnostics.py` | **Enhance** | AI diagnosis integration |
| `config.py` | **Modify** | AI diagnostic prompts, model params |

#### 4.2.2 AI Diagnostic Engine Design

**Structured Output Schema (JSON):**
```json
{
  "diagnosis_id": "diag_20240115_001",
  "timestamp": "2024-01-15T10:30:00Z",
  "vehicle_context": { "rpm": 2500, "speed_kmh": 80, ... },
  "dtcs": ["P0300", "P0171"],
  "primary_diagnosis": {
    "code": "P0300",
    "description": "Random/Multiple Cylinder Misfire",
    "probable_causes": [
      {"cause": "Faulty ignition coils", "probability": 0.45},
      {"cause": "Bad spark plugs", "probability": 0.30},
      {"cause": "Vacuum leak", "probability": 0.15},
      {"cause": "Fuel injector issues", "probability": 0.10}
    ],
    "confidence": 0.82,
    "severity": "major"
  },
  "secondary_diagnoses": [...],
  "recommended_actions": [
    {"action": "Inspect ignition coils", "priority": 1, "est_cost": "$150-300"},
    {"action": "Check spark plugs", "priority": 2, "est_cost": "$80-150"},
    {"action": "Smoke test for vacuum leaks", "priority": 3, "est_cost": "$100-200"}
  ],
  "rule_matches": ["RULE_001", "RULE_005"],
  "rag_sources": ["Hyundai i20 Service Manual Sec 3.2", "TSB 18-01-002"]
}
```

**System Prompt Enhancement:**
```python
AI_DIAGNOSTIC_SYSTEM_PROMPT = """You are an expert automotive diagnostician specializing in Hyundai vehicles.
Given DTC codes, live telemetry, and vehicle context, provide structured diagnosis.

OUTPUT FORMAT: JSON only, matching the DiagnosticOutput schema.
RULES:
1. Always include confidence scores (0.0-1.0)
2. Rank probable causes by probability
3. Reference Hyundai/Kia service bulletins where applicable
4. Consider i20 Asta 2023 specific known issues (Kappa 1.2L engine)
5. Flag safety-critical issues with severity="critical"
6. Include estimated repair costs in INR for Indian market"""
```

**RAG Integration:**
- Load Hyundai i20 service manual chunks (PDF parsing)
- Load TSBs (Technical Service Bulletins) 
- Vector store (ChromaDB or FAISS) for semantic search
- Inject relevant chunks into prompt context

#### 4.2.3 Database Changes

```sql
-- AI diagnostic sessions
CREATE TABLE ai_diagnostic_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    vehicle_context TEXT, -- JSON
    dtcs TEXT, -- JSON array
    ai_diagnosis TEXT, -- JSON
    rule_matches TEXT, -- JSON array
    user_feedback TEXT, -- 'confirmed' | 'rejected' | 'partial'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- RAG document store
CREATE TABLE rag_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT, -- 'service_manual', 'tsb', 'forum', 'custom'
    title TEXT,
    content TEXT,
    embedding BLOB, -- or reference to vector store
    metadata TEXT, -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

### Phase 3: Rule-Based Diagnostic Engine (Week 3) ⭐ **HIGH VALUE**

#### 4.3.1 Files to Create

| File | Description |
|------|-------------|
| `services/rule_engine.py` | Core rule engine (Drools-like but lightweight) |
| `services/rules/` | Rule definitions (YAML/JSON) |
| `services/rule_engine.py` | Rule loader, evaluator, explainer |

#### 4.3.2 Rule Engine Design

**Rule Types:**
```python
# Threshold Rule - single parameter exceeds limit
{
    "id": "RULE_001",
    "type": "threshold",
    "name": "Coolant Overheating",
    "parameter": "coolant_temp_c",
    "condition": ">",
    "threshold": 105,
    "severity": "critical",
    "dtc_hint": "P0217",
    "message": "Coolant temperature exceeds 105°C - immediate attention required"
}

# Trend Rule - parameter trending dangerously
{
    "id": "RULE_002",
    "type": "trend",
    "name": "Rapid Coolant Temp Rise",
    "parameter": "coolant_temp_c",
    "window_seconds": 60,
    "rate_threshold": 2.0,  # °C per minute
    "severity": "major",
    "dtc_hint": "P0128",
    "message": "Coolant temperature rising at {rate:.1f}°C/min - possible thermostat failure"
}

# Correlation Rule - multiple parameters related
{
    "id": "RULE_003",
    "type": "correlation",
    "name": "Lean Condition with High Fuel Trim",
    "conditions": [
        {"parameter": "stft_b1_pct", "condition": ">", "threshold": 15},
        {"parameter": "ltft_b1_pct", "condition": ">", "threshold": 10},
        {"parameter": "engine_load_pct", "condition": "<", "threshold": 50}
    ],
    "severity": "major",
    "dtc_hint": "P0171",
    "message": "Both STFT and LTFT elevated at low load - vacuum leak or MAF issue likely"
}

# Composite Rule - DTC + telemetry combination
{
    "id": "RULE_004",
    "type": "composite",
    "name": "Misfire with Rough Idle",
    "dtc_required": ["P0300", "P0301", "P0302", "P0303", "P0304"],
    "telemetry_conditions": [
        {"parameter": "rpm", "condition": "<", "threshold": 900},
        {"parameter": "engine_load_pct", "condition": "<", "threshold": 20}
    ],
    "severity": "major",
    "message": "Misfire DTC present with rough idle symptoms - check ignition system"
}
```

**Rule Engine API:**
```python
class RuleEngine:
    def load_rules(self, rule_dir: Path) -> None
    def evaluate(self, telemetry: Dict, dtcs: List[str]) -> List[RuleMatch]
    def explain(self, rule_match: RuleMatch) -> str  # Human-readable explanation
    def get_rule(self, rule_id: str) -> Rule
```

**Explainability Output:**
```python
{
    "rule_id": "RULE_003",
    "rule_name": "Lean Condition with High Fuel Trim",
    "matched_conditions": [
        {"parameter": "stft_b1_pct", "value": 18.5, "threshold": 15, "passed": true},
        {"parameter": "ltft_b1_pct", "value": 12.0, "threshold": 10, "passed": true},
        {"parameter": "engine_load_pct", "value": 35.0, "threshold": 50, "passed": true}
    ],
    "explanation": "STFT (18.5%) and LTFT (12.0%) both exceed thresholds at low load (35%), indicating unmetered air entering engine. Common causes: vacuum leak, cracked intake boot, faulty PCV valve."
}
```

#### 4.3.3 Database Changes

```sql
-- Rule definitions
CREATE TABLE diagnostic_rules (
    id TEXT PRIMARY KEY, -- RULE_001
    type TEXT, -- threshold, trend, correlation, composite
    name TEXT,
    definition TEXT, -- JSON
    severity TEXT,
    dtc_hint TEXT,
    enabled BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Rule evaluation history
CREATE TABLE rule_evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    rule_id TEXT,
    matched BOOLEAN,
    telemetry_snapshot TEXT, -- JSON
    dtcs TEXT, -- JSON
    match_details TEXT, -- JSON
    FOREIGN KEY (rule_id) REFERENCES diagnostic_rules(id)
);
```

---

### Phase 4: Professional Reporting (Week 4) ⭐ **HIGH VALUE**

#### 4.4.1 Files to Create

| File | Description |
|------|-------------|
| `services/report_generator.py` | Report generation engine |
| `services/report_templates/` | Jinja2 templates (HTML, PDF via WeasyPrint) |
| `modules/diagnostics.py` | Enhanced with report generation UI |

#### 4.4.2 Report Types

| Report Type | Template | Content |
|-------------|----------|---------|
| **Diagnostic Report** | `diagnostic_report.html` | DTCs, AI diagnosis, rule matches, recommended actions, cost estimates |
| **Health Check Report** | `health_check.html` | All systems status, trends, upcoming maintenance |
| **Session Summary** | `session_summary.html` | Telemetry stats, anomalies, DTCs during session |
| **Maintenance Report** | `maintenance_report.html` | Service history, upcoming, predictions |

#### 4.4.3 Report Data Structure

```python
@dataclass
class DiagnosticReportData:
    report_id: str
    generated_at: datetime
    vehicle: VehicleProfile
    session: Optional[TelemetrySession]
    dtcs: List[DTC]
    ai_diagnosis: AIDiagnosis
    rule_matches: List[RuleMatch]
    telemetry_summary: Dict  # min/max/avg for key params
    recommendations: List[Recommendation]
    oem_data: Dict  # TSBs, recalls, known issues
    estimated_costs: CostEstimate
```

#### 4.4.4 Export Formats

- **HTML** - Interactive, printable, shareable
- **PDF** - Professional, via WeasyPrint
- **JSON** - Machine-readable for integration

---

### Phase 5: Database Migrations (Week 4-5) ⭐ **FOUNDATIONAL**

#### 4.5.1 Migration Strategy

**Tool:** Alembic (SQLAlchemy migration tool)

**Migration Files:**
```
migrations/
├── env.py
├── script.py.mako
├── versions/
│   ├── 001_initial_schema.py          # V1 baseline (auto-generated)
│   ├── 002_add_real_obd_columns.py    # Phase 1
│   ├── 003_add_ai_diagnostics.py      # Phase 2
│   ├── 004_add_rule_engine.py         # Phase 3
│   ├── 005_add_reporting.py           # Phase 4
│   └── 006_seed_data.py               # Reference data
```

#### 4.5.2 Key Migrations

**001_initial_schema.py** - Baseline from current V1 database
```python
# Auto-generated from current schema
# Tables: vehicle_profile, telemetry_sessions, telemetry_records, 
# diagnostic_reports, maintenance_records, ai_conversations, settings
```

**002_add_real_obd_columns.py**
```python
def upgrade():
    # Add is_real column to telemetry_records
    op.add_column('telemetry_records', sa.Column('is_real', sa.Boolean(), default=False))
    op.add_column('telemetry_records', sa.Column('pid_source', sa.String(20)))
    
    # Create obd_connection_logs
    op.create_table('obd_connection_logs', ...)
    
    # Create obd_supported_pids
    op.create_table('obd_supported_pids', ...)

def downgrade():
    op.drop_column('telemetry_records', 'is_real')
    op.drop_column('telemetry_records', 'pid_source')
    op.drop_table('obd_connection_logs')
    op.drop_table('obd_supported_pids')
```

**003_add_ai_diagnostics.py**
```python
def upgrade():
    op.create_table('ai_diagnostic_sessions', ...)
    op.create_table('rag_documents', ...)
```

**004_add_rule_engine.py**
```python
def upgrade():
    op.create_table('diagnostic_rules', ...)
    op.create_table('rule_evaluations', ...)
    # Seed default rules
    op.bulk_insert(diagnostic_rules, DEFAULT_RULES)
```

**005_add_reporting.py**
```python
def upgrade():
    op.create_table('generated_reports', ...)
```

**006_seed_data.py**
```python
# Hyundai i20 Asta 2023 specific:
# - Maintenance intervals from config.py
# - Default diagnostic rules
# - Known TSBs/recalls
# - OEM DTC descriptions
```

#### 4.5.3 Migration Runner Service

```python
# services/migration_runner.py
class MigrationRunner:
    def __init__(self, db_path: Path):
        self.alembic_cfg = Config("migrations/alembic.ini")
        self.alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    
    def upgrade(self, revision: str = "head") -> bool
    def downgrade(self, revision: str) -> bool
    def current_revision(self) -> str
    def history(self) -> List[MigrationInfo]
    def stamp(self, revision: str) -> bool
```

---

### Phase 6: UI/UX Enhancements (Week 5-6) ⭐ **POLISH**

#### 4.6.1 New Module: `modules/obd_connection.py`

**Connection Wizard Flow:**
```
1. Welcome → 2. Adapter Detection → 3. Port Selection → 4. Protocol Test → 5. PID Discovery → 6. Connected!
```

**Features:**
- Auto-scan serial ports with ELM327 detection
- Test multiple baudrates/protocols
- Visual PID discovery progress
- Connection health monitor (real-time)
- Save connection profiles

#### 4.6.2 Enhanced Modules

| Module | Enhancements |
|--------|--------------|
| `dashboard.py` | Real/Simulation toggle, connection quality indicator, live PID badges |
| `diagnostics.py` | DTC workflow wizard, AI diagnosis button, freeze frame viewer, report generation |
| `ai_assistant.py` | Diagnostic mode (structured), rule match display, confidence visualization |
| `settings.py` | OBD Connection tab, AI Diagnostic config, Rule Engine config, Report templates |
| `vehicle_profile.py` | Live OBD info (VIN, CALID, CVN), supported PID list |

#### 4.6.3 Real-Time Updates (WebSocket/SSE)

**Current:** Streamlit auto-rerun (2-3s latency)
**V2 Target:** Server-Sent Events or WebSocket for <100ms updates

```python
# components/realtime.py
class RealtimeUpdater:
    def __init__(self):
        self.subscribers: Dict[str, List[Queue]] = defaultdict(list)
    
    def subscribe(self, channel: str) -> Queue
    def publish(self, channel: str, data: Any)
    def start_background_tasks()
```

---

## 5. Database Migration Strategy Details

### 5.1 Current V1 Schema (7 Tables)

| Table | Rows (est) | Key Columns |
|-------|------------|-------------|
| vehicle_profile | 1 | make, model, year, engine, transmission, vin, current_odometer |
| telemetry_sessions | 10-100 | name, scenario, start_time, end_time, is_active, peak_rpm, max_speed, avg_speed, etc. |
| telemetry_records | 1K-100K | session_id, timestamp, rpm, speed_kmh, coolant_temp_c, throttle_pos_pct, engine_load_pct, is_simulated |
| diagnostic_reports | 10-50 | session_id, dtc_count, codes (JSON), summary, recommendations, is_demo |
| maintenance_records | 5-50 | service_type, description, service_date, odometer_km, cost, next_service_km, next_service_date |
| ai_conversations | 50-500 | session_id, role, content, model, tokens_used, timestamp |
| settings | 20-30 | key, value, description |

### 5.2 V2 Schema Additions (8 New Tables)

| Table | Purpose | Est. Rows |
|-------|---------|-----------|
| obd_connection_logs | Connection audit trail | 100-1000 |
| obd_supported_pids | Cached PID support | 50-100 |
| ai_diagnostic_sessions | AI diagnosis history | 50-500 |
| rag_documents | Service manual/TSB chunks | 100-1000 |
| diagnostic_rules | Rule definitions | 20-50 |
| rule_evaluations | Rule match history | 1K-10K |
| generated_reports | Report metadata | 50-500 |
| vehicle_health_snapshots | Periodic health assessments | 100-1000 |

### 5.3 Migration Execution Plan

```bash
# 1. Backup current database
cp i20_garage.db i20_garage_v1_backup.db

# 2. Initialize Alembic
alembic init migrations
# Edit migrations/env.py for SQLite

# 3. Generate baseline migration (V1 schema)
alembic revision --autogenerate -m "baseline_v1_schema"

# 4. Create incremental migrations
alembic revision -m "add_real_obd_columns"
alembic revision -m "add_ai_diagnostics"
alembic revision -m "add_rule_engine"
alembic revision -m "add_reporting"
alembic revision -m "seed_data"

# 5. Run migrations
alembic upgrade head

# 6. Verify
alembic current
alembic history
```

---

## 6. File-Level Change Summary

### 6.1 Modified Files

| File | Phase | Change Type | Lines Changed |
|------|-------|-------------|---------------|
| `services/obd_service.py` | 1 | Major Refactor | ~400 |
| `services/ai_service.py` | 2 | Major Enhancement | ~200 |
| `services/database.py` | 1,5 | Schema Updates | ~100 |
| `config.py` | 1-6 | New Config Options | ~100 |
| `app.py` | 1-6 | Navigation, State | ~50 |
| `components/sidebar.py` | 1,6 | Real OBD Indicators | ~50 |
| `modules/dashboard.py` | 1,6 | Real/Sim Toggle | ~100 |
| `modules/diagnostics.py` | 1-4 | DTC Workflow, Reports | ~200 |
| `modules/ai_assistant.py` | 2,6 | Diagnostic Mode | ~100 |
| `modules/settings.py` | 1-6 | New Tabs | ~150 |
| `modules/vehicle_profile.py` | 1,6 | OBD Info | ~50 |
| `modules/maintenance.py` | 3,4 | Predictions | ~50 |
| `requirements.txt` | 1-6 | New Dependencies | ~10 |

### 6.2 New Files

| File | Phase | Purpose | Est. Lines |
|------|-------|---------|------------|
| `services/real_obd_adapter.py` | 1 | ELM327 communication | 300 |
| `services/connection_manager.py` | 1 | Port detection, reconnection | 200 |
| `services/pid_registry.py` | 1 | PID discovery, prioritization | 150 |
| `services/diagnostic_engine.py` | 2 | AI + Rules orchestration | 200 |
| `services/rule_engine.py` | 3 | Rule evaluation, explainability | 300 |
| `services/rules/*.yaml` | 3 | Rule definitions | 100 |
| `services/report_generator.py` | 4 | Report generation | 250 |
| `services/report_templates/*.html` | 4 | Jinja2 templates | 500 |
| `services/migration_runner.py` | 5 | Alembic wrapper | 100 |
| `migrations/versions/*.py` | 5 | Schema migrations | 300 |
| `modules/obd_connection.py` | 6 | Connection wizard | 300 |
| `components/realtime.py` | 6 | SSE/WebSocket updates | 150 |
| `tests/test_obd_real.py` | 1 | Real OBD tests | 200 |
| `tests/test_diagnostic_engine.py` | 2-3 | AI + Rules tests | 150 |
| `tests/test_rule_engine.py` | 3 | Rule engine tests | 100 |
| `tests/test_report_generator.py` | 4 | Report tests | 100 |

---

## 7. Dependencies to Add

```txt
# requirements.txt additions for V2

# OBD-II Real Connectivity
obd>=0.7.0              # Already in V1
pyserial>=3.5           # Already in V1
pyserial-asyncio>=0.5   # Async serial for background polling

# AI Diagnostics
chromadb>=0.4.0         # Vector store for RAG
sentence-transformers>=2.2.0  # Embeddings for RAG
pypdf>=3.0.0            # Service manual PDF parsing
python-docx>=0.8.0      # TSB document parsing

# Rule Engine
pyyaml>=6.0             # Rule definitions in YAML

# Reporting
jinja2>=3.1.0           # HTML templates
weasyprint>=60.0        # PDF generation
# Note: WeasyPrint requires system dependencies (GTK, cairo)

# Database Migrations
alembic>=1.11.0         # Schema migrations
sqlalchemy>=2.0.0       # Already implicit via alembic

# Real-time Updates
# Option A: Streamlit's built-in (simpler)
# Option B: websockets>=11.0  # If custom WebSocket needed

# Testing
pytest-asyncio>=0.21.0  # Async tests
pytest-mock>=3.10.0     # Already covered
```

---

## 8. Testing Strategy

### 8.1 Test Pyramid

| Level | Count | Tools | Coverage Target |
|-------|-------|-------|-----------------|
| Unit | 100+ | pytest, mock | 85% |
| Integration | 30+ | pytest, testcontainers | 70% |
| E2E | 10+ | playwright/selenium | Critical paths |

### 8.2 Test Categories

| Category | Test File | Key Scenarios |
|----------|-----------|---------------|
| Real OBD | `test_obd_real.py` | Port detection, connection, PID query, DTC scan, freeze frame, reconnection |
| AI Diagnostics | `test_diagnostic_engine.py` | Structured output, confidence, RAG, fallback |
| Rule Engine | `test_rule_engine.py` | All rule types, explainability, priority |
| Reporting | `test_report_generator.py` | HTML/PDF/JSON output, data accuracy |
| Migrations | `test_migrations.py` | Upgrade/downgrade, data integrity |
| Integration | `test_integration.py` | Full diagnostic workflow |

### 8.3 Mock Strategy for Real OBD Tests

```python
# tests/conftest.py
@pytest.fixture
def mock_elm327():
    """Mock ELM327 adapter for unit tests."""
    with patch('obd.OBD') as mock_obd:
        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = True
        mock_conn.supported_commands = { ... }
        mock_conn.query.return_value = MagicMock(value=MagicMock(magnitude=2500))
        mock_obd.return_value = mock_conn
        yield mock_conn
```

---

## 9. Timeline & Milestones

| Week | Phase | Deliverable | Success Criteria |
|------|-------|-------------|------------------|
| 1 | 1.1-1.2 | Real OBD Adapter + Connection Manager | Connect to ELM327, read RPM |
| 2 | 1.3-1.4 | PID Registry + Background Polling | 11 PIDs at 10Hz, auto-reconnect |
| 3 | 2.1-2.2 | AI Diagnostic Engine + RAG | Structured JSON diagnosis, >80% confidence |
| 4 | 3 | Rule Engine | 10+ rules, explainability working |
| 5 | 4 | Professional Reports | HTML/PDF generation, all report types |
| 6 | 5 | Database Migrations | Alembic working, V1→V2 upgrade tested |
| 7 | 6 | UI Enhancements | Connection wizard, real-time updates |
| 8 | All | Integration Testing | Full workflow: Connect → Scan → Diagnose → Report |

---

## 10. Risk Assessment & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| ELM327 adapter compatibility issues | High | High | Test with multiple adapters (USB, BT, WiFi), fallback to simulation |
| python-OBD library limitations | Medium | Medium | Implement custom PID queries, direct AT commands |
| LM Studio API changes | Low | Medium | Version pin, abstraction layer, fallback prompts |
| WeasyPrint system dependencies | Medium | High | Provide HTML-only fallback, Docker for deployment |
| Migration data loss | Low | Critical | Full backup before migration, test downgrade |
| Real-time performance | Medium | Medium | Optimize PID polling, use async, cache gauge status |
| Rule engine false positives | Medium | Medium | Tunable thresholds, confidence scoring, user feedback loop |

---

## 11. Success Metrics

| Metric | V1 Baseline | V2 Target |
|--------|-------------|-----------|
| Real OBD Connection Success Rate | N/A | >95% |
| PID Read Latency (P50) | N/A | <50ms |
| AI Diagnosis Confidence | N/A | >80% avg |
| Rule Engine Precision | N/A | >85% |
| Report Generation Time | N/A | <5s |
| Test Coverage | 100% (47/47) | >85% |
| Migration Success Rate | N/A | 100% |

---

## 12. Appendix: Key Configuration Additions

### config.py additions for V2

```python
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

# AI Diagnostic Configuration
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

# Rule Engine Configuration
RULE_ENGINE_CONFIG = {
    "enabled": True,
    "rules_dir": "services/rules",
    "evaluation_interval_ms": 1000,
    "trend_window_seconds": 60,
    "min_confidence": 0.6,
}

# Reporting Configuration
REPORT_CONFIG = {
    "templates_dir": "services/report_templates",
    "output_dir": "reports",
    "pdf_enabled": True,
    "default_format": "html",
    "include_oem_data": True,
    "cost_currency": "INR",
    "cost_region": "India",
}

# Migration Configuration
MIGRATION_CONFIG = {
    "migrations_dir": "migrations",
    "backup_before_migrate": True,
    "backup_dir": "backups/migrations",
}
```

---

## 13. Next Steps

1. **Immediate**: Create `migrations/` directory, initialize Alembic, generate baseline migration
2. **Week 1**: Implement `RealOBDAdapter` and `ConnectionManager` in `services/obd_service.py`
3. **Week 1-2**: Build PID Registry and background polling thread
4. **Week 2**: Create connection wizard UI (`modules/obd_connection.py`)
5. **Week 2-3**: Enhance AI service with structured output and RAG
6. **Week 3**: Build Rule Engine with default Hyundai i20 rules
7. **Week 4**: Implement Report Generator with templates
8. **Week 4-5**: Run all migrations, verify V1→V2 upgrade
9. **Week 5-6**: UI polish, real-time updates, integration testing
10. **Week 8**: Full E2E testing, documentation, release

---

*Document Version: 1.0*  
*Generated: 2026-11-16*  
*Based on V1 Audit (47 tests passing, 7 modules, 3 services)*
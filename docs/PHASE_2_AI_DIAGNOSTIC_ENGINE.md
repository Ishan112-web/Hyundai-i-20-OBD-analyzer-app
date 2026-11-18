# Phase 2: AI Diagnostic Engine - Implementation Documentation

## Overview

Phase 2 implements a complete AI-powered diagnostic engine for the i20 AI Garage application. The engine transforms vehicle telemetry data, DTC codes, and contextual information into structured, evidence-based diagnostic reports using local LM Studio inference (Qwen2.5 3B Instruct).

## Key Features Delivered

### 1. Structured Pydantic Models (`services/diagnostic_models.py`)
- **DiagnosticResult** - Complete structured diagnostic output
- **ProbableCause** - Ranked causes with confidence, evidence, verification steps, urgency
- **PrimaryDiagnosis / SecondaryDiagnosis** - Multi-diagnosis support
- **DiagnosticRecommendation** - Prioritized actions with safety levels and INR cost estimates
- **DiagnosticContext** - Prompt context builder with `to_prompt_context()` method
- **Enums**: DataSource, DiagnosticSeverity, DiagnosticStatus, DataQuality, SafetyLevel

### 2. Knowledge Base (`services/diagnostic_engine.py::KnowledgeBase`)
- Lightweight local RAG with built-in automotive knowledge
- DTC explanations (P0300, P0171, P0420, P0128)
- Diagnostic principles (fuel trim, cooling, ignition)
- Hyundai i20 Asta 2023 1.2L Kappa specific issues
- Keyword-based search with DTC-code and tag filtering
- Extensible via database (`rag_documents` table)

### 3. Diagnostic Context Builder (`services/diagnostic_engine.py::DiagnosticContextBuilder`)
Gathers comprehensive context from existing services:
- Vehicle profile from database
- Live sensor readings from OBD service (simulation or real)
- Active DTCs with severity/status
- Freeze frame data (real mode)
- Recent telemetry trends (50 records, calculated trends)
- Diagnostic history (last 5 reports)
- Unsupported/missing PIDs
- Knowledge passages relevant to DTCs and abnormal readings

### 4. Diagnostic Prompt Builder (`services/diagnostic_engine.py::DiagnosticPromptBuilder`)
- System prompt with vehicle specifics (2023 Hyundai i20 Asta, 1.2L Kappa, Manual 5-speed, India BS6)
- JSON schema embedded in prompt for structured output enforcement
- Diagnostic instructions (confidence scoring, evidence requirements, safety warnings)

### 5. Diagnostic Engine Orchestrator (`services/diagnostic_engine.py::DiagnosticEngine`)
Complete orchestration pipeline:
1. **Context Building** - DiagnosticContextBuilder
2. **Data Quality Assessment** - 5-tier quality (excellent/good/fair/poor/none)
3. **Prompt Construction** - DiagnosticPromptBuilder
4. **AI Call with Retry** - Up to 2 retries with exponential backoff
5. **Response Parsing** - JSON extraction and Pydantic validation
6. **Reconciliation** - Cross-check AI findings with actual scanned DTCs
7. **Persistence** - Save to `ai_diagnostic_sessions` table

### 6. AI Service Enhancement (`services/ai_service.py`)
- **structured_completion()** - Pydantic model-validated JSON output
- **_extract_json()** - Robust JSON extraction from AI responses
- Low temperature (0.1) for consistent structured output
- 4096 max tokens for complete diagnostic responses

### 7. Database Schema Extensions (`services/database.py`)
New tables:
- **ai_diagnostic_sessions** - Full diagnostic history with JSON fields
- **rag_documents** - Extensible knowledge base with tags, metadata, embeddings

New methods:
- `save_ai_diagnostic_session()` / `get_ai_diagnostic_sessions()`
- `add_rag_document()` / `search_rag_documents()` / `get_rag_documents_by_tags()`

### 8. Diagnostics Module UI (`modules/diagnostics.py`)
- **"🧠 Run AI Diagnosis" button** in scan panel
- **AI Diagnosis Panel** (3rd column) with structured result display:
  - Overall severity badge, confidence, data source
  - Primary/secondary diagnoses with probable causes
  - Evidence (supporting/contradictory) with verification steps
  - Prioritized recommendations with safety levels and INR costs
  - Safety warnings, missing information
  - Simulation disclaimer when applicable

### 9. AI Assistant Module Enhancement (`modules/ai_assistant.py`)
- **Mode Selector**: Chat Mode / Diagnostic Mode
- **Diagnostic Mode Interface**:
  - DTC input field (comma-separated)
  - Symptoms text area
  - Full vehicle scan button
  - Full structured result display matching Diagnostics panel

### 10. Comprehensive Test Suite (`tests/test_diagnostic_engine.py`)
37 tests covering:
- Pydantic model validation (confidence bounds, required fields)
- KnowledgeBase search and retrieval
- DiagnosticContextBuilder with mock services
- DiagnosticPromptBuilder prompt generation
- DiagnosticEngine orchestration (full flow, error handling)
- Data quality assessment
- JSON extraction and response parsing
- Reconciliation logic
- Singleton pattern

## File Structure Changes

```
services/
├── diagnostic_models.py          # NEW: Pydantic models
├── diagnostic_engine.py          # NEW: Engine, ContextBuilder, KnowledgeBase, PromptBuilder
├── ai_service.py                 # ENHANCED: structured_completion()
├── database.py                   # ENHANCED: ai_diagnostic_sessions, rag_documents tables
├── __init__.py                   # ENHANCED: exports get_diagnostic_engine

modules/
├── diagnostics.py                # ENHANCED: AI Diagnosis panel, 3-column layout
├── ai_assistant.py               # ENHANCED: Mode selector, Diagnostic mode

tests/
└── test_diagnostic_engine.py     # NEW: 37 tests

docs/
└── PHASE_2_AI_DIAGNOSTIC_ENGINE.md  # NEW: This documentation
```

## Configuration

### AI_DIAGNOSTIC_CONFIG (config.py)
```python
AI_DIAGNOSTIC_CONFIG = {
    "model": "qwen2.5-3b-instruct",
    "temperature": 0.1,
    "max_tokens": 4096,
    "structured_output": True,
    "rag_enabled": True,
    "confidence_threshold": 0.5,
}
```

### Database Tables

#### ai_diagnostic_sessions
```sql
CREATE TABLE ai_diagnostic_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    diagnosis_id TEXT UNIQUE NOT NULL,
    session_id TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    vehicle_context TEXT,  -- JSON
    dtcs TEXT,             -- JSON
    ai_diagnosis TEXT,     -- JSON (full DiagnosticResult)
    rule_matches TEXT,     -- JSON
    user_feedback TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### rag_documents
```sql
CREATE TABLE rag_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,          -- 'builtin', 'manual', 'tsb', 'forum'
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT,                     -- JSON array
    metadata TEXT,                 -- JSON
    embedding TEXT,                -- JSON array (future vector search)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Usage Examples

### Running AI Diagnosis from Diagnostics Page
1. Perform DTC scan (simulation or real)
2. Click "🧠 Run AI Diagnosis" button
3. View structured results in right panel

### Running AI Diagnosis from AI Assistant (Diagnostic Mode)
1. Switch to "Diagnostic Mode" tab
2. Enter DTC codes (e.g., "P0300, P0171") or describe symptoms
3. Click "Analyze" or "Full Vehicle Scan"
4. View structured results

### Programmatic Usage
```python
from services import get_diagnostic_engine

engine = get_diagnostic_engine()
result = engine.run_diagnosis()

# Access structured data
print(result.diagnosis_id)
print(result.primary_diagnosis.code)
for cause in result.primary_diagnosis.probable_causes:
    print(f"  {cause.cause}: {cause.confidence:.0%}")
for rec in result.recommended_actions:
    print(f"  Priority {rec.priority}: {rec.recommendation} ({rec.estimated_cost_inr})")

# Get history
history = engine.get_diagnosis_history(limit=10)
```

## Data Flow

```
User Action (Scan + AI Diagnosis)
         ↓
OBD Service → DTCs + Sensor Readings
         ↓
Database → Vehicle Profile + Telemetry History + Past Reports
         ↓
KnowledgeBase → Relevant passages for DTCs + abnormal readings
         ↓
DiagnosticContextBuilder → Complete DiagnosticContext
         ↓
DiagnosticPromptBuilder → System Prompt + Context + JSON Schema
         ↓
LM Studio (Qwen2.5 3B) → JSON Response
         ↓
JSON Extraction → Pydantic Validation (DiagnosticResult)
         ↓
Reconciliation → Cross-check with actual DTCs
         ↓
Database Persistence → ai_diagnostic_sessions table
         ↓
UI Display → Structured panels with evidence, recommendations, costs
```

## Safety & Limitations

### Safety Features
- **Simulation data clearly labeled** - All demo output shows "SIMULATION DATA — NOT ACTUAL VEHICLE DATA"
- **Confidence scoring** - Every cause has 0.0-1.0 confidence, overall diagnosis confidence
- **Contradictory evidence required** - AI must list evidence against each probable cause
- **Safety levels** - Recommendations classified: Safe / Caution / Professional
- **Professional flag** - Critical repairs marked `requires_professional: true`
- **No code clearing** - Read-only diagnostic operations

### Limitations
- **Local inference only** - Requires LM Studio running with Qwen2.5 3B model
- **No manufacturer-specific PIDs** - Standard OBD-II PIDs only
- **Simulation mode** - Default mode uses generated data, not real vehicle
- **Single model** - Currently configured for Qwen2.5 3B Instruct
- **No vector search** - RAG uses keyword matching (embeddings stored for future)

## Testing

Run all tests:
```bash
pytest tests/ -v
```

Run only diagnostic engine tests:
```bash
pytest tests/test_diagnostic_engine.py -v
```

Test coverage:
- 133 total tests (96 existing + 37 new)
- All tests passing

## Integration with Existing Architecture

### Service Singletons
```python
from services import get_diagnostic_engine, get_ai_service, get_database, get_obd_service

# All services use singleton pattern
engine = get_diagnostic_engine()
```

### Configuration
All configuration in `config.py` - no hardcoded values in services.

### Error Handling
- Custom exceptions: `AIServiceError`
- Graceful degradation: AI unavailable → error status, not crash
- Retry logic: 2 retries with exponential backoff for AI calls
- Validation: Pydantic validation with clear error messages

## Future Extensibility

### Planned Enhancements
1. **Vector Search** - Enable embedding-based RAG search
2. **Multi-model Support** - Allow model selection per task
3. **Rule Engine** - Deterministic diagnostic rules alongside AI
4. **Image Analysis** - Support for visual inspection (borescope, etc.)
5. **Telemetry Anomaly Detection** - ML-based anomaly detection on live data
6. **TSB Integration** - Technical Service Bulletins in knowledge base
7. **Community Knowledge** - Forum-sourced fixes with validation

### Extending Knowledge Base
Add documents via database:
```python
db = get_database()
db.add_rag_document(
    source="manual",
    title="Hyundai i20 Service Manual - Ignition System",
    content="...",
    tags=["hyundai", "i20", "ignition", "coil"],
    metadata={"year": 2023, "engine": "kappa_1.2l"}
)
```

## Acceptance Criteria Met

✅ All 96 existing tests preserved and passing
✅ Works without physical OBD hardware (simulation mode)
✅ Integrates with existing OBD service, database, AI service
✅ Structured JSON output matching V2 plan schema
✅ RAG/knowledge retrieval from local knowledge base
✅ Persistent diagnostic history in SQLite
✅ Diagnostics page: "Run AI Diagnosis" button + structured display
✅ AI Assistant page: Diagnostic mode with DTC/symptom input
✅ Comprehensive test suite (37 new tests)
✅ Updated README.md with Phase 2 features
✅ Created docs/PHASE_2_AI_DIAGNOSTIC_ENGINE.md

## Verification Checklist

- [x] `pytest tests/` → 133 tests pass
- [x] `streamlit run app.py` → App launches
- [x] Diagnostics page → Scan → "Run AI Diagnosis" → Structured result
- [x] AI Assistant → Diagnostic Mode → Enter DTCs → Analysis result
- [x] Simulation mode works (no hardware required)
- [x] Database persists ai_diagnostic_sessions
- [x] Knowledge base returns relevant passages
- [x] Simulation disclaimer displayed
- [x] INR cost estimates in recommendations
- [x] Safety levels on recommendations
- [x] Contradictory evidence in probable causes
- [x] Verification steps for each probable cause
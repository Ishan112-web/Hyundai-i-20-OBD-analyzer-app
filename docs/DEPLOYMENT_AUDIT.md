# i20 AI Garage - Deployment Audit

**Generated:** 2026-11-20
**Repository:** https://github.com/Ishan112-web/Hyundai-i-20-OBD-analyzer-app
**Branch:** master
**Commit:** 9f54b9b

---

## 1. Repository Structure

```
c:\i20-AI\
├── app.py                      # Main Streamlit entry point
├── config.py                   # Configuration (environment-driven)
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── run.bat / run.ps1           # Windows startup scripts
├── .env / .env.example         # Environment configuration
├── .gitignore                  # Git ignore rules
├── components/                 # UI components (shell, charts, UI system)
├── modules/                    # Page render modules (9 pages)
├── services/                   # Backend services (DB, AI, OBD, migrations)
│   ├── database.py             # SQLite service with migrations
│   ├── ai_service.py           # LM Studio integration
│   ├── obd_service.py          # OBD-II abstraction (simulation + real)
│   ├── migrations/             # Migration system (baseline + runner)
│   └── ...
├── scripts/                    # Utility scripts (migration, backup)
├── tests/                      # Test suite (unit + browser/Playwright)
├── data/                       # SQLite database & profiles
├── reports/                    # Generated reports output
├── artifacts/                  # Test screenshots & artifacts
└── docs/                       # Documentation
```

---

## 2. Streamlit Entry Point

**File:** `app.py`
**Run Command:** `streamlit run app.py --server.port=8501 --server.address=0.0.0.0`

**Key Characteristics:**
- Single-page application with multi-page navigation via session state
- `st.set_page_config()` called at module level (lines 13-23)
- Initializes services lazily via singleton pattern in `services/__init__.py`
- Uses `st.rerun()` for navigation transitions
- Background simulation thread in `OBDService._simulation_loop()`
- Auto-telemetry update runs on every script execution (line 107-128)

---

## 3. Dependencies

### Production (`requirements.txt`)

| Package | Version | Purpose |
|---------|---------|---------|
| streamlit | >=1.67.0 | Web UI framework |
| plotly | >=5.0.0 | Interactive charts |
| pandas | >=2.0.0 | Data manipulation |
| requests | >=2.31.0 | HTTP client for LM Studio |
| python-dotenv | >=1.0.0 | Environment loading |
| obd | >=0.7.0 | OBD-II communication |
| jinja2 | >=3.1.0 | Report templates |
| reportlab | >=4.0.0 | PDF generation |
| typing-extensions | >=4.0.0 | Type hints |
| pyserial | >=3.5 | Serial communication |
| pillow | >=9.0.0 | Image processing |

### Development (`requirements-dev.txt`)

| Package | Version | Purpose |
|---------|---------|---------|
| playwright | >=1.40.0 | Browser automation |
| pytest-playwright | >=0.4.0 | Playwright pytest integration |

### Python Version

- **Compatible:** Python 3.10 - 3.12 (tested on 3.11)
- **Incompatible:** Python < 3.10 (typing features), Python 3.13+ (reportlab wheels)

---

## 4. Native/System Dependencies

| Dependency | Purpose | Docker Install |
|------------|---------|----------------|
| `sqlite3` | Database (built-in) | Included in Python |
| `libpq` | Not used | N/A |
| `freetype` | Pillow/ReportLab fonts | `apt-get install -y libfreetype6-dev` |
| `zlib` | Compression | `apt-get install -y zlib1g-dev` |
| `libjpeg` | Image processing | `apt-get install -y libjpeg-dev` |
| `openblas` | NumPy/Pandas performance | `apt-get install -y libopenblas-dev` |
| `chromium` | Playwright browser | `playwright install-deps chromium` |

---

## 5. Database Initialization & Migrations

### Database Path
- **Default:** `data/i20_garage.db` (from `config.DATABASE_PATH`)
- **Staging Override:** Via `DATABASE_PATH` environment variable

### Schema Creation
- `DatabaseService._init_database()` creates all tables on first run (lines 67-257)
- Tables: `vehicle_profile`, `telemetry_sessions`, `telemetry_records`, `diagnostic_reports`, `maintenance_records`, `ai_conversations`, `settings`, `obd_connection_logs`, `obd_supported_pids`, `ai_diagnostic_sessions`, `rag_documents`, `rule_evaluations`, `rule_findings`, `rule_triggers`
- Indexes created for query performance

### Migration System
- **Location:** `services/migrations/`
- **Baseline Version:** 1 (legacy schema from Phases 1-4)
- **Runner:** `scripts/database_migrate.py` or `MigrationRunner` class
- **Checksums:** SHA256 of schema for integrity verification
- **Backup:** Automatic pre-migration backup via `BackupManager`
- **Locking:** SQLite `BEGIN IMMEDIATE` / `BEGIN EXCLUSIVE` for concurrency safety

### Staging Considerations
- Fresh database: migrations initialize tracking table automatically
- Existing database: baseline adoption validates schema compatibility
- **No destructive operations** in baseline migration (0001)

---

## 6. Application Startup Commands

### Local Development
```bash
# Windows Batch
run.bat

# PowerShell
.\run.ps1

# Direct
.venv\Scripts\python.exe -m streamlit run app.py --server.port=8501 --server.address=localhost
```

### Production/Staging
```bash
# Using gunicorn (not applicable - Streamlit runs its own server)
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
```

### Environment Variables Required
| Variable | Default | Staging Value |
|----------|---------|---------------|
| `LM_STUDIO_BASE_URL` | `http://localhost:1234/v1` | **Must be configured or AI disabled** |
| `LM_STUDIO_MODEL` | `qwen2.5-3b-instruct` | Same |
| `OBD_MODE` | `simulation` | `simulation` (required) |
| `OBD_PORT` | `COM3` | N/A (simulation) |
| `DATABASE_PATH` | `data/i20_garage.db` | `/app/data/i20_garage_staging.db` |
| `SIMULATION_INTERVAL` | `0.5` | `1.0` (reduce CPU) |
| `TELEMETRY_REFRESH_INTERVAL` | `1.0` | `2.0` (reduce CPU) |

---

## 7. Environment Variables & Secrets

### Current `.env` (Local)
```env
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_MODEL=qwen2.5-3b-instruct
LM_STUDIO_TEMPERATURE=0.7
LM_STUDIO_TIMEOUT=30
OBD_MODE=simulation
OBD_PORT=COM3
OBD_BAUDRATE=38400
OBD_PROTOCOL=auto
SIMULATION_INTERVAL=0.5
TELEMETRY_REFRESH_INTERVAL=1.0
```

### Secrets Management
- **No hardcoded secrets** in codebase
- `.env` is gitignored
- `.env.example` provides template
- Staging: Use platform secret store (Render Environment Variables)

---

## 8. File-System Paths Used

| Path | Purpose | Persistence |
|------|---------|-------------|
| `data/i20_garage.db` | Main SQLite database | **Required** |
| `data/connection_profiles.json` | OBD connection profiles | Optional |
| `reports/` | Generated HTML/PDF reports | Optional |
| `services/migrations/versions/` | Migration files | Read-only |
| `services/rules/` | Rule engine YAML files | Read-only |
| `services/report_templates/` | Jinja2 templates | Read-only |

---

## 9. External Dependencies

### LM Studio (Local AI)
- **Endpoint:** `http://localhost:1234/v1` (OpenAI-compatible)
- **Model:** `qwen2.5-3b-instruct` (or configured model)
- **Staging:** **NOT available** in cloud container
- **Fallback:** AI Assistant shows connection error, UI remains functional

### OBD-II Hardware
- **Real Mode:** Serial port (COM3/ttyUSB0), ELM327 adapter
- **Staging:** **MUST use simulation mode**
- **Simulation:** `SimulationEngine` generates realistic telemetry

### Windows-Specific
- Default `OBD_PORT=COM3`
- `run.bat` startup script
- Path separators handled via `pathlib`

---

## 10. Simulation Mode

### Activation
- `OBD_MODE=simulation` (environment variable, default in `.env.example`)
- Settings page allows runtime toggle (but persists only in session)

### Behavior
- `SimulationEngine` generates correlated vehicle telemetry
- Scenarios: `idle`, `city`, `highway`, `acceleration`, `overheating`
- Demo DTCs: P0300, P0171, P0420, P0128 (marked `is_demo: true`)
- No hardware access attempted
- Background thread updates at `SIMULATION_INTERVAL` (default 0.5s)

### Staging Requirements
- **Default to simulation mode**
- **Disable real connection attempts**
- **No ECU write commands** (Mode 04 clear-DTC, actuator tests)
- Reduce simulation interval to conserve CPU

---

## 11. Key Risks for Staging Deployment

| Risk | Impact | Mitigation |
|------|--------|------------|
| LM Studio unavailable | AI Assistant non-functional | Graceful degradation, clear messaging |
| SQLite file locking | Concurrent Streamlit sessions fail | WAL mode, connection pooling |
| Background threads | Container restart leaves zombies | Daemon threads, proper shutdown |
| No persistent volume | Data lost on redeploy | Document as ephemeral, use external DB for production |
| Large memory usage | Container OOM | Limit simulation frequency, optimize charts |
| Playwright in container | Browser tests need Chromium | Install deps, run headless |

---

## 12. Migration Checklist for Staging

- [ ] Create `Dockerfile` with Python 3.11 slim
- [ ] Create `.dockerignore` excluding `.venv`, `__pycache__`, `.env`, `data/*.db`, `artifacts/`
- [ ] Create `render.yaml` for Render deployment
- [ ] Create staging config (`.env.staging` template)
- [ ] Create `docs/DEPLOYMENT_GUIDE.md`
- [ ] Test Docker build locally
- [ ] Verify health check endpoint
- [ ] Configure Render environment variables
- [ ] Deploy and verify staging URL
- [ ] Run Playwright tests against staging
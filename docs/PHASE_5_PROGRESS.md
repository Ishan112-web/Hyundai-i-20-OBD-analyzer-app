# Phase 5: Database Migration & Versioning System - Progress Tracker

**Status**: IN PROGRESS  
**Started**: 2026-11-16  
**Objective**: Build a reliable, version-controlled database migration infrastructure for i20 AI Garage.

---

## 1. Repository Audit Findings (Completed)

### Actual Database Schema (14 business tables + sqlite_sequence)

| # | Table | Source | Purpose |
|---|-------|--------|---------|
| 1 | `vehicle_profile` | V1 | Vehicle specifications (make, model, year, engine, etc.) |
| 2 | `telemetry_sessions` | V1 | OBD telemetry session metadata |
| 3 | `telemetry_records` | V1 | Individual sensor readings per session |
| 4 | `diagnostic_reports` | V1 | DTC scan history |
| 5 | `maintenance_records` | V1 | Service/maintenance history |
| 6 | `ai_conversations` | V1 | AI chat history |
| 7 | `settings` | V1 | Application settings key-value store |
| 8 | `obd_connection_logs` | Phase 1 | OBD connection event log |
| 9 | `obd_supported_pids` | Phase 1 | Cached supported PID list |
| 10 | `ai_diagnostic_sessions` | Phase 2 | AI structured diagnostic sessions |
| 11 | `rag_documents` | Phase 2 | RAG knowledge base documents |
| 12 | `rule_evaluations` | Phase 3 | Rule engine evaluation history |
| 13 | `rule_findings` | Phase 3 | Individual rule findings |
| 14 | `rule_triggers` | Phase 3 | Rule trigger history (cooldown tracking) |
| — | `sqlite_sequence` | System | AUTOINCREMENT tracking |

### Database Properties (Verified Read-Only)

| Property | Value |
|----------|-------|
| Path | `data/i20_garage.db` |
| Journal Mode | DELETE |
| Foreign Keys | OFF (0) |
| Busy Timeout | 5000ms |
| User Version | 0 (no migration tracking) |
| Integrity Check | OK |

### Existing Data Contracts (Verified from database.py and rule_history.py)

- **Vehicle Profile**: `get_vehicle_profile()` → Dict with make, model, year, engine, transmission, fuel_type, market, ecu_tuning, diagnostic_mode, vin
- **Telemetry Sessions**: `get_telemetry_sessions()` → List[Dict] with session_name, scenario, start_time, duration_seconds, peak_rpm, max_speed, avg_speed, max_coolant_temp, max_engine_load
- **Telemetry Records**: `get_session_records(session_id)` → List[Dict] with timestamp, rpm, speed_kmh, coolant_temp_c, throttle_pos_pct, engine_load_pct, intake_pressure_kpa, stft_b1_pct, ltft_b1_pct, voltage_v, maf_g_s, map_kpa, is_simulated
- **Diagnostic Reports**: `get_diagnostic_reports()` → List[Dict] with dtc_count, codes_json, summary, is_demo
- **AI Diagnostic Sessions**: `get_ai_diagnostic_sessions()` → List[Dict] with diagnosis_id, vehicle_context, dtcs, ai_diagnosis, rule_matches
- **Maintenance Records**: `get_maintenance_records()` → List[Dict] with service_type, description, service_date, odometer_km, cost, next_service_km, next_service_date
- **Rule Evaluation History**: `rule_engine.get_evaluation_history()` → List[Dict]
- **Rule Finding History**: `rule_engine.get_finding_history(rule_id)` → List[Dict]

### Existing Backup Capabilities

- `DatabaseService.backup_database(backup_path)` — Uses `shutil.copy2()` (file copy)
- No integrity verification of backup
- No automated backup before schema changes

### Existing Migration/Versioning Capabilities

- **NONE** — No schema version tracking, no migration infrastructure
- `PRAGMA user_version` = 0
- Tables created with `CREATE TABLE IF NOT EXISTS` on service initialization
- Rule engine tables created by `RuleHistoryStore._init_tables()` on first use

### Test Baseline

- **325 tests passing**, 1 failed (pre-existing flaky `test_city_scenario_behavior`)
- No physical OBD hardware required
- No LM Studio connection required for tests
- Tests use temporary databases where applicable

---

## 2. Architecture Decision

### Migration Framework Choice: Custom Python System

**Rationale:**
- Application is SQLite-first, local-only, no ORM
- Minimal dependencies preferred (avoid Alembic overhead)
- Full control over transaction safety, backup verification, legacy adoption
- Existing codebase patterns favor explicit, readable Python modules

### Version Tracking: `schema_migrations` Table

Using a dedicated history table (not `PRAGMA user_version`) because:
- Supports detailed migration metadata (checksum, description, duration)
- Enables checksum verification of applied migrations
- Provides audit trail for debugging
- Allows multiple migration branches detection

### Proposed File Structure

```
services/
    database.py              # MODIFIED: integrate migration runner
    migrations/
        __init__.py
        models.py            # Pydantic models for migration metadata
        registry.py          # Migration discovery and ordering
        runner.py            # Migration execution with transactions
        backup_manager.py    # SQLite online backup + verification
        baseline.py          # Legacy database adoption logic

scripts/
    database_status.py       # Migration status inspection
    database_migrate.py      # CLI migration execution
    database_backup.py       # Backup management

tests/
    test_migration_models.py
    test_migration_runner.py
    test_migration_registry.py
    test_migration_backup.py
    test_migration_legacy.py
    test_migration_integration.py

docs/
    PHASE_5_PROGRESS.md
    PHASE_5_DATABASE_MIGRATIONS.md
```

---

## 3. Implementation Progress

### Stage 1: Read-only Audit ✅ COMPLETED
- [x] Inspected project structure
- [x] Inspected database.py and all accessor methods
- [x] Inspected rule_history.py (Phase 3 tables)
- [x] Inspected diagnostic_engine.py, diagnostic_models.py
- [x] Inspected report_models.py, report_data_builder.py, report_generator.py
- [x] Inspected app.py and sidebar navigation
- [x] Inspected actual SQLite database read-only
- [x] Verified integrity_check = OK
- [x] Ran baseline tests: **325 passed, 1 failed (pre-existing)**

### Stage 2: Architecture Design ✅ COMPLETED
- [x] Chose custom Python migration system
- [x] Defined `schema_migrations` table for version tracking
- [x] Designed migration registry with checksum verification
- [x] Designed legacy adoption (baseline detection + safe initialization)
- [x] Designed backup manager using SQLite online backup API
- [x] Designed startup integration with DatabaseService
- [x] Defined test strategy (temporary databases only)

### Stage 3: Migration Infrastructure 🔄 IN PROGRESS
- [ ] Create `services/migrations/models.py` — Pydantic migration models
- [ ] Create `services/migrations/registry.py` — Migration discovery & ordering
- [ ] Create `services/migrations/runner.py` — Transaction-safe execution
- [ ] Create `services/migrations/backup_manager.py` — Backup + verification
- [ ] Create `services/migrations/baseline.py` — Legacy adoption logic
- [ ] Create `services/migrations/__init__.py` — Exports

### Stage 4: Baseline Adoption
- [ ] Detect existing schema and match to baseline
- [ ] Validate required tables/columns for baseline
- [ ] Create verified backup before changes
- [ ] Establish migration metadata for legacy databases
- [ ] Verify existing records preserved

### Stage 5: Backup and Restore
- [ ] SQLite online backup API (`connection.backup()`)
- [ ] Backup integrity verification (PRAGMA integrity_check)
- [ ] Schema and row-count validation
- [ ] Safe restore with atomic replacement
- [ ] WAL-compatible backup handling

### Stage 6: DatabaseService Integration
- [ ] Integrate migration check in `DatabaseService.__init__`
- [ ] Ensure migration runs once per startup (not on every Streamlit rerun)
- [ ] Preserve all existing CRUD methods
- [ ] Handle migration failures gracefully

### Stage 7: Management Interface
- [ ] `python -m services.migrations status` — Show migration status
- [ ] `python -m services.migrations migrate` — Execute pending migrations
- [ ] `python -m services.migrations backup` — Create verified backup
- [ ] `python -m services.migrations verify` — Verify database integrity
- [ ] `python -m services.migrations dry-run` — Show pending migrations

### Stage 8: Testing
- [ ] Migration runner tests
- [ ] Legacy database adoption tests
- [ ] Backup/restore tests
- [ ] Transaction failure/recovery tests
- [ ] Full regression suite (must maintain 325+ passing)

### Stage 9: Documentation & Final Review
- [ ] Complete PHASE_5_PROGRESS.md
- [ ] Create PHASE_5_DATABASE_MIGRATIONS.md technical documentation
- [ ] Update README.md with migration instructions
- [ ] Verify no database schema changes
- [ ] Verify no existing tests removed/weakened

---

## 4. Acceptance Criteria Tracking

| Criterion | Status |
|-----------|--------|
| Actual legacy schema audited | ✅ |
| Migration mechanism implemented | 🔄 |
| Single authoritative schema-version source | 🔄 |
| Ordered migration discovery | 🔄 |
| Migration checksums | 🔄 |
| Duplicate version detection | 🔄 |
| Applied migration history | 🔄 |
| Unknown future versions rejected safely | 🔄 |
| No unnecessary dependency added | 🔄 |
| Existing database adopted safely | 🔄 |
| Fresh database initializes correctly | 🔄 |
| Baseline schema validated | 🔄 |
| Existing tables preserved | 🔄 |
| Existing records preserved | 🔄 |
| Existing IDs preserved | 🔄 |
| Existing relationships preserved | 🔄 |
| Existing database methods continue working | 🔄 |
| Automatic backup before migration | 🔄 |
| Backup verification | 🔄 |
| Safe transaction boundaries | 🔄 |
| Concurrent migration protection | 🔄 |
| Foreign-key checks | 🔄 |
| Integrity checks | 🔄 |
| Failed migration recovery | 🔄 |
| Restore functionality | 🔄 |
| No production database used in destructive tests | 🔄 |
| No silent automatic reset | 🔄 |
| No automatic deletion of backups | 🔄 |
| DatabaseService integration | 🔄 |
| Startup compatibility | 🔄 |
| Streamlit reruns do not repeat migrations | 🔄 |
| Existing pages work | 🔄 |
| AI diagnostic persistence works | 🔄 |
| Rule history works | 🔄 |
| Report data retrieval works | 🔄 |
| Simulation continues working | 🔄 |
| Migration runner tests | 🔄 |
| Legacy database tests | 🔄 |
| Fresh database tests | 🔄 |
| Backup and restore tests | 🔄 |
| Transaction failure tests | 🔄 |
| Integrity tests | 🔄 |
| Integration tests | 🔄 |
| Full regression suite passes | 🔄 |
| No existing tests removed or weakened | 🔄 |
| Progress tracker complete | 🔄 |
| Technical documentation complete | 🔄 |
| README updated | 🔄 |
| CLI usage documented | 🔄 |
| Backup/restore procedure documented | 🔄 |
| Recovery procedure documented | 🔄 |
| Limitations documented | 🔄 |

---

## 5. Known Issues / Risks

1. **Foreign keys currently OFF** — Migration runner should enable for verification but not change application default without testing
2. **Journal mode DELETE** — SQLite online backup API works with DELETE mode; WAL would need different handling
3. **Rule engine tables created separately** — Must ensure baseline includes all 14 business tables
4. **No existing schema version** — Baseline migration must establish version 1 for existing databases
5. **Streamlit reruns** — Must guard against repeated migration execution

---

## 6. Next Actions

1. Create `services/migrations/models.py` with Pydantic models
2. Create `services/migrations/registry.py` for migration discovery
3. Create `services/migrations/runner.py` for execution
4. Create `services/migrations/backup_manager.py` for backups
5. Create `services/migrations/baseline.py` for legacy adoption
6. Integrate with `DatabaseService`
7. Add CLI management scripts
8. Write comprehensive tests
9. Run full regression
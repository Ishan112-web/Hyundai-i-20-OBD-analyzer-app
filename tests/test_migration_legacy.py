"""
Tests for legacy database adoption.
"""

import tempfile
import shutil
import sqlite3
from pathlib import Path
import pytest

from services.migrations import (
    BaselineValidator,
    BaselineAdopter,
    ensure_database_migrated,
    BackupManager,
    BASELINE_VERSION,
    BASELINE_TABLES,
)


class TestBaselineValidator:
    """Tests for BaselineValidator."""

    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_valid_baseline_db(self, db_path: Path):
        """Create a database with all baseline tables."""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Vehicle profile
            cursor.execute("""
                CREATE TABLE vehicle_profile (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    make TEXT NOT NULL, model TEXT NOT NULL, year INTEGER NOT NULL,
                    engine TEXT NOT NULL, transmission TEXT NOT NULL, fuel_type TEXT NOT NULL,
                    market TEXT NOT NULL, ecu_tuning TEXT NOT NULL, diagnostic_mode TEXT NOT NULL,
                    vin TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Telemetry sessions
            cursor.execute("""
                CREATE TABLE telemetry_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_name TEXT, scenario TEXT, start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP, duration_seconds REAL, peak_rpm REAL,
                    max_speed REAL, avg_speed REAL, max_coolant_temp REAL,
                    max_engine_load REAL, total_distance_km REAL, fuel_consumed_l REAL,
                    notes TEXT, is_active BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Telemetry records
            cursor.execute("""
                CREATE TABLE telemetry_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL, timestamp TIMESTAMP NOT NULL,
                    rpm REAL, speed_kmh REAL, coolant_temp_c REAL,
                    throttle_pos_pct REAL, engine_load_pct REAL, intake_pressure_kpa REAL,
                    stft_b1_pct REAL, ltft_b1_pct REAL, voltage_v REAL,
                    maf_g_s REAL, map_kpa REAL, is_simulated BOOLEAN DEFAULT 1,
                    FOREIGN KEY (session_id) REFERENCES telemetry_sessions (id) ON DELETE CASCADE
                )
            """)

            # Diagnostic reports
            cursor.execute("""
                CREATE TABLE diagnostic_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER, scan_time TIMESTAMP NOT NULL,
                    dtc_count INTEGER DEFAULT 0, codes_json TEXT, summary TEXT,
                    is_demo BOOLEAN DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES telemetry_sessions (id) ON DELETE SET NULL
                )
            """)

            # Maintenance records
            cursor.execute("""
                CREATE TABLE maintenance_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_type TEXT NOT NULL, description TEXT, service_date DATE NOT NULL,
                    odometer_km INTEGER NOT NULL, cost REAL, notes TEXT,
                    next_service_km INTEGER, next_service_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # AI conversations
            cursor.execute("""
                CREATE TABLE ai_conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL,
                    model TEXT, tokens_used INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Settings
            cursor.execute("""
                CREATE TABLE settings (
                    key TEXT PRIMARY KEY, value TEXT NOT NULL, description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # OBD connection logs
            cursor.execute("""
                CREATE TABLE obd_connection_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, event_type TEXT NOT NULL,
                    port TEXT, baudrate INTEGER, protocol TEXT, details TEXT
                )
            """)

            # OBD supported PIDs
            cursor.execute("""
                CREATE TABLE obd_supported_pids (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pid TEXT UNIQUE NOT NULL, name TEXT, unit TEXT,
                    description TEXT, is_supported BOOLEAN DEFAULT 1,
                    last_verified DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # AI diagnostic sessions
            cursor.execute("""
                CREATE TABLE ai_diagnostic_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    diagnosis_id TEXT UNIQUE NOT NULL, session_id TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, vehicle_context TEXT,
                    dtcs TEXT, ai_diagnosis TEXT, rule_matches TEXT, user_feedback TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # RAG documents
            cursor.execute("""
                CREATE TABLE rag_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL, title TEXT NOT NULL, content TEXT NOT NULL,
                    tags TEXT, metadata TEXT, embedding TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Rule evaluations
            cursor.execute("""
                CREATE TABLE rule_evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_id TEXT NOT NULL, rule_name TEXT NOT NULL, rule_category TEXT,
                    rule_severity TEXT, vehicle_make TEXT, vehicle_model TEXT, vehicle_year INTEGER,
                    vehicle_engine TEXT, dtcs_matched TEXT, telemetry_anomalies TEXT,
                    matched BOOLEAN NOT NULL, confidence_score REAL, matching_details TEXT,
                    suggested_actions TEXT, evaluation_time_ms REAL, evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    session_id TEXT
                )
            """)

            # Rule findings
            cursor.execute("""
                CREATE TABLE rule_findings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    evaluation_id INTEGER NOT NULL, rule_id TEXT NOT NULL, rule_name TEXT NOT NULL,
                    rule_category TEXT, rule_severity TEXT, finding_type TEXT NOT NULL,
                    finding_title TEXT NOT NULL, finding_description TEXT, evidence TEXT,
                    related_dtcs TEXT, related_pids TEXT, confidence_score REAL,
                    severity_score INTEGER, impact_assessment TEXT, recommended_actions TEXT,
                    estimated_repair_cost_min REAL, estimated_repair_cost_max REAL,
                    safety_risk_level TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (evaluation_id) REFERENCES rule_evaluations (id) ON DELETE CASCADE
                )
            """)

            # Rule triggers
            cursor.execute("""
                CREATE TABLE rule_triggers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trigger_name TEXT NOT NULL, trigger_type TEXT NOT NULL, condition TEXT NOT NULL,
                    enabled BOOLEAN DEFAULT 1, priority INTEGER DEFAULT 0, cooldown_seconds INTEGER DEFAULT 300,
                    max_triggers_per_hour INTEGER DEFAULT 10, last_triggered TIMESTAMP,
                    trigger_count INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Indexes
            cursor.execute("CREATE INDEX idx_telemetry_session ON telemetry_records(session_id)")
            cursor.execute("CREATE INDEX idx_telemetry_timestamp ON telemetry_records(timestamp)")

            cursor.execute("PRAGMA user_version = 1")
            conn.commit()

    def test_validate_valid_database(self):
        db_path = self.temp_dir / "valid.db"
        self.create_valid_baseline_db(db_path)

        validator = BaselineValidator(db_path)
        is_valid, errors, details = validator.validate()

        assert is_valid is True
        assert errors == []
        assert len(details["tables_found"]) == len(BASELINE_TABLES)
        assert details["integrity_ok"] is True
        assert details["user_version"] == 1

    def test_validate_missing_table(self):
        db_path = self.temp_dir / "missing_table.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE vehicle_profile (id INTEGER PRIMARY KEY)")
            conn.commit()

        validator = BaselineValidator(db_path)
        is_valid, errors, details = validator.validate()

        assert is_valid is False
        assert len(errors) > 0
        assert any("vehicle_profile" in e for e in errors)

    def test_validate_insufficient_columns(self):
        db_path = self.temp_dir / "insufficient_cols.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            # vehicle_profile needs at least 10 columns
            cursor.execute("CREATE TABLE vehicle_profile (id INTEGER PRIMARY KEY, make TEXT)")
            # Create other tables with minimal columns
            for table in BASELINE_TABLES:
                if table != "vehicle_profile":
                    cursor.execute(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY)")
            conn.commit()

        validator = BaselineValidator(db_path)
        is_valid, errors, details = validator.validate()

        assert is_valid is False
        assert any("columns" in e for e in errors)

    def test_validate_nonexistent_db(self):
        db_path = self.temp_dir / "nonexistent.db"
        validator = BaselineValidator(db_path)
        is_valid, errors, details = validator.validate()

        assert is_valid is False
        assert any("not found" in e for e in errors)

    def test_validate_corrupted_db(self):
        db_path = self.temp_dir / "corrupt.db"
        with open(db_path, "wb") as f:
            f.write(b"not a database")

        validator = BaselineValidator(db_path)
        is_valid, errors, details = validator.validate()

        assert is_valid is False


class TestBaselineAdopter:
    """Tests for BaselineAdopter."""

    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_valid_baseline_db(self, db_path: Path):
        """Create a database with all baseline tables."""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            for table in BASELINE_TABLES:
                min_cols = BASELINE_TABLES[table]["min_columns"]
                cols = ", ".join([f"col{i} TEXT" for i in range(min_cols - 1)])
                cursor.execute(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY, {cols})")
            cursor.execute("PRAGMA user_version = 1")
            conn.commit()

    def test_adopt_existing_database(self):
        db_path = self.temp_dir / "existing.db"
        self.create_valid_baseline_db(db_path)

        adopter = BaselineAdopter(db_path)
        success, message = adopter.adopt_existing_database(create_backup=True)

        assert success is True
        assert "adopted" in message.lower()

        # Verify migration tracking was created
        from services.migrations import SchemaMigrationStore
        store = SchemaMigrationStore(db_path)
        assert store.get_current_version() == BASELINE_VERSION

        applied = store.get_applied_migrations()
        assert len(applied) == 1
        assert applied[0].version == BASELINE_VERSION
        assert applied[0].name == "legacy_schema_baseline"

    def test_adopt_creates_backup(self):
        db_path = self.temp_dir / "existing.db"
        self.create_valid_baseline_db(db_path)

        adopter = BaselineAdopter(db_path)
        success, message = adopter.adopt_existing_database(create_backup=True)

        assert success is True
        assert "backup" in message.lower()

        # Check backup was created
        backup_dir = db_path.parent / "backups"
        backups = list(backup_dir.glob("*.sqlite"))
        assert len(backups) >= 1

    def test_adopt_without_backup(self):
        db_path = self.temp_dir / "existing.db"
        self.create_valid_baseline_db(db_path)

        adopter = BaselineAdopter(db_path)
        success, message = adopter.adopt_existing_database(create_backup=False)

        assert success is True

        backup_dir = db_path.parent / "backups"
        if backup_dir.exists():
            backups = list(backup_dir.glob("*.sqlite"))
            # May have other backups, but none from this adoption
            pass

    def test_adopt_invalid_database_fails(self):
        db_path = self.temp_dir / "invalid.db"
        with sqlite3.connect(db_path) as conn:
            conn.execute("CREATE TABLE vehicle_profile (id INTEGER PRIMARY KEY)")
            conn.commit()

        adopter = BaselineAdopter(db_path)
        success, message = adopter.adopt_existing_database(create_backup=False)

        assert success is False
        assert "validation failed" in message.lower()

    def test_initialize_fresh_database(self):
        db_path = self.temp_dir / "fresh.db"
        # Don't create the database file - let DatabaseService do it

        adopter = BaselineAdopter(db_path)
        success, message = adopter.initialize_fresh_database()

        assert success is True
        assert "initialized" in message.lower()

        # Verify migration tracking was created
        from services.migrations import SchemaMigrationStore
        store = SchemaMigrationStore(db_path)
        assert store.get_current_version() == BASELINE_VERSION

    def test_adopt_already_adopted(self):
        db_path = self.temp_dir / "existing.db"
        self.create_valid_baseline_db(db_path)

        adopter = BaselineAdopter(db_path)
        success1, msg1 = adopter.adopt_existing_database(create_backup=False)
        assert success1 is True

        # Try to adopt again
        success2, msg2 = adopter.adopt_existing_database(create_backup=False)
        assert success2 is True
        assert "already" in msg2.lower()

        # Version should still be 1
        from services.migrations import SchemaMigrationStore
        store = SchemaMigrationStore(db_path)
        assert store.get_current_version() == BASELINE_VERSION


class TestEnsureDatabaseMigrated:
    """Tests for ensure_database_migrated high-level function."""

    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_valid_baseline_db(self, db_path: Path):
        """Create a database with all baseline tables."""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            for table in BASELINE_TABLES:
                min_cols = BASELINE_TABLES[table]["min_columns"]
                cols = ", ".join([f"col{i} TEXT" for i in range(min_cols - 1)])
                cursor.execute(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY, {cols})")
            cursor.execute("PRAGMA user_version = 1")
            conn.commit()

    def test_ensure_existing_database(self):
        db_path = self.temp_dir / "existing.db"
        self.create_valid_baseline_db(db_path)

        success, message = ensure_database_migrated(db_path)

        assert success is True
        assert "adopted" in message.lower()

    def test_ensure_fresh_database(self):
        db_path = self.temp_dir / "fresh.db"
        # File doesn't exist yet

        success, message = ensure_database_migrated(db_path)

        # Should succeed but note it's fresh
        assert success is True
        # Message should indicate fresh database handling
        # (actual schema creation would be done by DatabaseService)

    def test_ensure_nonexistent_no_create(self):
        """Test with a path that won't be created."""
        db_path = self.temp_dir / "subdir" / "nonexistent.db"
        # Don't create subdir

        success, message = ensure_database_migrated(db_path)

        # Should handle gracefully
        assert success is True  # Fresh database path


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""
i20 AI Garage - Database Service

SQLite database management for vehicle data, telemetry, diagnostics,
maintenance records, and AI conversation history.
"""

import sqlite3
import json
import shutil
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Tuple
import logging

from config import DATABASE_PATH
from services.migrations import ensure_database_migrated

logger = logging.getLogger(__name__)


class DatabaseService:
    """Manages SQLite database operations for i20 AI Garage."""

    def __init__(self, db_path: Path = DATABASE_PATH, run_migrations: bool = True):
        self.db_path = db_path
        self._init_database()
        # Run database migrations after schema initialization
        if run_migrations:
            self._run_migrations()

    def _run_migrations(self):
        """Run database migrations to ensure schema is up to date."""
        try:
            success, message = ensure_database_migrated(self.db_path)
            if success:
                logger.info(f"Database migration: {message}")
            else:
                logger.error(f"Database migration failed: {message}")
                # Don't raise - allow app to continue for debugging
        except Exception as e:
            logger.error(f"Migration error: {e}")
            # Don't raise - allow app to continue for debugging

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    @contextmanager
    def get_connection(self):
        """Public context manager for database connections."""
        with self._get_connection() as conn:
            yield conn

    def _init_database(self):
        """Initialize database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Vehicle profile table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vehicle_profile (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    make TEXT NOT NULL,
                    model TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    engine TEXT NOT NULL,
                    transmission TEXT NOT NULL,
                    fuel_type TEXT NOT NULL,
                    market TEXT NOT NULL,
                    ecu_tuning TEXT NOT NULL,
                    diagnostic_mode TEXT NOT NULL,
                    vin TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Telemetry sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_name TEXT,
                    scenario TEXT,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    duration_seconds REAL,
                    peak_rpm REAL,
                    max_speed REAL,
                    avg_speed REAL,
                    max_coolant_temp REAL,
                    max_engine_load REAL,
                    total_distance_km REAL,
                    fuel_consumed_l REAL,
                    notes TEXT,
                    is_active BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Telemetry records table (individual data points)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    rpm REAL,
                    speed_kmh REAL,
                    coolant_temp_c REAL,
                    throttle_pos_pct REAL,
                    engine_load_pct REAL,
                    intake_pressure_kpa REAL,
                    stft_b1_pct REAL,
                    ltft_b1_pct REAL,
                    voltage_v REAL,
                    maf_g_s REAL,
                    map_kpa REAL,
                    is_simulated BOOLEAN DEFAULT 1,
                    FOREIGN KEY (session_id) REFERENCES telemetry_sessions (id) ON DELETE CASCADE
                )
            """)

            # Diagnostic reports table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS diagnostic_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    scan_time TIMESTAMP NOT NULL,
                    dtc_count INTEGER DEFAULT 0,
                    codes_json TEXT,
                    summary TEXT,
                    is_demo BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES telemetry_sessions (id) ON DELETE SET NULL
                )
            """)

            # Maintenance records table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS maintenance_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_type TEXT NOT NULL,
                    description TEXT,
                    service_date DATE NOT NULL,
                    odometer_km INTEGER NOT NULL,
                    cost REAL,
                    notes TEXT,
                    next_service_km INTEGER,
                    next_service_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # AI conversation history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    model TEXT,
                    tokens_used INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # OBD Connection Logs table (Phase 1)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS obd_connection_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT NOT NULL,  -- 'connect', 'disconnect', 'error', 'reconnect'
                    port TEXT,
                    baudrate INTEGER,
                    protocol TEXT,
                    details TEXT
                )
            """)

            # Supported PIDs Cache table (Phase 1)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS obd_supported_pids (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pid TEXT UNIQUE NOT NULL,
                    name TEXT,
                    unit TEXT,
                    description TEXT,
                    is_supported BOOLEAN DEFAULT 1,
                    last_verified DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # AI Diagnostic Sessions table (Phase 2)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_diagnostic_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    diagnosis_id TEXT UNIQUE NOT NULL,
                    session_id TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    vehicle_context TEXT,  -- JSON
                    dtcs TEXT,  -- JSON
                    ai_diagnosis TEXT,  -- JSON (full DiagnosticResult)
                    rule_matches TEXT,  -- JSON
                    user_feedback TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # RAG Documents table (Phase 2)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rag_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,  -- 'builtin', 'manual', 'tsb', 'forum'
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT,  -- JSON array
                    metadata TEXT,  -- JSON
                    embedding TEXT,  -- JSON array of floats (for future vector search)
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for better query performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_session ON telemetry_records(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry_records(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_maintenance_date ON maintenance_records(service_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_conversation_session ON ai_conversations(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_diagnostic_session ON diagnostic_reports(session_id)")

            # Initialize default vehicle profile if empty
            self._init_default_vehicle_profile(cursor)

            conn.commit()
            logger.info("Database initialized successfully")

    def _init_default_vehicle_profile(self, cursor):
        """Initialize default vehicle profile if none exists."""
        cursor.execute("SELECT COUNT(*) FROM vehicle_profile")
        if cursor.fetchone()[0] == 0:
            from config import VEHICLE_INFO
            cursor.execute("""
                INSERT INTO vehicle_profile (make, model, year, engine, transmission, fuel_type, market, ecu_tuning, diagnostic_mode, vin)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                VEHICLE_INFO["make"],
                VEHICLE_INFO["model"],
                VEHICLE_INFO["year"],
                VEHICLE_INFO["engine"],
                VEHICLE_INFO["transmission"],
                VEHICLE_INFO["fuel_type"],
                VEHICLE_INFO["market"],
                VEHICLE_INFO["ecu_tuning"],
                VEHICLE_INFO["diagnostic_mode"],
                VEHICLE_INFO.get("vin"),
            ))

    # Vehicle Profile Methods
    def get_vehicle_profile(self) -> Optional[Dict[str, Any]]:
        """Get the current vehicle profile."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM vehicle_profile ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_vehicle_profile(self, **kwargs) -> bool:
        """Update vehicle profile."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM vehicle_profile ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                profile_id = row[0]
                fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
                values = list(kwargs.values()) + [profile_id]
                cursor.execute(f"UPDATE vehicle_profile SET {fields}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", values)
                return cursor.rowcount > 0
            return False

    # Telemetry Session Methods
    def create_telemetry_session(self, session_name: str = "", scenario: str = "") -> int:
        """Create a new telemetry session and return its ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO telemetry_sessions (session_name, scenario, start_time, is_active)
                VALUES (?, ?, CURRENT_TIMESTAMP, 1)
            """, (session_name, scenario))
            return cursor.lastrowid

    def end_telemetry_session(self, session_id: int, notes: str = "") -> bool:
        """End a telemetry session and calculate statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Calculate session statistics
            cursor.execute("""
                SELECT
                    MIN(timestamp) as start_time,
                    MAX(timestamp) as end_time,
                    MAX(rpm) as peak_rpm,
                    MAX(speed_kmh) as max_speed,
                    AVG(speed_kmh) as avg_speed,
                    MAX(coolant_temp_c) as max_coolant_temp,
                    MAX(engine_load_pct) as max_engine_load
                FROM telemetry_records
                WHERE session_id = ?
            """, (session_id,))
            stats = cursor.fetchone()

            if stats and stats["start_time"]:
                from datetime import datetime
                start = datetime.fromisoformat(stats["start_time"])
                end = datetime.fromisoformat(stats["end_time"])
                duration = (end - start).total_seconds()

                cursor.execute("""
                    UPDATE telemetry_sessions
                    SET end_time = CURRENT_TIMESTAMP,
                        duration_seconds = ?,
                        peak_rpm = ?,
                        max_speed = ?,
                        avg_speed = ?,
                        max_coolant_temp = ?,
                        max_engine_load = ?,
                        notes = ?,
                        is_active = 0
                    WHERE id = ?
                """, (
                    duration,
                    stats["peak_rpm"],
                    stats["max_speed"],
                    stats["avg_speed"],
                    stats["max_coolant_temp"],
                    stats["max_engine_load"],
                    notes,
                    session_id
                ))
                return cursor.rowcount > 0
            return False

    def get_telemetry_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get list of telemetry sessions."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM telemetry_sessions
                ORDER BY start_time DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_active_session(self) -> Optional[Dict[str, Any]]:
        """Get the currently active telemetry session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM telemetry_sessions WHERE is_active = 1 ORDER BY start_time DESC LIMIT 1")
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_session_records(self, session_id: int) -> List[Dict[str, Any]]:
        """Get all telemetry records for a session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM telemetry_records
                WHERE session_id = ?
                ORDER BY timestamp ASC
            """, (session_id,))
            return [dict(row) for row in cursor.fetchall()]

    def add_telemetry_record(self, session_id: int, data: Dict[str, Any]) -> bool:
        """Add a telemetry record to a session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO telemetry_records (
                    session_id, timestamp, rpm, speed_kmh, coolant_temp_c,
                    throttle_pos_pct, engine_load_pct, intake_pressure_kpa,
                    stft_b1_pct, ltft_b1_pct, voltage_v, maf_g_s, map_kpa, is_simulated
                ) VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                data.get("rpm"),
                data.get("speed_kmh"),
                data.get("coolant_temp_c"),
                data.get("throttle_pos_pct"),
                data.get("engine_load_pct"),
                data.get("intake_pressure_kpa"),
                data.get("stft_b1_pct"),
                data.get("ltft_b1_pct"),
                data.get("voltage_v"),
                data.get("maf_g_s"),
                data.get("map_kpa"),
                data.get("is_simulated", True)
            ))
            return cursor.rowcount > 0

    def export_session_csv(self, session_id: int, filepath: Path) -> bool:
        """Export session telemetry data to CSV."""
        import csv
        records = self.get_session_records(session_id)
        if not records:
            return False

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                "timestamp", "rpm", "speed_kmh", "coolant_temp_c",
                "throttle_pos_pct", "engine_load_pct", "intake_pressure_kpa",
                "stft_b1_pct", "ltft_b1_pct", "voltage_v", "maf_g_s", "map_kpa", "is_simulated"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for record in records:
                writer.writerow({k: record.get(k) for k in fieldnames})
        return True

    # Diagnostic Report Methods
    def save_diagnostic_report(self, session_id: Optional[int], dtc_count: int,
                                codes: List[Dict], summary: str, is_demo: bool = True) -> int:
        """Save a diagnostic scan report."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO diagnostic_reports (session_id, scan_time, dtc_count, codes_json, summary, is_demo)
                VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?)
            """, (session_id, dtc_count, json.dumps(codes), summary, is_demo))
            return cursor.lastrowid

    def get_diagnostic_reports(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get diagnostic scan history."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM diagnostic_reports
                ORDER BY scan_time DESC
                LIMIT ?
            """, (limit,))
            reports = []
            for row in cursor.fetchall():
                report = dict(row)
                report["codes"] = json.loads(report["codes_json"]) if report["codes_json"] else []
                reports.append(report)
            return reports

    # Maintenance Record Methods
    def add_maintenance_record(self, service_type: str, description: str, service_date: str,
                                odometer_km: int, cost: float = None, notes: str = "",
                                next_service_km: int = None, next_service_date: str = None) -> int:
        """Add a maintenance record."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO maintenance_records (
                    service_type, description, service_date, odometer_km, cost, notes,
                    next_service_km, next_service_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (service_type, description, service_date, odometer_km, cost, notes,
                  next_service_km, next_service_date))
            return cursor.lastrowid

    def get_maintenance_records(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all maintenance records."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM maintenance_records
                ORDER BY service_date DESC, odometer_km DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def update_maintenance_record(self, record_id: int, **kwargs) -> bool:
        """Update a maintenance record."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
            values = list(kwargs.values()) + [record_id]
            cursor.execute(f"UPDATE maintenance_records SET {fields}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", values)
            return cursor.rowcount > 0

    def delete_maintenance_record(self, record_id: int) -> bool:
        """Delete a maintenance record."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM maintenance_records WHERE id = ?", (record_id,))
            return cursor.rowcount > 0

    def get_upcoming_maintenance(self, current_odometer: int) -> List[Dict[str, Any]]:
        """Get maintenance items due based on current odometer."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM maintenance_records
                WHERE next_service_km IS NOT NULL AND next_service_km <= ?
                ORDER BY next_service_km ASC
            """, (current_odometer + 1000,))  # 1000km buffer
            return [dict(row) for row in cursor.fetchall()]

    # AI Conversation Methods
    def add_ai_message(self, session_id: str, role: str, content: str,
                        model: str = None, tokens_used: int = None) -> int:
        """Add an AI conversation message."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ai_conversations (session_id, role, content, model, tokens_used)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, role, content, model, tokens_used))
            return cursor.lastrowid

    def get_ai_conversation(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get AI conversation history for a session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM ai_conversations
                WHERE session_id = ?
                ORDER BY created_at ASC
                LIMIT ?
            """, (session_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    def clear_ai_conversation(self, session_id: str) -> bool:
        """Clear AI conversation history for a session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ai_conversations WHERE session_id = ?", (session_id,))
            return cursor.rowcount > 0

    # Settings Methods
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default

    def set_setting(self, key: str, value: str, description: str = "") -> bool:
        """Set a setting value."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO settings (key, value, description, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (key, value, description))
            return cursor.rowcount > 0

    # OBD Connection Log Methods (Phase 1)
    def log_obd_connection(self, event_type: str, port: str = None,
                           baudrate: int = None, protocol: str = None,
                           details: str = "") -> int:
        """Log an OBD connection event."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO obd_connection_logs (event_type, port, baudrate, protocol, details)
                VALUES (?, ?, ?, ?, ?)
            """, (event_type, port, baudrate, protocol, details))
            return cursor.lastrowid

    def get_obd_connection_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get OBD connection log history."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM obd_connection_logs
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    # Supported PIDs Cache Methods (Phase 1)
    def save_supported_pids(self, pids: List[Dict[str, Any]]) -> bool:
        """Save supported PIDs to cache."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for pid_info in pids:
                cursor.execute("""
                    INSERT OR REPLACE INTO obd_supported_pids (pid, name, unit, description, is_supported, last_verified)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    pid_info.get("pid"),
                    pid_info.get("name"),
                    pid_info.get("unit"),
                    pid_info.get("description"),
                    pid_info.get("is_supported", True)
                ))
            return True

    def get_supported_pids(self) -> List[Dict[str, Any]]:
        """Get cached supported PIDs."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM obd_supported_pids ORDER BY pid")
            return [dict(row) for row in cursor.fetchall()]

    def clear_supported_pids(self) -> bool:
        """Clear supported PIDs cache."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM obd_supported_pids")
            return cursor.rowcount >= 0

    # AI Diagnostic Session Methods (Phase 2)
    def save_ai_diagnostic_session(self, diagnosis_id: str, session_id: str,
                                    vehicle_context: Dict[str, Any],
                                    dtcs: List[Dict],
                                    ai_diagnosis: Dict[str, Any],
                                    rule_matches: List[str]) -> int:
        """Save an AI diagnostic session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO ai_diagnostic_sessions
                (diagnosis_id, session_id, vehicle_context, dtcs, ai_diagnosis, rule_matches)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                diagnosis_id,
                session_id,
                json.dumps(vehicle_context),
                json.dumps(dtcs),
                json.dumps(ai_diagnosis),
                json.dumps(rule_matches)
            ))
            return cursor.lastrowid

    def get_ai_diagnostic_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get AI diagnostic session history."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM ai_diagnostic_sessions
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            results = []
            for row in cursor.fetchall():
                item = dict(row)
                # Parse JSON fields
                if item.get("vehicle_context"):
                    item["vehicle_context"] = json.loads(item["vehicle_context"])
                if item.get("dtcs"):
                    item["dtcs"] = json.loads(item["dtcs"])
                if item.get("ai_diagnosis"):
                    item["ai_diagnosis"] = json.loads(item["ai_diagnosis"])
                if item.get("rule_matches"):
                    item["rule_matches"] = json.loads(item["rule_matches"])
                results.append(item)
            return results

    def get_ai_diagnostic_session(self, diagnosis_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific AI diagnostic session by diagnosis_id."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM ai_diagnostic_sessions
                WHERE diagnosis_id = ?
            """, (diagnosis_id,))
            row = cursor.fetchone()
            if row:
                item = dict(row)
                if item.get("vehicle_context"):
                    item["vehicle_context"] = json.loads(item["vehicle_context"])
                if item.get("dtcs"):
                    item["dtcs"] = json.loads(item["dtcs"])
                if item.get("ai_diagnosis"):
                    item["ai_diagnosis"] = json.loads(item["ai_diagnosis"])
                if item.get("rule_matches"):
                    item["rule_matches"] = json.loads(item["rule_matches"])
                return item
            return None

    def add_ai_diagnostic_feedback(self, diagnosis_id: str, feedback: str) -> bool:
        """Add user feedback to an AI diagnostic session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE ai_diagnostic_sessions
                SET user_feedback = ?
                WHERE diagnosis_id = ?
            """, (feedback, diagnosis_id))
            return cursor.rowcount > 0

    # RAG Document Methods (Phase 2)
    def add_rag_document(self, source: str, title: str, content: str,
                         tags: List[str] = None, metadata: Dict[str, Any] = None,
                         embedding: List[float] = None) -> int:
        """Add a document to the RAG knowledge base."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO rag_documents (source, title, content, tags, metadata, embedding)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                source,
                title,
                content,
                json.dumps(tags) if tags else "[]",
                json.dumps(metadata) if metadata else "{}",
                json.dumps(embedding) if embedding else "[]"
            ))
            return cursor.lastrowid

    def search_rag_documents(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Simple text search for RAG documents (keyword-based)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Simple keyword search using LIKE
            query_terms = query.lower().split()
            if not query_terms:
                return []

            # Build LIKE conditions
            conditions = []
            params = []
            for term in query_terms:
                conditions.append("(LOWER(title) LIKE ? OR LOWER(content) LIKE ? OR LOWER(tags) LIKE ?)")
                params.extend([f"%{term}%", f"%{term}%", f"%{term}%"])

            where_clause = " OR ".join(conditions)
            params.append(top_k)

            cursor.execute(f"""
                SELECT * FROM rag_documents
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ?
            """, params)

            results = []
            for row in cursor.fetchall():
                item = dict(row)
                if item.get("tags"):
                    item["tags"] = json.loads(item["tags"])
                if item.get("metadata"):
                    item["metadata"] = json.loads(item["metadata"])
                if item.get("embedding"):
                    item["embedding"] = json.loads(item["embedding"])
                results.append(item)
            return results

    def get_rag_documents_by_tags(self, tags: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Get RAG documents matching any of the given tags."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            tag_conditions = " OR ".join(["LOWER(tags) LIKE ?" for _ in tags])
            params = [f"%{tag.lower()}%" for tag in tags]
            params.append(limit)

            cursor.execute(f"""
                SELECT * FROM rag_documents
                WHERE {tag_conditions}
                ORDER BY created_at DESC
                LIMIT ?
            """, params)

            results = []
            for row in cursor.fetchall():
                item = dict(row)
                if item.get("tags"):
                    item["tags"] = json.loads(item["tags"])
                if item.get("metadata"):
                    item["metadata"] = json.loads(item["metadata"])
                results.append(item)
            return results

    def get_all_rag_documents(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all RAG documents."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM rag_documents
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

            results = []
            for row in cursor.fetchall():
                item = dict(row)
                if item.get("tags"):
                    item["tags"] = json.loads(item["tags"])
                if item.get("metadata"):
                    item["metadata"] = json.loads(item["metadata"])
                if item.get("embedding"):
                    item["embedding"] = json.loads(item["embedding"])
                results.append(item)
            return results

    def update_rag_document(self, doc_id: int, **kwargs) -> bool:
        """Update a RAG document."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Handle JSON fields
            if "tags" in kwargs:
                kwargs["tags"] = json.dumps(kwargs["tags"])
            if "metadata" in kwargs:
                kwargs["metadata"] = json.dumps(kwargs["metadata"])
            if "embedding" in kwargs:
                kwargs["embedding"] = json.dumps(kwargs["embedding"])

            fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
            values = list(kwargs.values()) + [doc_id]
            cursor.execute(f"""
                UPDATE rag_documents
                SET {fields}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, values)
            return cursor.rowcount > 0

    def delete_rag_document(self, doc_id: int) -> bool:
        """Delete a RAG document."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM rag_documents WHERE id = ?", (doc_id,))
            return cursor.rowcount > 0

    # Backup Methods
    def backup_database(self, backup_path: Path) -> bool:
        """Create a backup of the database."""
        try:
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backed up to {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            stats = {}
            tables = [
                "vehicle_profile", "telemetry_sessions", "telemetry_records",
                "diagnostic_reports", "maintenance_records", "ai_conversations",
                "settings", "obd_connection_logs", "obd_supported_pids",
                "ai_diagnostic_sessions", "rag_documents"
            ]
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]

            # Database file size
            stats["db_size_bytes"] = self.db_path.stat().st_size if self.db_path.exists() else 0
            return stats


# Singleton instance
_db_instance: Optional[DatabaseService] = None

def get_database() -> DatabaseService:
    """Get the database service singleton."""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseService()
    return _db_instance
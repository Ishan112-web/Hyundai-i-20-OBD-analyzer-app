"""
i20 AI Garage - Baseline Adoption

Handles adoption of existing databases into the migration system.
"""

import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

from .models import MigrationInfo, BASELINE_VERSION, BASELINE_NAME, BASELINE_DESCRIPTION
from .backup_manager import BackupManager

logger = logging.getLogger(__name__)

# Required tables for baseline (all Phases 1-4)
BASELINE_TABLES = {
    # V1 Core
    "vehicle_profile": {"required": True, "min_columns": 10},
    "telemetry_sessions": {"required": True, "min_columns": 13},
    "telemetry_records": {"required": True, "min_columns": 15},
    "diagnostic_reports": {"required": True, "min_columns": 7},
    "maintenance_records": {"required": True, "min_columns": 10},
    "ai_conversations": {"required": True, "min_columns": 6},
    "settings": {"required": True, "min_columns": 3},
    # Phase 1
    "obd_connection_logs": {"required": True, "min_columns": 6},
    "obd_supported_pids": {"required": True, "min_columns": 6},
    # Phase 2
    "ai_diagnostic_sessions": {"required": True, "min_columns": 8},
    "rag_documents": {"required": True, "min_columns": 8},
    # Phase 3
    "rule_evaluations": {"required": True, "min_columns": 18},
    "rule_findings": {"required": True, "min_columns": 20},
    "rule_triggers": {"required": True, "min_columns": 9},
}


class BaselineValidator:
    """
    Validates that a database matches the expected baseline schema.
    """

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def validate(self) -> Tuple[bool, List[str], Dict]:
        """
        Validate database against baseline requirements.

        Returns:
            Tuple of (is_valid, errors, details_dict)
        """
        errors = []
        details = {
            "tables_found": [],
            "tables_missing": [],
            "columns_checked": {},
            "indexes_found": [],
            "foreign_keys_enabled": False,
            "integrity_ok": False,
            "user_version": 0,
        }

        if not self.db_path.exists():
            errors.append(f"Database file not found: {self.db_path}")
            return False, errors, details

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Integrity check
                cursor.execute("PRAGMA integrity_check")
                integrity = cursor.fetchone()[0]
                details["integrity_ok"] = (integrity == "ok")
                if not details["integrity_ok"]:
                    errors.append(f"Integrity check failed: {integrity}")

                # Foreign keys
                cursor.execute("PRAGMA foreign_keys")
                details["foreign_keys_enabled"] = bool(cursor.fetchone()[0])

                # User version
                cursor.execute("PRAGMA user_version")
                details["user_version"] = cursor.fetchone()[0]

                # Get all tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                existing_tables = {row[0] for row in cursor.fetchall()}
                details["tables_found"] = sorted(existing_tables)

                # Check required tables
                for table_name, req in BASELINE_TABLES.items():
                    if table_name not in existing_tables:
                        if req["required"]:
                            errors.append(f"Required baseline table missing: {table_name}")
                            details["tables_missing"].append(table_name)
                        continue

                    # Validate column count
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    col_count = len(columns)
                    details["columns_checked"][table_name] = col_count

                    if col_count < req["min_columns"]:
                        errors.append(
                            f"Table {table_name} has only {col_count} columns, "
                            f"expected at least {req['min_columns']}"
                        )

                # Check for unexpected tables (not in baseline)
                expected_tables = set(BASELINE_TABLES.keys())
                unexpected = existing_tables - expected_tables
                if unexpected:
                    logger.info(f"Unexpected tables (not in baseline): {sorted(unexpected)}")
                    details["unexpected_tables"] = sorted(unexpected)

                # Check indexes
                cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
                details["indexes_found"] = [row[0] for row in cursor.fetchall()]

        except Exception as e:
            errors.append(f"Validation error: {e}")

        return len(errors) == 0, errors, details


class BaselineAdopter:
    """
    Adopts an existing database into the migration system.

    For existing databases with the correct schema:
    1. Validate baseline compatibility
    2. Create verified backup
    3. Initialize schema_migrations table
    4. Record baseline as applied
    5. Set user_version to baseline version

    For new databases:
    1. Let DatabaseService create schema
    2. Initialize migration tracking
    3. Record baseline as applied
    """

    def __init__(
        self,
        db_path: Path,
        backup_manager: Optional[BackupManager] = None,
    ):
        self.db_path = Path(db_path)
        self.backup_manager = backup_manager or BackupManager(db_path)
        self.validator = BaselineValidator(db_path)

    def adopt_existing_database(self, create_backup: bool = True) -> Tuple[bool, str]:
        """
        Adopt an existing database into the migration system.

        Args:
            create_backup: Whether to create a backup before changes

        Returns:
            Tuple of (success, message)
        """
        # 1. Validate baseline
        logger.info(f"Validating baseline for {self.db_path}")
        is_valid, errors, details = self.validator.validate()

        if not is_valid:
            msg = f"Baseline validation failed: {'; '.join(errors)}"
            logger.error(msg)
            return False, msg

        logger.info(f"Baseline validation passed: {len(details['tables_found'])} tables found")

        # 2. Create backup if requested
        backup_path = None
        if create_backup:
            logger.info("Creating pre-adoption backup...")
            backup_path, backup_meta = self.backup_manager.create_backup(
                prefix="pre_baseline_adoption",
                description="Backup before baseline migration adoption",
                verify=True,
            )
            if backup_path is None:
                return False, "Failed to create backup before baseline adoption"
            if backup_meta and not backup_meta.integrity_ok:
                return False, "Backup verification failed - adoption aborted"
            logger.info(f"Backup created and verified: {backup_path}")

        # 3. Initialize migration tracking
        from .registry import SchemaMigrationStore
        store = SchemaMigrationStore(self.db_path)

        if not store.initialize():
            return False, "Failed to initialize schema_migrations table"

        # 4. Check if already adopted
        current_version = store.get_current_version()
        if current_version >= BASELINE_VERSION:
            logger.info(f"Database already at version {current_version}, skipping baseline adoption")
            return True, f"Database already adopted (version {current_version})"

        # 5. Record baseline migration
        from datetime import datetime
        from .models import AppliedMigration

        baseline_info = MigrationInfo(
            version=BASELINE_VERSION,
            name=BASELINE_NAME,
            description=BASELINE_DESCRIPTION,
            checksum=self._compute_schema_checksum(),
            has_downgrade=False,
        )

        applied = AppliedMigration(
            version=baseline_info.version,
            name=baseline_info.name,
            description=baseline_info.description,
            checksum=baseline_info.checksum,
            applied_at=datetime.now(),
            duration_ms=0.0,
            success=True,
        )

        if not store.record_migration(applied):
            return False, "Failed to record baseline migration"

        # 6. Set user_version for quick version check
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA user_version = {BASELINE_VERSION}")
                conn.commit()
        except Exception as e:
            logger.warning(f"Could not set user_version: {e}")

        msg = f"Successfully adopted existing database at baseline version {BASELINE_VERSION}"
        if backup_path:
            msg += f" (backup: {backup_path.name})"
        logger.info(msg)
        return True, msg

    def initialize_fresh_database(self) -> Tuple[bool, str]:
        """
        Initialize a fresh database with migration tracking.

        This should be called AFTER DatabaseService._init_database()
        and RuleHistoryStore._init_tables() have created the schema.
        """
        logger.info(f"Initializing fresh database migration tracking: {self.db_path}")

        # 1. Initialize migration tracking
        from .registry import SchemaMigrationStore
        store = SchemaMigrationStore(self.db_path)

        if not store.initialize():
            return False, "Failed to initialize schema_migrations table"

        # 2. Record baseline migration
        from datetime import datetime
        from .models import AppliedMigration

        baseline_info = MigrationInfo(
            version=BASELINE_VERSION,
            name=BASELINE_NAME,
            description=BASELINE_DESCRIPTION,
            checksum=self._compute_schema_checksum(),
            has_downgrade=False,
        )

        applied = AppliedMigration(
            version=baseline_info.version,
            name=baseline_info.name,
            description=baseline_info.description,
            checksum=baseline_info.checksum,
            applied_at=datetime.now(),
            duration_ms=0.0,
            success=True,
        )

        if not store.record_migration(applied):
            return False, "Failed to record baseline migration"

        # 3. Set user_version
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA user_version = {BASELINE_VERSION}")
                conn.commit()
        except Exception as e:
            logger.warning(f"Could not set user_version: {e}")

        logger.info(f"Fresh database initialized at baseline version {BASELINE_VERSION}")
        return True, f"Fresh database initialized at version {BASELINE_VERSION}"

    def _compute_schema_checksum(self) -> str:
        """Compute checksum of current database schema."""
        import hashlib
        import json

        schema_data = {
            "tables": {},
            "version": BASELINE_VERSION,
        }

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                for table_name in sorted(BASELINE_TABLES.keys()):
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    schema_data["tables"][table_name] = [
                        {
                            "name": col[1],
                            "type": col[2],
                            "notnull": bool(col[3]),
                            "default": col[4],
                            "pk": bool(col[5]),
                        }
                        for col in columns
                    ]

                # Include indexes
                cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
                schema_data["indexes"] = {row[0]: row[1] or "" for row in cursor.fetchall()}

        except Exception as e:
            logger.warning(f"Could not compute full schema checksum: {e}")

        content = json.dumps(schema_data, sort_keys=True, default=str)
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn


def ensure_database_migrated(db_path: Path) -> Tuple[bool, str]:
    """
    High-level function to ensure a database is migrated.

    Handles both:
    - Existing databases (adopt baseline)
    - Fresh databases (initialize tracking)

    Returns:
        Tuple of (success, message)
    """
    adopter = BaselineAdopter(db_path)

    if db_path.exists():
        # Existing database - adopt it
        logger.info(f"Existing database found, adopting baseline: {db_path}")
        return adopter.adopt_existing_database(create_backup=True)
    else:
        # Fresh database - let DatabaseService create schema first
        # This function should be called AFTER DatabaseService initialization
        logger.info(f"Fresh database, initializing migration tracking: {db_path}")
        return adopter.initialize_fresh_database()
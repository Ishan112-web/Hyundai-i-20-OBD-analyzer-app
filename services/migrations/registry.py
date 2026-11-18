"""
i20 AI Garage - Migration Registry

Discovers, validates, and orders migration modules.
"""

import importlib.util
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

from .models import (
    MigrationInfo,
    AppliedMigration,
    MigrationStatus,
    BASELINE_VERSION,
    BASELINE_NAME,
    BASELINE_DESCRIPTION,
    MIGRATIONS_DIR,
    get_baseline_migration_info,
)

logger = logging.getLogger(__name__)


class MigrationRegistry:
    """
    Discovers and manages migration modules.

    Migration modules are Python files in the versions/ directory
    with the format: {version:04d}_{name}.py

    Each module must expose:
    - MIGRATION_INFO: MigrationInfo instance
    - upgrade(conn): Function to apply migration
    - downgrade(conn): Optional function to rollback migration
    """

    def __init__(self, migrations_dir: Optional[Path] = None):
        self.migrations_dir = migrations_dir or MIGRATIONS_DIR
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Optional[Dict[int, MigrationInfo]] = None
        self._modules: Dict[int, Any] = {}

    def discover_migrations(self) -> List[MigrationInfo]:
        """
        Discover all valid migration modules in the migrations directory.

        Returns:
            List of MigrationInfo sorted by version.

        Raises:
            ValueError: If duplicate versions found or module invalid.
        """
        if self._cache is not None:
            return list(self._cache.values())

        migrations: Dict[int, MigrationInfo] = {}
        seen_versions: Dict[int, Path] = {}

        for py_file in sorted(self.migrations_dir.glob("*.py")):
            if py_file.name.startswith("__"):
                continue

            # Parse version from filename: 0001_name.py
            try:
                version_str = py_file.stem.split("_")[0]
                version = int(version_str)
            except (IndexError, ValueError):
                logger.warning(f"Skipping migration file with invalid name format: {py_file.name}")
                continue

            if version in seen_versions:
                raise ValueError(
                    f"Duplicate migration version {version}: "
                    f"{seen_versions[version].name} and {py_file.name}"
                )

            # Load and validate module
            migration_info = self._load_migration_module(py_file, version)
            if migration_info:
                if migration_info.version != version:
                    raise ValueError(
                        f"Migration version mismatch in {py_file.name}: "
                        f"filename says {version}, MIGRATION_INFO says {migration_info.version}"
                    )
                migrations[version] = migration_info
                seen_versions[version] = py_file

        # Verify sequential versions (no gaps after baseline)
        if migrations:
            max_version = max(migrations.keys())
            expected = set(range(BASELINE_VERSION, max_version + 1))
            missing = expected - set(migrations.keys())
            if missing:
                logger.warning(f"Missing migration versions: {sorted(missing)}")

        # Sort by version
        self._cache = dict(sorted(migrations.items()))
        return list(self._cache.values())

    def _load_migration_module(self, py_file: Path, expected_version: int) -> Optional[MigrationInfo]:
        """Load and validate a single migration module."""
        module_name = f"migrations.versions.{py_file.stem}"

        try:
            spec = importlib.util.spec_from_file_location(module_name, py_file)
            if spec is None or spec.loader is None:
                logger.error(f"Could not load migration module: {py_file}")
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Get MIGRATION_INFO
            if not hasattr(module, "MIGRATION_INFO"):
                logger.error(f"Migration module missing MIGRATION_INFO: {py_file}")
                return None

            migration_info = module.MIGRATION_INFO
            if not isinstance(migration_info, MigrationInfo):
                logger.error(f"MIGRATION_INFO is not a MigrationInfo instance: {py_file}")
                return None

            # Verify checksum if migration file exists
            if not migration_info.verify_checksum(py_file):
                logger.warning(f"Checksum mismatch for {py_file.name} - migration file may have been modified")

            # Verify required functions
            if not hasattr(module, "upgrade") or not callable(module.upgrade):
                logger.error(f"Migration module missing upgrade() function: {py_file}")
                return None

            # Cache module for later execution
            self._modules[expected_version] = module

            return migration_info

        except Exception as e:
            logger.error(f"Failed to load migration module {py_file}: {e}")
            return None

    def get_migration(self, version: int) -> Optional[Tuple[MigrationInfo, Any]]:
        """Get migration info and module for a specific version."""
        migrations = self.discover_migrations()
        for info in migrations:
            if info.version == version:
                return info, self._modules.get(version)
        return None

    def get_pending_migrations(self, current_version: int) -> List[MigrationInfo]:
        """Get migrations that haven't been applied yet."""
        all_migrations = self.discover_migrations()
        return [m for m in all_migrations if m.version > current_version]

    def get_latest_version(self) -> int:
        """Get the highest available migration version."""
        migrations = self.discover_migrations()
        return max((m.version for m in migrations), default=BASELINE_VERSION - 1)

    def validate_migrations(self) -> Tuple[bool, List[str]]:
        """
        Validate all migration modules for consistency.

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        warnings = []
        migrations = self.discover_migrations()

        versions = [m.version for m in migrations]
        if len(versions) != len(set(versions)):
            errors.append("Duplicate migration versions detected")

        # Check for gaps (warnings, not errors)
        if migrations:
            for i in range(len(migrations) - 1):
                if migrations[i + 1].version != migrations[i].version + 1:
                    warnings.append(
                        f"Migration version gap: {migrations[i].version} -> {migrations[i + 1].version}"
                    )

        # Verify each module can be loaded
        for info in migrations:
            module = self._modules.get(info.version)
            if module is None:
                errors.append(f"Module not loaded for version {info.version}")
                continue

            if not hasattr(module, "upgrade") or not callable(module.upgrade):
                errors.append(f"Missing upgrade() in version {info.version}")

            if info.has_downgrade:
                if not hasattr(module, "downgrade") or not callable(module.downgrade):
                    errors.append(f"Has_downgrade=True but no downgrade() in version {info.version}")

        return len(errors) == 0, errors


class SchemaMigrationStore:
    """
    Manages the schema_migrations table in the database.
    Tracks which migrations have been applied.
    """

    SCHEMA_TABLE = "schema_migrations"

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def _get_connection(self):
        """Get a database connection with row factory."""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self) -> bool:
        """Create the schema_migrations table if it doesn't exist."""
        import sqlite3
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.SCHEMA_TABLE} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        version INTEGER NOT NULL UNIQUE,
                        name TEXT NOT NULL,
                        description TEXT,
                        checksum TEXT NOT NULL,
                        applied_at TEXT NOT NULL DEFAULT (datetime('now')),
                        duration_ms REAL DEFAULT 0.0,
                        success BOOLEAN DEFAULT 1,
                        error_message TEXT
                    )
                """)
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to initialize schema_migrations table: {e}")
            return False

    def get_applied_migrations(self) -> List[AppliedMigration]:
        """Get all successfully applied migrations."""
        import sqlite3
        from datetime import datetime
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    SELECT version, name, description, checksum, applied_at, duration_ms, success, error_message
                    FROM {self.SCHEMA_TABLE}
                    WHERE success = 1
                    ORDER BY version
                """)
                rows = cursor.fetchall()

                applied = []
                for row in rows:
                    applied.append(AppliedMigration(
                        version=row["version"],
                        name=row["name"],
                        description=row["description"] or "",
                        checksum=row["checksum"],
                        applied_at=datetime.fromisoformat(row["applied_at"]),
                        duration_ms=row["duration_ms"] or 0.0,
                        success=bool(row["success"]),
                        error_message=row["error_message"],
                    ))
                return applied
        except Exception as e:
            logger.error(f"Failed to get applied migrations: {e}")
        return []

    def get_current_version(self) -> int:
        """Get the current schema version (highest applied)."""
        applied = self.get_applied_migrations()
        return max((m.version for m in applied), default=0)

    def record_migration(self, migration: AppliedMigration) -> bool:
        """Record a migration as applied."""
        import sqlite3
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    INSERT INTO {self.SCHEMA_TABLE} (version, name, description, checksum, applied_at, duration_ms, success, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    migration.version,
                    migration.name,
                    migration.description,
                    migration.checksum,
                    migration.applied_at.isoformat(),
                    migration.duration_ms,
                    1 if migration.success else 0,
                    migration.error_message,
                ))
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Migration version {migration.version} already recorded")
            return False
        except Exception as e:
            logger.error(f"Failed to record migration: {e}")
            return False

    def record_failed_migration(self, version: int, name: str, checksum: str, error: str) -> bool:
        """Record a failed migration attempt."""
        import sqlite3
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    INSERT INTO {self.SCHEMA_TABLE} (version, name, description, checksum, applied_at, duration_ms, success, error_message)
                    VALUES (?, ?, ?, ?, datetime('now'), 0.0, 0, ?)
                """, (version, name, f"FAILED: {error}", checksum, error))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to record failed migration: {e}")
            return False

    def verify_checksums(self, registry: MigrationRegistry) -> Tuple[bool, List[str]]:
        """
        Verify that applied migrations match their source code checksums.

        Returns:
            Tuple of (all_match, list_of_mismatches)
        """
        from .models import BASELINE_VERSION
        applied = self.get_applied_migrations()
        mismatches = []

        for applied_migration in applied:
            # Skip baseline version - its checksum is computed from schema, not file
            if applied_migration.version == BASELINE_VERSION:
                continue

            module = registry._modules.get(applied_migration.version)
            if module is None:
                # Try to find the migration file
                for py_file in registry.migrations_dir.glob(f"{applied_migration.version:04d}_*.py"):
                    if applied_migration.checksum != MigrationInfo.compute_checksum(py_file):
                        mismatches.append(f"Version {applied_migration.version}: source file checksum mismatch")
                    break
                else:
                    mismatches.append(f"Version {applied_migration.version}: migration file not found")
                continue

            # Compute current checksum from module file (normalized)
            # Use registry's migrations_dir
            py_file = registry.migrations_dir / f"{applied_migration.version:04d}_{applied_migration.name}.py"
            if not py_file.exists():
                # Try any matching file
                matches = list(registry.migrations_dir.glob(f"{applied_migration.version:04d}_*.py"))
                if matches:
                    py_file = matches[0]
                else:
                    mismatches.append(f"Version {applied_migration.version}: migration file not found")
                    continue

            # Use MigrationInfo.compute_checksum for consistent normalization
            current_checksum = MigrationInfo.compute_checksum(py_file)
            if current_checksum != applied_migration.checksum:
                mismatches.append(f"Version {applied_migration.version}: checksum mismatch (modified after apply)")

        return len(mismatches) == 0, mismatches


def create_baseline_migration_file(migrations_dir: Path) -> Path:
    """
    Create the baseline migration file (0001_legacy_schema_baseline.py).

    This represents the existing application schema and should not be modified.
    Future migrations are numbered 0002, 0003, etc.
    """
    import hashlib
    import re

    migrations_dir.mkdir(parents=True, exist_ok=True)
    baseline_path = migrations_dir / "0001_legacy_schema_baseline.py"

    if baseline_path.exists():
        return baseline_path

    # Create content with placeholder checksum
    placeholder_checksum = "0" * 64
    content = '''"""
Baseline Migration - Legacy Schema Adoption

This migration represents the existing i20 AI Garage database schema
as of Phases 1-4 completion. It establishes version 1 for databases
that already have the complete schema.

DO NOT MODIFY THIS FILE - it represents the historical baseline.
Future schema changes must be implemented as new migrations (0002, 0003, etc.).
"""

import sqlite3
from pathlib import Path
from services.migrations.models import MigrationInfo


MIGRATION_INFO = MigrationInfo(
    version=1,
    name="legacy_schema_baseline",
    description="Initial schema matching existing i20 AI Garage application (Phases 1-4)",
    checksum="{checksum}",
    has_downgrade=False,
)


def upgrade(conn: sqlite3.Connection) -> None:
    """
    Baseline migration does not modify the database.
    It only records that the baseline schema is present.
    The actual schema is created by DatabaseService._init_database()
    and RuleHistoryStore._init_tables().
    """
    cursor = conn.cursor()

    # Verify baseline tables exist
    required_tables = [
        "vehicle_profile",
        "telemetry_sessions",
        "telemetry_records",
        "diagnostic_reports",
        "maintenance_records",
        "ai_conversations",
        "settings",
        "obd_connection_logs",
        "obd_supported_pids",
        "ai_diagnostic_sessions",
        "rag_documents",
        "rule_evaluations",
        "rule_findings",
        "rule_triggers",
    ]

    for table in required_tables:
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,)
        )
        if not cursor.fetchone():
            raise RuntimeError("Baseline validation failed: required table '{{table}}' not found".format(table=table))

    # All baseline tables exist - migration succeeds
    # No schema changes needed; DatabaseService and RuleHistoryStore handle table creation


def downgrade(conn: sqlite3.Connection) -> None:
    """
    Baseline migration has no downgrade.
    To rollback, restore from backup.
    """
    raise NotImplementedError("Baseline migration cannot be downgraded. Restore from backup.")
'''
    content = content.format(checksum=placeholder_checksum)
    # Compute checksum with normalized placeholder
    normalized = re.sub(r'checksum\s*=\s*["\'][0-9a-fA-F]{64}["\']', 'checksum="PLACEHOLDER"', content)
    actual_checksum = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    # Replace placeholder with actual checksum
    content = content.replace(placeholder_checksum, actual_checksum)

    baseline_path.write_text(content, encoding="utf-8")
    return baseline_path
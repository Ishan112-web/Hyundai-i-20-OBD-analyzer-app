"""
i20 AI Garage - Migration Runner

Executes migrations with transaction safety, backup verification, and recovery.
"""

import logging
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from .models import (
    MigrationInfo,
    MigrationStatus,
    MigrationResult,
    AppliedMigration,
    BASELINE_VERSION,
    SCHEMA_MIGRATIONS_TABLE,
)
from .registry import MigrationRegistry, SchemaMigrationStore
from .backup_manager import BackupManager
from .baseline import ensure_database_migrated

logger = logging.getLogger(__name__)


class MigrationRunner:
    """
    Central migration execution engine.

    Responsibilities:
    - Determine current database version
    - Discover pending migrations
    - Create and verify backups before migration
    - Execute migrations in transactions
    - Record migration history
    - Handle failures safely
    """

    def __init__(
        self,
        db_path: Path,
        migrations_dir: Optional[Path] = None,
        backup_dir: Optional[Path] = None,
        dry_run: bool = False,
    ):
        self.db_path = Path(db_path)
        self.dry_run = dry_run
        self.registry = MigrationRegistry(migrations_dir)
        self.store = SchemaMigrationStore(db_path)
        self.backup_manager = BackupManager(db_path, backup_dir)
        self._lock_acquired = False

    def get_status(self) -> MigrationStatus:
        """Get comprehensive migration status."""
        # Ensure baseline
        current_version = self.store.get_current_version()

        # If no migrations recorded but database exists, check if it needs adoption
        if current_version == 0 and self.db_path.exists():
            # Try to validate as baseline
            from .baseline import BaselineValidator
            validator = BaselineValidator(self.db_path)
            is_valid, errors, details = validator.validate()
            if is_valid:
                current_version = BASELINE_VERSION
                logger.info(f"Database appears to be at baseline version (not yet adopted)")

        pending = self.registry.get_pending_migrations(current_version)
        latest = self.registry.get_latest_version()

        # Check for future version
        is_future = current_version > latest

        # Get applied migrations
        applied = self.store.get_applied_migrations()

        # Verify checksums
        checksums_ok, checksum_errors = self.store.verify_checksums(self.registry)

        # Integrity check
        integrity_ok, integrity_msg = self._check_integrity()

        return MigrationStatus(
            current_version=current_version,
            latest_version=latest,
            pending_migrations=pending,
            applied_migrations=applied,
            is_up_to_date=(len(pending) == 0 and not is_future),
            is_future_version=is_future,
            integrity_ok=integrity_ok and checksums_ok,
            integrity_details=f"Integrity: {integrity_msg}; Checksums: {'OK' if checksums_ok else 'MISMATCH'}",
        )

    def _check_integrity(self) -> Tuple[bool, str]:
        """Quick integrity check."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()
                return result[0] == "ok", result[0]
        except Exception as e:
            return False, f"Error: {e}"

    def validate_pending(self) -> Tuple[bool, List[str]]:
        """Validate all pending migrations can be loaded."""
        return self.registry.validate_migrations()

    @contextmanager
    def _migration_connection(self):
        """
        Context manager for migration execution connection.

        Uses IMMEDIATE transaction for safer concurrent access.
        """
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")

        try:
            # Use IMMEDIATE to acquire write lock early
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _acquire_lock(self) -> bool:
        """Attempt to acquire migration lock via PRAGMA."""
        try:
            with sqlite3.connect(self.db_path, timeout=5.0) as conn:
                conn.execute("PRAGMA busy_timeout = 5000")
                # Try to get exclusive lock
                conn.execute("BEGIN EXCLUSIVE")
                # Check if schema_migrations table exists
                cursor = conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
                )
                if cursor.fetchone():
                    conn.execute("SELECT 1 FROM schema_migrations LIMIT 1")
                conn.rollback()
                self._lock_acquired = True
                return True
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() or "busy" in str(e).lower():
                logger.error("Database is locked by another process - cannot migrate")
                return False
            raise
        except Exception as e:
            logger.warning(f"Could not verify exclusive access: {e}")
            return True  # Proceed anyway

    def _release_lock(self):
        """Release migration lock."""
        self._lock_acquired = False

    def migrate(
        self,
        target_version: Optional[int] = None,
        create_backup: bool = True,
        force: bool = False,
    ) -> List[MigrationResult]:
        """
        Execute pending migrations up to target_version (or latest).

        Args:
            target_version: Migrate up to this version (None = latest)
            create_backup: Create backup before each migration
            force: Skip some safety checks (use with caution)

        Returns:
            List of MigrationResult for each executed migration
        """
        results = []

        # Get status
        status = self.get_status()

        if status.is_future_version:
            raise RuntimeError(
                f"Database version ({status.current_version}) is newer than "
                f"application supports ({status.latest_version}). "
                f"Please update the application."
            )

        if status.is_up_to_date and target_version is None:
            logger.info("Database is already up to date")
            return results

        # Validate migrations
        valid, errors = self.validate_pending()
        if not valid:
            raise RuntimeError(f"Migration validation failed: {errors}")

        # Determine which migrations to run
        pending = status.pending_migrations
        if target_version is not None:
            pending = [m for m in pending if m.version <= target_version]

        if not pending:
            logger.info("No migrations to run")
            return results

        # Acquire lock
        if not self._acquire_lock():
            raise RuntimeError("Could not acquire migration lock - database may be in use")

        try:
            # Ensure baseline is recorded for fresh databases
            # Check if schema_migrations table exists
            table_exists = False
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
                )
                table_exists = cursor.fetchone() is not None

            if not table_exists:
                logger.info("No migration history table found - ensuring baseline...")
                success, msg = ensure_database_migrated(self.db_path)
                if not success:
                    raise RuntimeError(f"Baseline adoption failed: {msg}")
                status = self.get_status()  # Refresh
                pending = status.pending_migrations
                if target_version is not None:
                    pending = [m for m in pending if m.version <= target_version]

            # Execute each migration
            for migration_info in pending:
                logger.info(f"Running migration {migration_info.version}: {migration_info.name}")

                # Create backup before migration
                backup_path = None
                backup_meta = None
                if create_backup:
                    logger.info("Creating pre-migration backup...")
                    backup_path, backup_meta = self.backup_manager.create_backup(
                        prefix=f"pre_migration_{migration_info.version:04d}",
                        description=f"Backup before migration {migration_info.version}: {migration_info.name}",
                        verify=True,
                    )
                    if backup_path is None:
                        result = MigrationResult(
                            success=False,
                            version=migration_info.version,
                            name=migration_info.name,
                            duration_ms=0.0,
                            error_message="Failed to create backup",
                        )
                        results.append(result)
                        break
                    if backup_meta and not backup_meta.integrity_ok:
                        result = MigrationResult(
                            success=False,
                            version=migration_info.version,
                            name=migration_info.name,
                            duration_ms=0.0,
                            error_message="Backup verification failed",
                            backup_path=backup_path,
                            backup_metadata=backup_meta,
                        )
                        results.append(result)
                        break

                # Execute migration
                result = self._execute_migration(migration_info, backup_path, backup_meta)
                results.append(result)

                if not result.success:
                    logger.error(f"Migration {migration_info.version} failed: {result.error_message}")
                    break

                logger.info(f"Migration {migration_info.version} completed in {result.duration_ms:.1f}ms")

            return results

        finally:
            self._release_lock()

    def _execute_migration(
        self,
        migration_info: MigrationInfo,
        backup_path: Optional[Path],
        backup_meta: Optional[Any],
    ) -> MigrationResult:
        """Execute a single migration."""
        module = self.registry._modules.get(migration_info.version)
        if module is None:
            return MigrationResult(
                success=False,
                version=migration_info.version,
                name=migration_info.name,
                duration_ms=0.0,
                error_message="Migration module not loaded",
                backup_path=backup_path,
                backup_metadata=backup_meta,
            )

        start_time = time.perf_counter()

        try:
            if self.dry_run:
                logger.info(f"DRY RUN: Would execute migration {migration_info.version}")
                duration = (time.perf_counter() - start_time) * 1000
                return MigrationResult(
                    success=True,
                    version=migration_info.version,
                    name=migration_info.name,
                    duration_ms=duration,
                    backup_path=backup_path,
                    backup_metadata=backup_meta,
                )

            # Execute in transaction
            with self._migration_connection() as conn:
                cursor = conn.cursor()

                # Run the migration
                module.upgrade(conn)

                # Verify expected schema changes (basic)
                cursor.execute("PRAGMA integrity_check")
                if cursor.fetchone()[0] != "ok":
                    raise RuntimeError("Post-migration integrity check failed")

                cursor.execute("PRAGMA foreign_key_check")
                fk_errors = cursor.fetchall()
                if fk_errors:
                    raise RuntimeError(f"Post-migration foreign key violations: {fk_errors}")

            # Record successful migration
            duration_ms = (time.perf_counter() - start_time) * 1000
            applied = AppliedMigration(
                version=migration_info.version,
                name=migration_info.name,
                description=migration_info.description,
                checksum=migration_info.checksum,
                applied_at=datetime.now(),
                duration_ms=duration_ms,
                success=True,
            )

            if not self.store.record_migration(applied):
                raise RuntimeError("Failed to record migration in history")

            # Update user_version
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(f"PRAGMA user_version = {migration_info.version}")

            return MigrationResult(
                success=True,
                version=migration_info.version,
                name=migration_info.name,
                duration_ms=duration_ms,
                backup_path=backup_path,
                backup_metadata=backup_meta,
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            error_msg = str(e)
            logger.error(f"Migration {migration_info.version} failed: {error_msg}")

            # Record failed migration
            failed = AppliedMigration(
                version=migration_info.version,
                name=migration_info.name,
                description=f"FAILED: {error_msg}",
                checksum=migration_info.checksum,
                applied_at=datetime.now(),
                duration_ms=duration_ms,
                success=False,
                error_message=error_msg,
            )
            self.store.record_failed_migration(
                migration_info.version,
                migration_info.name,
                migration_info.checksum,
                error_msg,
            )

            return MigrationResult(
                success=False,
                version=migration_info.version,
                name=migration_info.name,
                duration_ms=duration_ms,
                error_message=error_msg,
                backup_path=backup_path,
                backup_metadata=backup_meta,
            )

    def dry_run_status(self) -> MigrationStatus:
        """Show what migrations would run without executing."""
        self.dry_run = True
        return self.get_status()

    def verify_database(self) -> Tuple[bool, str]:
        """Comprehensive database verification."""
        status = self.get_status()

        checks = []
        all_ok = True

        # Integrity
        integrity_ok, integrity_msg = self._check_integrity()
        checks.append(("Integrity", integrity_ok, integrity_msg))
        all_ok = all_ok and integrity_ok

        # Checksums
        checksums_ok, checksum_errors = self.store.verify_checksums(self.registry)
        checks.append(("Checksums", checksums_ok, "OK" if checksums_ok else "; ".join(checksum_errors)))
        all_ok = all_ok and checksums_ok

        # Foreign keys
        fk_ok, fk_msg = self._check_foreign_keys()
        checks.append(("Foreign Keys", fk_ok, fk_msg))
        all_ok = all_ok and fk_ok

        # Version consistency
        version_ok = not status.is_future_version
        checks.append(("Version", version_ok, f"Current: {status.current_version}, Latest: {status.latest_version}"))
        all_ok = all_ok and version_ok

        details = "\n".join([f"  {name}: {'PASS' if ok else 'FAIL'} - {msg}" for name, ok, msg in checks])
        return all_ok, f"Verification {'PASSED' if all_ok else 'FAILED'}:\n{details}"

    def _check_foreign_keys(self) -> Tuple[bool, str]:
        """Check foreign key constraints."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA foreign_keys = ON")
                cursor.execute("PRAGMA foreign_key_check")
                errors = cursor.fetchall()
                if errors:
                    return False, f"Violations: {errors}"
                return True, "OK"
        except Exception as e:
            return False, f"Error: {e}"

    def rollback_to_backup(self, backup_path: Path) -> bool:
        """Rollback database to a backup (emergency recovery)."""
        logger.warning(f"Rolling back to backup: {backup_path}")
        return self.backup_manager.restore_backup(backup_path, verify_first=True)


def create_migration_runner(
    db_path: Path,
    migrations_dir: Optional[Path] = None,
    backup_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> MigrationRunner:
    """Factory function for MigrationRunner."""
    return MigrationRunner(db_path, migrations_dir, backup_dir, dry_run)
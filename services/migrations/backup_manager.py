"""
i20 AI Garage - Backup Manager

Reliable SQLite backup and verification using the online backup API.
"""

import hashlib
import logging
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .models import BackupMetadata, DatabaseSchemaSnapshot

logger = logging.getLogger(__name__)


class BackupManager:
    """
    Manages database backups with verification.

    Uses SQLite's online backup API (connection.backup()) which is safe
    for live databases and handles WAL mode correctly.
    """

    def __init__(
        self,
        db_path: Path,
        backup_dir: Optional[Path] = None,
    ):
        self.db_path = Path(db_path)
        self.backup_dir = backup_dir or (self.db_path.parent / "backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def _generate_backup_filename(self, prefix: str = "pre_migration") -> Path:
        """Generate a unique backup filename with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.backup_dir / f"{self.db_path.stem}_{prefix}_{timestamp}.sqlite"

    def create_backup(
        self,
        prefix: str = "pre_migration",
        description: str = "",
        verify: bool = True,
    ) -> Tuple[Optional[Path], Optional[BackupMetadata]]:
        """
        Create a verified backup of the database.

        Args:
            prefix: Filename prefix (e.g., "pre_migration", "manual")
            description: Human-readable description
            verify: Whether to verify backup integrity

        Returns:
            Tuple of (backup_path, backup_metadata) or (None, None) on failure
        """
        if not self.db_path.exists():
            logger.error(f"Source database not found: {self.db_path}")
            return None, None

        backup_path = self._generate_backup_filename(prefix)

        try:
            # Use SQLite online backup API - safe for live databases
            with sqlite3.connect(self.db_path) as src:
                with sqlite3.connect(backup_path) as dst:
                    src.backup(dst)

            logger.info(f"Backup created: {backup_path}")

            # Get source schema version
            source_version = self._get_user_version(self.db_path)

            # Build metadata
            metadata = BackupMetadata(
                backup_path=backup_path,
                source_version=source_version,
                source_db_path=self.db_path,
                size_bytes=backup_path.stat().st_size,
                description=description,
            )

            # Verify if requested
            if verify:
                success, details = self.verify_backup(backup_path, self.db_path)
                metadata.integrity_ok = success
                metadata.integrity_checked_at = datetime.now()
                if not success:
                    logger.error(f"Backup verification failed: {details}")
                    # Don't delete - let user decide
                    return backup_path, metadata

                # Capture row counts and schema
                metadata.row_counts = self._get_row_counts(backup_path)
                metadata.schema_version = self._get_user_version(backup_path)

            return backup_path, metadata

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            if backup_path.exists():
                backup_path.unlink(missing_ok=True)
            return None, None

    def verify_backup(
        self,
        backup_path: Path,
        source_path: Optional[Path] = None,
    ) -> Tuple[bool, str]:
        """
        Verify a backup file is valid and matches source.

        Args:
            backup_path: Path to backup file
            source_path: Optional source database to compare against

        Returns:
            Tuple of (is_valid, details_message)
        """
        if not backup_path.exists():
            return False, f"Backup file not found: {backup_path}"

        try:
            with sqlite3.connect(backup_path) as conn:
                cursor = conn.cursor()

                # 1. Integrity check
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()
                if result[0] != "ok":
                    return False, f"Integrity check failed: {result[0]}"

                # 2. Foreign key check
                cursor.execute("PRAGMA foreign_key_check")
                fk_errors = cursor.fetchall()
                if fk_errors:
                    return False, f"Foreign key violations: {fk_errors}"

                # 3. Schema verification - tables exist
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall() if not row[0].startswith("sqlite_")]
                if not tables:
                    return False, "No tables found in backup"

                # 4. If source provided, compare row counts
                details = f"Tables: {len(tables)}, Integrity: OK"
                if source_path and source_path.exists():
                    source_counts = self._get_row_counts(source_path)
                    backup_counts = self._get_row_counts(backup_path)

                    mismatches = []
                    for table, count in source_counts.items():
                        backup_count = backup_counts.get(table, 0)
                        if count != backup_count:
                            mismatches.append(f"{table}: source={count} backup={backup_count}")

                    if mismatches:
                        return False, f"Row count mismatches: {', '.join(mismatches)}"

                    details += f", Row counts match: {len(source_counts)} tables"

                return True, details

        except Exception as e:
            return False, f"Verification error: {e}"

    def restore_backup(
        self,
        backup_path: Path,
        target_path: Optional[Path] = None,
        verify_first: bool = True,
    ) -> bool:
        """
        Restore database from a verified backup.

        Args:
            backup_path: Path to backup file
            target_path: Target database path (defaults to self.db_path)
            verify_first: Verify backup before restoring

        Returns:
            True if restore successful
        """
        target = target_path or self.db_path

        if not backup_path.exists():
            logger.error(f"Backup not found: {backup_path}")
            return False

        if verify_first:
            valid, msg = self.verify_backup(backup_path)
            if not valid:
                logger.error(f"Backup verification failed, refusing to restore: {msg}")
                return False

        try:
            # Close any existing connections by using a fresh connection
            # Use SQLite online backup API for atomic restore
            with sqlite3.connect(backup_path) as src:
                with sqlite3.connect(target) as dst:
                    src.backup(dst)

            logger.info(f"Database restored from {backup_path} to {target}")
            return True

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False

    def list_backups(self) -> List[BackupMetadata]:
        """List all available backups with metadata."""
        backups = []
        for backup_file in sorted(self.backup_dir.glob(f"{self.db_path.stem}_*.sqlite")):
            try:
                # Try to load metadata from companion .json file
                meta_file = backup_file.with_suffix(".json")
                if meta_file.exists():
                    import json
                    with open(meta_file) as f:
                        data = json.load(f)
                    backups.append(BackupMetadata.from_dict(data))
                else:
                    # Create minimal metadata from file stats
                    stat = backup_file.stat()
                    backups.append(BackupMetadata(
                        backup_path=backup_file,
                        created_at=datetime.fromtimestamp(stat.st_mtime),
                        source_version=0,
                        source_db_path=self.db_path,
                        size_bytes=stat.st_size,
                    ))
            except Exception as e:
                logger.warning(f"Could not read metadata for {backup_file}: {e}")
        return backups

    def save_metadata(self, metadata: BackupMetadata) -> bool:
        """Save backup metadata to companion JSON file."""
        try:
            meta_file = metadata.backup_path.with_suffix(".json")
            with open(meta_file, "w") as f:
                import json
                json.dump(metadata.to_dict(), f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Failed to save backup metadata: {e}")
            return False

    def _get_user_version(self, db_path: Path) -> int:
        """Get PRAGMA user_version from database."""
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA user_version")
                return cursor.fetchone()[0]
        except Exception:
            return 0

    def _get_row_counts(self, db_path: Path) -> Dict[str, int]:
        """Get row counts for all user tables."""
        counts = {}
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                tables = [row[0] for row in cursor.fetchall()]
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    counts[table] = cursor.fetchone()[0]
        except Exception as e:
            logger.warning(f"Could not get row counts: {e}")
        return counts

    def capture_schema_snapshot(self, db_path: Optional[Path] = None) -> DatabaseSchemaSnapshot:
        """Capture complete schema snapshot for comparison."""
        target = db_path or self.db_path
        snapshot = DatabaseSchemaSnapshot()

        try:
            with sqlite3.connect(target) as conn:
                cursor = conn.cursor()

                # Tables and columns
                cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                for row in cursor.fetchall():
                    table_name, sql = row
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    snapshot.tables[table_name] = {
                        "sql": sql,
                        "columns": [
                            {
                                "name": col[1],
                                "type": col[2],
                                "notnull": bool(col[3]),
                                "default": col[4],
                                "pk": bool(col[5]),
                            }
                            for col in columns
                        ],
                    }

                # Indexes
                cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
                for row in cursor.fetchall():
                    snapshot.indexes[row[0]] = row[1] or ""

                # Foreign keys
                for table in snapshot.tables:
                    cursor.execute(f"PRAGMA foreign_key_list({table})")
                    for fk in cursor.fetchall():
                        snapshot.foreign_keys.append({
                            "table": table,
                            "id": fk[0],
                            "seq": fk[1],
                            "table_ref": fk[2],
                            "from": fk[3],
                            "to": fk[4],
                            "on_update": fk[5],
                            "on_delete": fk[6],
                            "match": fk[7],
                        })

                # Triggers
                cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger'")
                for row in cursor.fetchall():
                    snapshot.triggers.append({"name": row[0], "sql": row[1] or ""})

                # Views
                cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='view'")
                for row in cursor.fetchall():
                    snapshot.views[row[0]] = row[1] or ""

                # User version
                cursor.execute("PRAGMA user_version")
                snapshot.user_version = cursor.fetchone()[0]

                snapshot.schema_hash = snapshot.compute_hash()

        except Exception as e:
            logger.error(f"Failed to capture schema snapshot: {e}")

        return snapshot

    def compare_schemas(self, db_path1: Path, db_path2: Path) -> Dict[str, any]:
        """Compare two database schemas."""
        snap1 = self.capture_schema_snapshot(db_path1)
        snap2 = self.capture_schema_snapshot(db_path2)

        return {
            "identical": snap1.schema_hash == snap2.schema_hash,
            "hash1": snap1.schema_hash,
            "hash2": snap2.schema_hash,
            "tables_only_in_1": set(snap1.tables.keys()) - set(snap2.tables.keys()),
            "tables_only_in_2": set(snap2.tables.keys()) - set(snap1.tables.keys()),
            "common_tables": set(snap1.tables.keys()) & set(snap2.tables.keys()),
        }
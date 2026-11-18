"""
Tests for migration runner.
"""

import tempfile
import shutil
import sqlite3
from pathlib import Path
import pytest

from services.migrations import (
    MigrationRunner,
    create_migration_runner,
    MigrationRegistry,
    create_baseline_migration_file,
    MigrationInfo,
)
from services.migrations.models import BASELINE_VERSION


class TestMigrationRunner:
    """Tests for MigrationRunner."""

    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.db_path = self.temp_dir / "test.db"
        self.migrations_dir = self.temp_dir / "migrations"

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_baseline_db(self):
        """Create a database with baseline schema (minimal columns for validation)."""
        from services.migrations.baseline import BASELINE_TABLES
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Create all baseline tables with minimum required columns
            for table, req in BASELINE_TABLES.items():
                min_cols = req["min_columns"]
                cols = ", ".join([f"col{i} TEXT" for i in range(min_cols - 1)])
                cursor.execute(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY, {cols})")
            cursor.execute("PRAGMA user_version = 1")
            conn.commit()

    def create_baseline_schema(self, db_path: Path):
        """Create the full baseline schema as DatabaseService would."""
        self.db_path = db_path
        self.create_baseline_db()

    def create_migration_file(self, version: int, name: str, sql: str = None):
        """Create a migration file with correct checksum."""
        import hashlib
        import re
        if sql is None:
            sql = f"CREATE TABLE migration_{version}_table (id INTEGER PRIMARY KEY)"
        # Create content template with placeholder checksum (64 zeros)
        placeholder_checksum = "0" * 64
        template = '''"""
Migration {version}: {name}
"""
import sqlite3
from services.migrations.models import MigrationInfo

MIGRATION_INFO = MigrationInfo(
    version={version},
    name="{name}",
    description="Test migration {version}",
    checksum="{checksum}",
    has_downgrade=False,
)

def upgrade(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute("""{sql}""")
'''
        content = template.format(version=version, name=name, checksum=placeholder_checksum, sql=sql)
        # Compute checksum with normalized placeholder
        normalized = re.sub(r'checksum\s*=\s*["\'][0-9a-fA-F]{64}["\']', 'checksum="PLACEHOLDER"', content)
        actual_checksum = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        # Replace placeholder with actual checksum
        content = content.replace(placeholder_checksum, actual_checksum)

        filepath = self.migrations_dir / f"{version:04d}_{name}.py"
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content)
        return filepath

    def test_runner_creation(self):
        runner = create_migration_runner(self.db_path, self.migrations_dir)
        assert isinstance(runner, MigrationRunner)

    def test_status_empty_db(self):
        runner = create_migration_runner(self.db_path, self.migrations_dir)
        status = runner.get_status()

        assert status.current_version == 0
        assert status.latest_version == BASELINE_VERSION - 1  # No migrations
        assert status.is_up_to_date is True
        assert status.is_future_version is False

    def test_status_with_baseline_db(self):
        self.create_baseline_schema(self.db_path)
        runner = create_migration_runner(self.db_path, self.migrations_dir)
        status = runner.get_status()

        # Should detect baseline version even without migration record
        assert status.current_version == BASELINE_VERSION

    def test_dry_run(self):
        self.create_baseline_schema(self.db_path)
        self.create_migration_file(2, "add_table_2")
        self.create_migration_file(3, "add_table_3")

        runner = create_migration_runner(self.db_path, self.migrations_dir, dry_run=True)
        status = runner.dry_run_status()

        assert status.current_version == BASELINE_VERSION
        assert status.latest_version == 3
        assert len(status.pending_migrations) == 2
        assert status.pending_migrations[0].version == 2
        assert status.pending_migrations[1].version == 3

    def test_migrate_new_database(self):
        """Test migrating a fresh database (no baseline tables)."""
        runner = create_migration_runner(self.db_path, self.migrations_dir)
        # This should fail because no baseline tables exist
        status = runner.get_status()
        assert status.current_version == 0

    def test_migrate_with_pending(self):
        """Test running migrations on a baseline database."""
        self.create_baseline_db()
        self.create_migration_file(2, "add_feature_a")
        self.create_migration_file(3, "add_feature_b")

        runner = create_migration_runner(self.db_path, self.migrations_dir)
        results = runner.migrate()

        assert len(results) == 2
        assert results[0].success is True
        assert results[0].version == 2
        assert results[1].success is True
        assert results[1].version == 3

        # Verify migrations recorded
        status = runner.get_status()
        assert status.current_version == 3
        assert len(status.applied_migrations) == 3  # baseline + 2 + 3
        assert status.is_up_to_date is True

    def test_migrate_target_version(self):
        self.create_baseline_db()
        self.create_migration_file(2, "add_feature_a")
        self.create_migration_file(3, "add_feature_b")
        self.create_migration_file(4, "add_feature_c")

        runner = create_migration_runner(self.db_path, self.migrations_dir)
        results = runner.migrate(target_version=3)

        assert len(results) == 2  # Only up to version 3
        assert results[0].version == 2
        assert results[1].version == 3

        status = runner.get_status()
        assert status.current_version == 3

    def test_migrate_no_backup(self):
        self.create_baseline_db()
        self.create_migration_file(2, "no_backup_test")

        runner = create_migration_runner(self.db_path, self.migrations_dir)
        results = runner.migrate(create_backup=False)

        assert len(results) == 1
        assert results[0].success is True
        assert results[0].backup_path is None

    def test_migrate_already_up_to_date(self):
        self.create_baseline_db()
        self.create_migration_file(2, "add_feature_a")

        runner = create_migration_runner(self.db_path, self.migrations_dir)
        runner.migrate()  # Apply migration

        # Run again - should be up to date
        results = runner.migrate()
        assert len(results) == 0

    def test_migrate_future_version_error(self):
        self.create_baseline_db()
        self.create_migration_file(2, "add_feature_a")

        runner = create_migration_runner(self.db_path, self.migrations_dir)
        runner.migrate()  # Apply to version 2

        # Remove migration file to simulate future version
        (self.migrations_dir / "0002_add_feature_a.py").unlink()

        runner2 = create_migration_runner(self.db_path, self.migrations_dir)
        with pytest.raises(RuntimeError, match="newer than application supports"):
            runner2.migrate()

    def test_verify_database(self):
        self.create_baseline_db()
        self.create_migration_file(2, "add_feature_a")
        self.create_migration_file(3, "add_feature_b")

        runner = create_migration_runner(self.db_path, self.migrations_dir)
        runner.migrate()

        ok, details = runner.verify_database()
        assert ok is True
        assert "PASSED" in details

    def test_verify_database_with_corruption(self):
        self.create_baseline_db()
        # Create baseline migration file so registry knows about version 1
        from services.migrations import create_baseline_migration_file
        create_baseline_migration_file(self.migrations_dir)
        runner = create_migration_runner(self.db_path, self.migrations_dir)
        runner.migrate()  # Just adopt baseline

        # Corrupt the database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA writable_schema = ON")
            conn.execute("DELETE FROM sqlite_master WHERE type='table'")
            conn.commit()

        ok, details = runner.verify_database()
        assert ok is False

    def test_migration_failure_rollback(self):
        """Test that failed migrations are recorded."""
        self.create_baseline_db()

        # Create a migration that will fail - reference non-existent table
        content = '''"""
Migration 2: failing_migration
"""
import sqlite3
from services.migrations.models import MigrationInfo

MIGRATION_INFO = MigrationInfo(
    version=2,
    name="failing_migration",
    description="This migration fails",
    checksum="0" * 64,
    has_downgrade=False,
)

def upgrade(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute("INSERT INTO nonexistent_table (id) VALUES (1)")  # Table doesn't exist
'''
        filepath = self.migrations_dir / "0002_failing_migration.py"
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content)

        runner = create_migration_runner(self.db_path, self.migrations_dir)
        results = runner.migrate()

        assert len(results) == 1
        assert results[0].success is False
        assert "no such table" in results[0].error_message.lower() or "incomplete input" in results[0].error_message.lower()

        # Check failed migration recorded in database
        import sqlite3
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT version, success, error_message FROM schema_migrations WHERE version = 2")
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == 2
            assert row[1] == 0  # success = 0
            assert "no such table" in row[2].lower()

    def test_checksum_verification(self):
        """Test that checksums are verified after migration."""
        self.create_baseline_db()
        self.create_migration_file(2, "checksum_test")

        runner = create_migration_runner(self.db_path, self.migrations_dir)
        runner.migrate()

        # Modify the migration file
        filepath = self.migrations_dir / "0002_checksum_test.py"
        content = filepath.read_text()
        filepath.write_text(content + "\n# modified\n")

        runner2 = create_migration_runner(self.db_path, self.migrations_dir)
        ok, mismatches = runner2.store.verify_checksums(runner2.registry)

        assert ok is False
        assert len(mismatches) > 0
        assert "checksum mismatch" in mismatches[0].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
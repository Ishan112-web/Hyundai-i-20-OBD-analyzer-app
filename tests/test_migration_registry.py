"""
Tests for migration registry.
"""

import tempfile
import shutil
from pathlib import Path
import pytest

from services.migrations import MigrationRegistry, SchemaMigrationStore, MigrationInfo


class TestMigrationRegistry:
    """Tests for MigrationRegistry."""

    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_migration_file(self, version: int, name: str, content: str = None):
        """Create a migration file."""
        if content is None:
            checksum = "0" * 64
            content = f'''"""
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
    cursor.execute("CREATE TABLE IF NOT EXISTS test_table_{version} (id INTEGER PRIMARY KEY)")
'''
        filepath = self.temp_dir / f"{version:04d}_{name}.py"
        filepath.write_text(content)
        return filepath

    def test_discover_migrations(self):
        self.create_migration_file(1, "first")
        self.create_migration_file(2, "second")
        self.create_migration_file(3, "third")

        registry = MigrationRegistry(self.temp_dir)
        migrations = registry.discover_migrations()

        assert len(migrations) == 3
        assert migrations[0].version == 1
        assert migrations[1].version == 2
        assert migrations[2].version == 3

    def test_discover_migrations_sorted(self):
        self.create_migration_file(3, "third")
        self.create_migration_file(1, "first")
        self.create_migration_file(2, "second")

        registry = MigrationRegistry(self.temp_dir)
        migrations = registry.discover_migrations()

        assert migrations[0].version == 1
        assert migrations[1].version == 2
        assert migrations[2].version == 3

    def test_duplicate_version_raises(self):
        self.create_migration_file(1, "first_a")
        self.create_migration_file(1, "first_b")

        registry = MigrationRegistry(self.temp_dir)
        with pytest.raises(ValueError, match="Duplicate migration version"):
            registry.discover_migrations()

    def test_invalid_filename_skipped(self):
        self.create_migration_file(1, "valid")
        (self.temp_dir / "invalid_name.py").write_text("# No version prefix")

        registry = MigrationRegistry(self.temp_dir)
        migrations = registry.discover_migrations()

        assert len(migrations) == 1
        assert migrations[0].version == 1

    def test_validate_migrations(self):
        self.create_migration_file(1, "first")
        self.create_migration_file(2, "second")

        registry = MigrationRegistry(self.temp_dir)
        valid, errors = registry.validate_migrations()

        assert valid is True
        assert errors == []

    def test_validate_migrations_gap_warning(self):
        self.create_migration_file(1, "first")
        self.create_migration_file(3, "third")  # Gap at 2

        registry = MigrationRegistry(self.temp_dir)
        valid, errors = registry.validate_migrations()

        assert valid is True  # Gaps are warnings, not errors
        assert errors == []  # No errors returned
        # Gap warning is logged but not returned as error

    def test_get_pending_migrations(self):
        self.create_migration_file(1, "first")
        self.create_migration_file(2, "second")
        self.create_migration_file(3, "third")

        registry = MigrationRegistry(self.temp_dir)
        pending = registry.get_pending_migrations(1)

        assert len(pending) == 2
        assert pending[0].version == 2
        assert pending[1].version == 3

    def test_get_latest_version(self):
        self.create_migration_file(1, "first")
        self.create_migration_file(5, "fifth")

        registry = MigrationRegistry(self.temp_dir)
        latest = registry.get_latest_version()

        assert latest == 5

    def test_empty_registry(self):
        registry = MigrationRegistry(self.temp_dir)
        migrations = registry.discover_migrations()
        assert migrations == []

        latest = registry.get_latest_version()
        assert latest == 0  # BASELINE_VERSION - 1


class TestSchemaMigrationStore:
    """Tests for SchemaMigrationStore."""

    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.db_path = self.temp_dir / "test.db"

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialize(self):
        store = SchemaMigrationStore(self.db_path)
        assert store.initialize() is True

        # Second initialize should succeed (idempotent)
        assert store.initialize() is True

    def test_record_and_get_migration(self):
        store = SchemaMigrationStore(self.db_path)
        store.initialize()

        from services.migrations.models import AppliedMigration
        from datetime import datetime

        migration = AppliedMigration(
            version=1,
            name="test",
            description="Test migration",
            checksum="a" * 64,
            applied_at=datetime.now(),
            duration_ms=100.0,
            success=True,
        )

        assert store.record_migration(migration) is True

        applied = store.get_applied_migrations()
        assert len(applied) == 1
        assert applied[0].version == 1
        assert applied[0].name == "test"
        assert applied[0].success is True

    def test_record_duplicate_version_fails(self):
        store = SchemaMigrationStore(self.db_path)
        store.initialize()

        from services.migrations.models import AppliedMigration
        from datetime import datetime

        migration = AppliedMigration(
            version=1,
            name="test",
            description="Test",
            checksum="a" * 64,
            applied_at=datetime.now(),
        )

        assert store.record_migration(migration) is True
        assert store.record_migration(migration) is False  # Duplicate

    def test_get_current_version(self):
        store = SchemaMigrationStore(self.db_path)
        store.initialize()

        assert store.get_current_version() == 0

        from services.migrations.models import AppliedMigration
        from datetime import datetime

        for v in [1, 2, 3]:
            migration = AppliedMigration(
                version=v,
                name=f"migration_{v}",
                description="",
                checksum="a" * 64,
                applied_at=datetime.now(),
            )
            store.record_migration(migration)

        assert store.get_current_version() == 3

    def test_record_failed_migration(self):
        store = SchemaMigrationStore(self.db_path)
        store.initialize()

        assert store.record_failed_migration(1, "failed_migration", "a" * 64, "Error message") is True

        applied = store.get_applied_migrations()
        assert len(applied) == 0  # Failed migrations not in successful list

        # But we can verify it was recorded by checking the table directly
        import sqlite3
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT version, success, error_message FROM schema_migrations")
            rows = cursor.fetchall()
            assert len(rows) == 1
            assert rows[0][0] == 1
            assert rows[0][1] == 0  # success = 0
            assert rows[0][2] == "Error message"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
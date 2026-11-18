"""
Tests for backup manager.
"""

import tempfile
import shutil
import sqlite3
from pathlib import Path
import pytest

from services.migrations import BackupManager


class TestBackupManager:
    """Tests for BackupManager."""

    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.db_path = self.temp_dir / "source.db"
        self.backup_dir = self.temp_dir / "backups"

        # Create a test database with some data
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)")
            cursor.execute("CREATE TABLE another_table (id INTEGER PRIMARY KEY, value INTEGER)")
            for i in range(10):
                cursor.execute("INSERT INTO test_table (name) VALUES (?)", (f"name_{i}",))
            for i in range(5):
                cursor.execute("INSERT INTO another_table (value) VALUES (?)", (i * 10,))
            cursor.execute("PRAGMA user_version = 1")
            conn.commit()

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_backup(self):
        manager = BackupManager(self.db_path, self.backup_dir)
        backup_path, metadata = manager.create_backup(prefix="test", description="Test backup")

        assert backup_path is not None
        assert backup_path.exists()
        assert metadata is not None
        assert metadata.integrity_ok is True
        assert metadata.source_version == 1
        assert metadata.row_counts["test_table"] == 10
        assert metadata.row_counts["another_table"] == 5

    def test_create_backup_no_verify(self):
        manager = BackupManager(self.db_path, self.backup_dir)
        backup_path, metadata = manager.create_backup(verify=False)

        assert backup_path is not None
        assert metadata.integrity_ok is False  # Not checked
        assert metadata.integrity_checked_at is None

    def test_verify_backup(self):
        manager = BackupManager(self.db_path, self.backup_dir)
        backup_path, _ = manager.create_backup()

        # Verify against source
        ok, details = manager.verify_backup(backup_path, self.db_path)
        assert ok is True
        assert "Row counts match" in details

    def test_verify_backup_standalone(self):
        manager = BackupManager(self.db_path, self.backup_dir)
        backup_path, _ = manager.create_backup()

        # Verify without source comparison
        ok, details = manager.verify_backup(backup_path)
        assert ok is True
        assert "Integrity: OK" in details

    def test_verify_corrupted_backup(self):
        manager = BackupManager(self.db_path, self.backup_dir)
        backup_path, _ = manager.create_backup()

        # Corrupt the backup
        with open(backup_path, "wb") as f:
            f.write(b"corrupted data")

        ok, details = manager.verify_backup(backup_path)
        assert ok is False

    def test_restore_backup(self):
        manager = BackupManager(self.db_path, self.backup_dir)
        backup_path, _ = manager.create_backup()

        # Modify source
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM test_table")
            conn.commit()

        # Restore
        target = self.temp_dir / "restored.db"
        success = manager.restore_backup(backup_path, target)

        assert success is True
        assert target.exists()

        # Verify restored data
        with sqlite3.connect(target) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM test_table")
            assert cursor.fetchone()[0] == 10

    def test_restore_to_same_path(self):
        manager = BackupManager(self.db_path, self.backup_dir)
        backup_path, _ = manager.create_backup()

        # Modify source
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM test_table")
            conn.commit()

        # Restore to same path
        success = manager.restore_backup(backup_path, self.db_path)

        assert success is True

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM test_table")
            assert cursor.fetchone()[0] == 10

    def test_list_backups(self):
        manager = BackupManager(self.db_path, self.backup_dir)

        # Create multiple backups
        for i in range(3):
            manager.create_backup(prefix=f"backup_{i}")

        backups = manager.list_backups()
        assert len(backups) == 3

        # Should be sorted by name (which includes timestamp)
        for b in backups:
            assert b.backup_path.exists()

    def test_capture_schema_snapshot(self):
        manager = BackupManager(self.db_path, self.backup_dir)
        snapshot = manager.capture_schema_snapshot()

        assert "test_table" in snapshot.tables
        assert "another_table" in snapshot.tables
        assert snapshot.user_version == 1
        assert len(snapshot.schema_hash) == 64

    def test_compare_schemas_identical(self):
        manager = BackupManager(self.db_path, self.backup_dir)
        backup_path, _ = manager.create_backup()

        result = manager.compare_schemas(self.db_path, backup_path)
        assert result["identical"] is True
        assert result["hash1"] == result["hash2"]

    def test_compare_schemas_different(self):
        manager = BackupManager(self.db_path, self.backup_dir)

        # Create another database with different schema
        other_db = self.temp_dir / "other.db"
        with sqlite3.connect(other_db) as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE different_table (id INTEGER PRIMARY KEY)")
            conn.commit()

        result = manager.compare_schemas(self.db_path, other_db)
        assert result["identical"] is False
        assert "different_table" in result["tables_only_in_2"]
        assert "test_table" in result["tables_only_in_1"]

    def test_backup_nonexistent_db(self):
        manager = BackupManager(self.temp_dir / "nonexistent.db", self.backup_dir)
        backup_path, metadata = manager.create_backup()
        assert backup_path is None
        assert metadata is None

    def test_save_and_load_metadata(self):
        manager = BackupManager(self.db_path, self.backup_dir)
        backup_path, metadata = manager.create_backup()

        # Save metadata
        assert manager.save_metadata(metadata) is True

        # Load backups (should find the metadata file)
        backups = manager.list_backups()
        assert len(backups) >= 1

        # Find our backup
        found = False
        for b in backups:
            if b.backup_path == backup_path:
                found = True
                assert b.integrity_ok is True
                assert b.row_counts == metadata.row_counts
                break
        assert found


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
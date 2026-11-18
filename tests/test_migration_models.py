"""
Tests for migration models.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
import tempfile
import pytest

from services.migrations.models import (
    MigrationInfo,
    AppliedMigration,
    MigrationStatus,
    BackupMetadata,
    MigrationResult,
    DatabaseSchemaSnapshot,
    BASELINE_VERSION,
    BASELINE_NAME,
    BASELINE_DESCRIPTION,
    get_baseline_migration_info,
)


class TestMigrationInfo:
    """Tests for MigrationInfo model."""

    def test_valid_migration_info(self):
        info = MigrationInfo(
            version=1,
            name="test_migration",
            description="Test migration",
            checksum="a" * 64,
        )
        assert info.version == 1
        assert info.name == "test_migration"
        assert info.checksum == "a" * 64
        assert info.has_downgrade is False

    def test_invalid_checksum_length(self):
        with pytest.raises(ValueError, match="at least 64 characters"):
            MigrationInfo(
                version=1,
                name="test",
                checksum="short",
            )

    def test_invalid_checksum_hex(self):
        with pytest.raises(ValueError, match="Checksum must be valid hex"):
            MigrationInfo(
                version=1,
                name="test",
                checksum="g" * 64,
            )

    def test_checksum_lowercase_conversion(self):
        info = MigrationInfo(
            version=1,
            name="test",
            checksum="A" * 64,
        )
        assert info.checksum == "a" * 64

    def test_compute_checksum(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("test content")
            f.flush()
            path = Path(f.name)

        try:
            info = MigrationInfo(version=1, name="test", checksum="0" * 64)
            checksum = info.compute_checksum(path)
            expected = hashlib.sha256(b"test content").hexdigest()
            assert checksum == expected
        finally:
            path.unlink()

    def test_verify_checksum(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("test content")
            f.flush()
            path = Path(f.name)

        try:
            expected = hashlib.sha256(b"test content").hexdigest()
            info = MigrationInfo(version=1, name="test", checksum=expected)
            assert info.verify_checksum(path) is True

            info2 = MigrationInfo(version=1, name="test", checksum="0" * 64)
            assert info2.verify_checksum(path) is False
        finally:
            path.unlink()


class TestAppliedMigration:
    """Tests for AppliedMigration model."""

    def test_applied_migration(self):
        applied = AppliedMigration(
            version=1,
            name="test",
            description="Test",
            checksum="a" * 64,
            applied_at=datetime.now(),
            duration_ms=100.0,
            success=True,
        )
        assert applied.is_failed is False

    def test_failed_migration(self):
        applied = AppliedMigration(
            version=1,
            name="test",
            description="Test",
            checksum="a" * 64,
            success=False,
            error_message="Something failed",
        )
        assert applied.is_failed is True


class TestBackupMetadata:
    """Tests for BackupMetadata model."""

    def test_to_dict_and_from_dict(self):
        metadata = BackupMetadata(
            backup_path=Path("backup.sqlite"),
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            source_version=1,
            source_db_path=Path("db.sqlite"),
            size_bytes=1024,
            integrity_ok=True,
            integrity_checked_at=datetime(2024, 1, 1, 12, 5, 0),
            row_counts={"table1": 100, "table2": 200},
            schema_version=1,
            description="Test backup",
        )

        data = metadata.to_dict()
        assert data["backup_path"] == "backup.sqlite"
        assert data["created_at"] == "2024-01-01T12:00:00"
        assert data["integrity_checked_at"] == "2024-01-01T12:05:00"
        assert data["row_counts"] == {"table1": 100, "table2": 200}

        restored = BackupMetadata.from_dict(data)
        assert restored.backup_path == Path("backup.sqlite")
        assert restored.created_at == datetime(2024, 1, 1, 12, 0, 0)
        assert restored.integrity_checked_at == datetime(2024, 1, 1, 12, 5, 0)
        assert restored.row_counts == {"table1": 100, "table2": 200}

    def test_from_dict_with_none_dates(self):
        data = {
            "backup_path": "/tmp/backup.sqlite",
            "created_at": "2024-01-01T12:00:00",
            "source_version": 1,
            "source_db_path": "/tmp/db.sqlite",
            "size_bytes": 1024,
            "integrity_ok": True,
            "integrity_checked_at": None,
            "row_counts": {},
            "schema_version": 1,
            "description": "",
        }
        restored = BackupMetadata.from_dict(data)
        assert restored.integrity_checked_at is None


class TestDatabaseSchemaSnapshot:
    """Tests for DatabaseSchemaSnapshot model."""

    def test_compute_hash(self):
        snapshot = DatabaseSchemaSnapshot(
            tables={"t1": {"columns": []}},
            indexes={"idx1": ["CREATE INDEX..."]},
            foreign_keys=[{"table": "t1", "to": "t2"}],
            triggers=[{"name": "trg1"}],
            views={"v1": "CREATE VIEW..."},
            user_version=1,
        )
        hash1 = snapshot.compute_hash()
        assert len(hash1) == 64

        # Same data should produce same hash
        snapshot2 = DatabaseSchemaSnapshot(
            tables={"t1": {"columns": []}},
            indexes={"idx1": ["CREATE INDEX..."]},
            foreign_keys=[{"table": "t1", "to": "t2"}],
            triggers=[{"name": "trg1"}],
            views={"v1": "CREATE VIEW..."},
            user_version=1,
        )
        assert snapshot2.compute_hash() == hash1

        # Different data should produce different hash
        snapshot3 = DatabaseSchemaSnapshot(user_version=2)
        assert snapshot3.compute_hash() != hash1


class TestConstants:
    """Tests for module constants."""

    def test_baseline_version(self):
        assert BASELINE_VERSION == 1

    def test_baseline_name(self):
        assert BASELINE_NAME == "legacy_schema_baseline"

    def test_baseline_description(self):
        assert "i20 AI Garage" in BASELINE_DESCRIPTION

    def test_get_baseline_migration_info(self):
        info = get_baseline_migration_info()
        assert info.version == BASELINE_VERSION
        assert info.name == BASELINE_NAME
        assert info.description == BASELINE_DESCRIPTION
        assert info.has_downgrade is False
        assert len(info.checksum) == 64  # Placeholder


class TestMigrationResult:
    """Tests for MigrationResult model."""

    def test_success_summary(self):
        result = MigrationResult(
            success=True,
            version=1,
            name="test",
            duration_ms=150.5,
        )
        assert "succeeded" in result.summary
        assert "150.5" in result.summary

    def test_failure_summary(self):
        result = MigrationResult(
            success=False,
            version=1,
            name="test",
            duration_ms=10.0,
            error_message="Something went wrong",
        )
        assert "FAILED" in result.summary
        assert "Something went wrong" in result.summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
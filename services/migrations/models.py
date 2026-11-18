"""
i20 AI Garage - Migration Models

Pydantic models for database migration metadata and state.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator


class MigrationInfo(BaseModel):
    """
    Metadata for a single migration.

    Each migration module must expose a MIGRATION_INFO instance.
    """

    version: int = Field(..., gt=0, description="Migration version number (1, 2, 3...)")
    name: str = Field(..., min_length=1, description="Human-readable migration name")
    description: str = Field(default="", description="Detailed description of changes")
    checksum: str = Field(..., min_length=64, max_length=64, description="SHA256 of migration source")

    # Optional rollback
    has_downgrade: bool = Field(default=False, description="Whether downgrade is implemented")

    @field_validator("checksum")
    @classmethod
    def validate_checksum(cls, v: str) -> str:
        if len(v) != 64:
            raise ValueError("Checksum must be 64-character SHA256 hex string")
        try:
            int(v, 16)
        except ValueError:
            raise ValueError("Checksum must be valid hex")
        return v.lower()

    @classmethod
    def compute_checksum(cls, migration_path: Path) -> str:
        """Compute SHA256 of migration file content (excluding checksum field)."""
        content = migration_path.read_text(encoding="utf-8")
        # Normalize checksum field to placeholder for consistent hashing
        import re
        # Replace any 64-char hex checksum with placeholder
        normalized = re.sub(r'checksum\s*=\s*["\'][0-9a-fA-F]{64}["\']', 'checksum="PLACEHOLDER"', content)
        normalized = re.sub(r'checksum\s*=\s*["\']{64}["\']', 'checksum="PLACEHOLDER"', normalized)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def verify_checksum(self, migration_path: Path) -> bool:
        """Verify migration file matches recorded checksum."""
        return self.checksum == self.compute_checksum(migration_path)


class AppliedMigration(BaseModel):
    """Record of a migration that has been applied to the database."""

    version: int = Field(..., gt=0)
    name: str
    description: str
    checksum: str
    applied_at: datetime = Field(default_factory=datetime.now)
    duration_ms: float = Field(default=0.0, description="Execution duration in milliseconds")
    success: bool = True
    error_message: Optional[str] = None

    @property
    def is_failed(self) -> bool:
        return not self.success


class MigrationStatus(BaseModel):
    """Overall migration status of a database."""

    current_version: int = Field(default=0, description="Current database schema version")
    latest_version: int = Field(default=0, description="Latest available migration version")
    pending_migrations: List[MigrationInfo] = Field(default_factory=list)
    applied_migrations: List[AppliedMigration] = Field(default_factory=list)
    is_up_to_date: bool = True
    is_future_version: bool = Field(default=False, description="Database ahead of application")
    last_checked: datetime = Field(default_factory=datetime.now)
    integrity_ok: bool = True
    integrity_details: Optional[str] = None


class BackupMetadata(BaseModel):
    """Metadata for a database backup."""

    backup_path: Path
    created_at: datetime = Field(default_factory=datetime.now)
    source_version: int
    source_db_path: Path
    size_bytes: int
    integrity_ok: bool = False
    integrity_checked_at: Optional[datetime] = None
    row_counts: Dict[str, int] = Field(default_factory=dict)
    schema_version: int = 0
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "backup_path": str(self.backup_path),
            "created_at": self.created_at.isoformat(),
            "source_version": self.source_version,
            "source_db_path": str(self.source_db_path),
            "size_bytes": self.size_bytes,
            "integrity_ok": self.integrity_ok,
            "integrity_checked_at": self.integrity_checked_at.isoformat() if self.integrity_checked_at else None,
            "row_counts": self.row_counts,
            "schema_version": self.schema_version,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BackupMetadata":
        data = data.copy()
        data["backup_path"] = Path(data["backup_path"])
        data["source_db_path"] = Path(data["source_db_path"])
        if data.get("created_at"):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("integrity_checked_at"):
            data["integrity_checked_at"] = datetime.fromisoformat(data["integrity_checked_at"])
        return cls(**data)


class MigrationResult(BaseModel):
    """Result of a migration operation."""

    success: bool
    version: int
    name: str
    duration_ms: float
    error_message: Optional[str] = None
    backup_path: Optional[Path] = None
    backup_metadata: Optional[BackupMetadata] = None

    @property
    def summary(self) -> str:
        if self.success:
            return f"Migration {self.version} ({self.name}) succeeded in {self.duration_ms:.1f}ms"
        return f"Migration {self.version} ({self.name}) FAILED: {self.error_message}"


class DatabaseSchemaSnapshot(BaseModel):
    """Snapshot of database schema for verification."""

    tables: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    indexes: Dict[str, List[str]] = Field(default_factory=dict)
    foreign_keys: List[Dict[str, Any]] = Field(default_factory=list)
    triggers: List[Dict[str, Any]] = Field(default_factory=list)
    views: Dict[str, str] = Field(default_factory=dict)
    user_version: int = 0
    schema_hash: str = ""

    def compute_hash(self) -> str:
        """Compute deterministic hash of schema."""
        content = json.dumps({
            "tables": self.tables,
            "indexes": self.indexes,
            "foreign_keys": self.foreign_keys,
            "triggers": self.triggers,
            "views": self.views,
            "user_version": self.user_version,
        }, sort_keys=True, default=str)
        return hashlib.sha256(content.encode("utf-8")).hexdigest()


# Constants
BASELINE_VERSION = 1
BASELINE_NAME = "legacy_schema_baseline"
BASELINE_DESCRIPTION = "Initial schema matching existing i20 AI Garage application (Phases 1-4)"

MIGRATIONS_DIR = Path(__file__).parent / "versions"
SCHEMA_MIGRATIONS_TABLE = "schema_migrations"


def get_schema_migrations_ddl() -> str:
    """DDL for the schema_migrations tracking table."""
    return f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA_MIGRATIONS_TABLE} (
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
    """


def get_baseline_migration_info() -> MigrationInfo:
    """MigrationInfo for the baseline (legacy schema adoption)."""
    # This is a placeholder - actual checksum computed at runtime
    return MigrationInfo(
        version=BASELINE_VERSION,
        name=BASELINE_NAME,
        description=BASELINE_DESCRIPTION,
        checksum="0" * 64,  # Will be computed from actual schema
        has_downgrade=False,
    )
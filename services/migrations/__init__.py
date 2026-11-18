"""
i20 AI Garage - Database Migrations Package

Provides a custom migration system for safe, versioned schema evolution.
"""

from .models import (
    MigrationInfo,
    AppliedMigration,
    MigrationStatus,
    BackupMetadata,
    MigrationResult,
    DatabaseSchemaSnapshot,
    BASELINE_VERSION,
    BASELINE_NAME,
    BASELINE_DESCRIPTION,
    MIGRATIONS_DIR,
    SCHEMA_MIGRATIONS_TABLE,
    get_schema_migrations_ddl,
    get_baseline_migration_info,
)

from .registry import (
    MigrationRegistry,
    SchemaMigrationStore,
    create_baseline_migration_file,
)

from .backup_manager import BackupManager

from .baseline import (
    BaselineValidator,
    BaselineAdopter,
    ensure_database_migrated,
    BASELINE_TABLES,
)

from .runner import (
    MigrationRunner,
    create_migration_runner,
)

__all__ = [
    # Models
    "MigrationInfo",
    "AppliedMigration",
    "MigrationStatus",
    "BackupMetadata",
    "MigrationResult",
    "DatabaseSchemaSnapshot",
    "BASELINE_VERSION",
    "BASELINE_NAME",
    "BASELINE_DESCRIPTION",
    "MIGRATIONS_DIR",
    "SCHEMA_MIGRATIONS_TABLE",
    "get_schema_migrations_ddl",
    "get_baseline_migration_info",
    # Registry
    "MigrationRegistry",
    "SchemaMigrationStore",
    "create_baseline_migration_file",
    # Backup
    "BackupManager",
    # Baseline
    "BaselineValidator",
    "BaselineAdopter",
    "ensure_database_migrated",
    "BASELINE_TABLES",
    # Runner
    "MigrationRunner",
    "create_migration_runner",
]
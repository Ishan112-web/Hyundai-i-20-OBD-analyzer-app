"""
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
    checksum="3e5383c5bdb5fffdb7b9c38a8f6173a61907f22ccc63a441b28a189ba6ded0eb",  # Computed at runtime from actual schema
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
            raise RuntimeError(f"Baseline validation failed: required table '{table}' not found")

    # All baseline tables exist - migration succeeds
    # No schema changes needed; DatabaseService and RuleHistoryStore handle table creation


def downgrade(conn: sqlite3.Connection) -> None:
    """
    Baseline migration has no downgrade.
    To rollback, restore from backup.
    """
    raise NotImplementedError("Baseline migration cannot be downgraded. Restore from backup.")

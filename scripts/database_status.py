#!/usr/bin/env python3
"""
i20 AI Garage - Database Status CLI

Shows current migration status and database health.
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATABASE_PATH
from services.migrations import create_migration_runner


def main():
    parser = argparse.ArgumentParser(description="Show database migration status")
    parser.add_argument("--db", type=Path, default=DATABASE_PATH, help="Database path")
    parser.add_argument("--migrations-dir", type=Path, help="Migrations directory")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--verify", action="store_true", help="Run full verification")
    args = parser.parse_args()

    runner = create_migration_runner(args.db, args.migrations_dir)

    if args.verify:
        ok, details = runner.verify_database()
        print(details)
        sys.exit(0 if ok else 1)

    status = runner.get_status()

    if args.json:
        import json
        from dataclasses import asdict
        # Convert to dict manually since MigrationStatus is a Pydantic model
        data = {
            "current_version": status.current_version,
            "latest_version": status.latest_version,
            "is_up_to_date": status.is_up_to_date,
            "is_future_version": status.is_future_version,
            "integrity_ok": status.integrity_ok,
            "integrity_details": status.integrity_details,
            "applied_migrations": [
                {
                    "version": m.version,
                    "name": m.name,
                    "description": m.description,
                    "checksum": m.checksum,
                    "applied_at": m.applied_at.isoformat() if m.applied_at else None,
                    "duration_ms": m.duration_ms,
                    "success": m.success,
                    "error_message": m.error_message,
                }
                for m in status.applied_migrations
            ],
            "pending_migrations": [
                {
                    "version": m.version,
                    "name": m.name,
                    "description": m.description,
                    "checksum": m.checksum,
                    "has_downgrade": m.has_downgrade,
                }
                for m in status.pending_migrations
            ],
        }
        print(json.dumps(data, indent=2))
        return

    # Human-readable output
    print("=" * 60)
    print("DATABASE MIGRATION STATUS")
    print("=" * 60)
    print(f"Database: {args.db}")
    print(f"Current Version: {status.current_version}")
    print(f"Latest Version:  {status.latest_version}")
    print(f"Up to Date:      {'YES' if status.is_up_to_date else 'NO'}")
    print(f"Future Version:  {'YES' if status.is_future_version else 'NO'}")
    print(f"Integrity OK:    {'YES' if status.integrity_ok else 'NO'}")
    if status.integrity_details:
        print(f"Details:         {status.integrity_details}")

    if status.applied_migrations:
        print("\nApplied Migrations:")
        print("-" * 60)
        for m in status.applied_migrations:
            status_icon = "[OK]" if m.success else "[FAIL]"
            print(f"  {status_icon} v{m.version:04d} - {m.name}")
            if m.description:
                print(f"       {m.description}")
            print(f"       Applied: {m.applied_at} ({m.duration_ms:.1f}ms)")

    if status.pending_migrations:
        print("\nPending Migrations:")
        print("-" * 60)
        for m in status.pending_migrations:
            print(f"  -> v{m.version:04d} - {m.name}")
            if m.description:
                print(f"       {m.description}")
    else:
        print("\nNo pending migrations.")

    print("=" * 60)


if __name__ == "__main__":
    main()
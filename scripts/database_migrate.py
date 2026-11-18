#!/usr/bin/env python3
"""
i20 AI Garage - Database Migration CLI

Runs database migrations with safety checks and backups.
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATABASE_PATH
from services.migrations import create_migration_runner


def main():
    parser = argparse.ArgumentParser(description="Run database migrations")
    parser.add_argument("--db", type=Path, default=DATABASE_PATH, help="Database path")
    parser.add_argument("--migrations-dir", type=Path, help="Migrations directory")
    parser.add_argument("--backup-dir", type=Path, help="Backup directory")
    parser.add_argument("--target", type=int, help="Target version (default: latest)")
    parser.add_argument("--no-backup", action="store_true", help="Skip backup creation (DANGEROUS)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would run without executing")
    parser.add_argument("--force", action="store_true", help="Skip some safety checks")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    # Configure logging
    import logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")

    runner = create_migration_runner(
        args.db,
        args.migrations_dir,
        args.backup_dir,
        dry_run=args.dry_run,
    )

    if args.dry_run:
        print("DRY RUN - No changes will be made")
        print("=" * 60)
        status = runner.dry_run()
        print(f"Current Version: {status.current_version}")
        print(f"Latest Version:  {status.latest_version}")
        if status.pending_migrations:
            print("\nPending Migrations:")
            for m in status.pending_migrations:
                print(f"  -> v{m.version:04d} - {m.name}")
                if m.description:
                    print(f"     {m.description}")
        else:
            print("No pending migrations.")
        return

    try:
        print(f"Running migrations on {args.db}")
        if args.target:
            print(f"Target version: {args.target}")
        if not args.no_backup:
            print("Backups will be created before each migration")
        else:
            print("WARNING: Backups DISABLED!")
        print("=" * 60)

        results = runner.migrate(
            target_version=args.target,
            create_backup=not args.no_backup,
            force=args.force,
        )

        if not results:
            print("No migrations to run - database is up to date")
            return

        # Print results
        all_success = True
        for result in results:
            if result.success:
                print(f"[OK] v{result.version:04d} ({result.name}) - {result.duration_ms:.1f}ms")
                if result.backup_path:
                    print(f"   Backup: {result.backup_path.name}")
            else:
                print(f"[FAIL] v{result.version:04d} ({result.name}) FAILED: {result.error_message}")
                if result.backup_path:
                    print(f"   Backup available: {result.backup_path}")
                all_success = False

        if all_success:
            print("=" * 60)
            print("All migrations completed successfully!")
        else:
            print("=" * 60)
            print("MIGRATION FAILED - See errors above")
            sys.exit(1)

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
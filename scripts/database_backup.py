#!/usr/bin/env python3
"""
i20 AI Garage - Database Backup CLI

Manages database backups: create, list, verify, restore.
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATABASE_PATH
from services.migrations import BackupManager, create_migration_runner


def cmd_create(args):
    """Create a new backup."""
    manager = BackupManager(args.db, args.backup_dir)
    print(f"Creating backup of {args.db}...")
    backup_path, metadata = manager.create_backup(
        prefix=args.prefix,
        description=args.description,
        verify=not args.no_verify,
    )

    if backup_path:
        print(f"[OK] Backup created: {backup_path}")
        if metadata:
            print(f"  Version: {metadata.source_version}")
            print(f"  Size: {metadata.size_bytes:,} bytes")
            print(f"  Verified: {'YES' if metadata.integrity_ok else 'NO'}")
            if metadata.row_counts:
                total = sum(metadata.row_counts.values())
                print(f"  Total rows: {total:,}")
        if metadata and not metadata.integrity_ok:
            sys.exit(1)
    else:
        print("[FAIL] Backup failed")
        sys.exit(1)


def cmd_list(args):
    """List all backups."""
    manager = BackupManager(args.db, args.backup_dir)
    backups = manager.list_backups()

    if not backups:
        print("No backups found")
        return

    print(f"Found {len(backups)} backup(s):")
    print("-" * 80)
    for b in backups:
        verified = "[OK]" if b.integrity_ok else "[FAIL]" if b.integrity_checked_at else "?"
        print(f"{verified} {b.backup_path.name}")
        print(f"    Created: {b.created_at}")
        print(f"    Version: {b.source_version}")
        print(f"    Size: {b.size_bytes:,} bytes")
        if b.description:
            print(f"    Description: {b.description}")
        if b.row_counts:
            total = sum(b.row_counts.values())
            print(f"    Rows: {total:,} across {len(b.row_counts)} tables")
        print()


def cmd_verify(args):
    """Verify a backup."""
    manager = BackupManager(args.db, args.backup_dir)

    if args.backup_file:
        backup_path = args.backup_file
        if not backup_path.is_absolute():
            backup_path = manager.backup_dir / backup_path
    else:
        # Verify latest
        backups = manager.list_backups()
        if not backups:
            print("No backups found")
            sys.exit(1)
        backup_path = backups[0].backup_path

    print(f"Verifying {backup_path}...")
    ok, details = manager.verify_backup(backup_path, args.db if args.compare else None)

    if ok:
        print(f"[OK] Verification PASSED: {details}")
    else:
        print(f"[FAIL] Verification FAILED: {details}")
        sys.exit(1)


def cmd_restore(args):
    """Restore database from backup."""
    manager = BackupManager(args.db, args.backup_dir)

    if args.backup_file:
        backup_path = args.backup_file
        if not backup_path.is_absolute():
            backup_path = manager.backup_dir / backup_path
    else:
        # Restore latest
        backups = manager.list_backups()
        if not backups:
            print("No backups found")
            sys.exit(1)
        backup_path = backups[0].backup_path

    print(f"Restoring from {backup_path}...")
    print(f"Target: {args.target or args.db}")

    if not args.force:
        confirm = input("This will OVERWRITE the target database. Continue? (yes/no): ")
        if confirm.lower() != "yes":
            print("Aborted")
            return

    success = manager.restore_backup(backup_path, args.target, verify_first=not args.no_verify)

    if success:
        print("[OK] Restore completed successfully")
    else:
        print("[FAIL] Restore failed")
        sys.exit(1)


def cmd_snapshot(args):
    """Capture schema snapshot."""
    manager = BackupManager(args.db, args.backup_dir)
    print("Capturing schema snapshot...")
    snapshot = manager.capture_schema_snapshot()

    print(f"Tables: {len(snapshot.tables)}")
    print(f"Indexes: {len(snapshot.indexes)}")
    print(f"Foreign Keys: {len(snapshot.foreign_keys)}")
    print(f"Triggers: {len(snapshot.triggers)}")
    print(f"Views: {len(snapshot.views)}")
    print(f"User Version: {snapshot.user_version}")
    print(f"Schema Hash: {snapshot.schema_hash}")

    if args.output:
        import json
        with open(args.output, "w") as f:
            json.dump({
                "tables": snapshot.tables,
                "indexes": snapshot.indexes,
                "foreign_keys": snapshot.foreign_keys,
                "triggers": snapshot.triggers,
                "views": snapshot.views,
                "user_version": snapshot.user_version,
                "schema_hash": snapshot.schema_hash,
            }, f, indent=2, default=str)
        print(f"Snapshot saved to {args.output}")


def cmd_compare(args):
    """Compare two databases."""
    manager = BackupManager(args.db, args.backup_dir)
    result = manager.compare_schemas(args.db1, args.db2)

    print(f"Database 1: {args.db1}")
    print(f"Database 2: {args.db2}")
    print(f"Identical: {result['identical']}")
    print(f"Hash 1: {result['hash1']}")
    print(f"Hash 2: {result['hash2']}")

    if result['tables_only_in_1']:
        print(f"\nTables only in DB1: {sorted(result['tables_only_in_1'])}")
    if result['tables_only_in_2']:
        print(f"Tables only in DB2: {sorted(result['tables_only_in_2'])}")
    if result['common_tables']:
        print(f"Common tables: {len(result['common_tables'])}")


def main():
    parser = argparse.ArgumentParser(description="Database backup management")
    parser.add_argument("--db", type=Path, default=DATABASE_PATH, help="Database path")
    parser.add_argument("--backup-dir", type=Path, help="Backup directory")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Create
    p_create = subparsers.add_parser("create", help="Create a new backup")
    p_create.add_argument("--prefix", default="manual", help="Filename prefix")
    p_create.add_argument("--description", default="", help="Description")
    p_create.add_argument("--no-verify", action="store_true", help="Skip verification")
    p_create.set_defaults(func=cmd_create)

    # List
    p_list = subparsers.add_parser("list", help="List all backups")
    p_list.set_defaults(func=cmd_list)

    # Verify
    p_verify = subparsers.add_parser("verify", help="Verify a backup")
    p_verify.add_argument("backup_file", nargs="?", type=Path, help="Backup file (default: latest)")
    p_verify.add_argument("--compare", action="store_true", help="Compare row counts with source")
    p_verify.set_defaults(func=cmd_verify)

    # Restore
    p_restore = subparsers.add_parser("restore", help="Restore from backup")
    p_restore.add_argument("backup_file", nargs="?", type=Path, help="Backup file (default: latest)")
    p_restore.add_argument("--target", type=Path, help="Target database (default: --db)")
    p_restore.add_argument("--force", action="store_true", help="Skip confirmation")
    p_restore.add_argument("--no-verify", action="store_true", help="Skip pre-restore verification")
    p_restore.set_defaults(func=cmd_restore)

    # Snapshot
    p_snapshot = subparsers.add_parser("snapshot", help="Capture schema snapshot")
    p_snapshot.add_argument("--output", type=Path, help="Save snapshot to JSON file")
    p_snapshot.set_defaults(func=cmd_snapshot)

    # Compare
    p_compare = subparsers.add_parser("compare", help="Compare two databases")
    p_compare.add_argument("db1", type=Path, help="First database")
    p_compare.add_argument("db2", type=Path, help="Second database")
    p_compare.set_defaults(func=cmd_compare)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
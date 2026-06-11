#!/usr/bin/env python3
"""Cleanup test pollution from chronocare production DB.

v0.6.0: removes the test-pollution Person and MedicalRecord rows that
accumulated before test isolation was added. Run this ONCE after deploying
the test isolation fix, then no longer needed.

Usage:
 uv run python scripts/cleanup_test_pollution.py [--dry-run]
"""
import argparse
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

POLLUTION_NAMES = ("测试报告人物", "深度验证人物", "测试人员")


def resolve_prod_db_path() -> Path:
    """Find the production DB file (live uvicorn uses this path).

    settings.base_dir has off-by-one bug in this repo (config.py uses 4
    .parent levels instead of 3). We replicate uvicorn behavior by resolving
    settings.database_url against cwd.
    """
    from chronocare.config import settings
    url = settings.database_url
    prefix = "sqlite+aiosqlite:///"
    if not url.startswith(prefix):
        raise RuntimeError(f"unexpected database_url scheme: {url}")
    rel = url[len(prefix):]
    return Path(rel).resolve()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="Show what would be deleted without making changes")
    args = ap.parse_args()

    db_path = resolve_prod_db_path()
    if not db_path.exists():
        print(f"Error: prod DB not found at {db_path}")
        return 1

    print(f"Production DB: {db_path}")
    print(f"Size: {db_path.stat().st_size} bytes")

    placeholders = ",".join(f"'{n}'" for n in POLLUTION_NAMES)

    find_pids_sql = (
        f"SELECT id, name FROM persons WHERE name IN ({placeholders}) ORDER BY id;"
    )
    proc = subprocess.run(
        ["sqlite3", str(db_path), find_pids_sql],
        capture_output=True, text=True, check=True,
    )
    person_lines = [ln for ln in proc.stdout.strip().split("\n") if ln]
    pids = []
    for ln in person_lines:
        parts = ln.split("|")
        if len(parts) >= 2:
            try:
                pids.append(int(parts[0]))
            except ValueError:
                pass

    if not pids:
        print("No pollution found. Nothing to clean up.")
        return 0

    pids_str = ",".join(str(i) for i in pids)
    find_mrs_sql = f"SELECT id FROM medical_records WHERE person_id IN ({pids_str});"
    proc = subprocess.run(
        ["sqlite3", str(db_path), find_mrs_sql],
        capture_output=True, text=True, check=True,
    )
    mr_lines = [ln for ln in proc.stdout.strip().split("\n") if ln]
    mr_ids = [int(ln.strip()) for ln in mr_lines if ln.strip().isdigit()]

    print(f"Found {len(pids)} test-pollution persons (id={pids[0]}..{pids[-1]})")
    print(f"Found {len(mr_ids)} test-pollution medical_records")

    if args.dry_run:
        print("DRY RUN — no changes made.")
        return 0

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    backup = backup_dir / f"chronocare-pre-cleanup-{ts}.db"
    shutil.copy2(db_path, backup)
    print(f"Backup saved to {backup}")

    mr_ids_str = ",".join(str(i) for i in mr_ids) if mr_ids else "0"
    delete_mrs_sql = f"DELETE FROM medical_records WHERE id IN ({mr_ids_str});"
    delete_persons_sql = f"DELETE FROM persons WHERE id IN ({pids_str});"

    subprocess.run(["sqlite3", str(db_path), delete_mrs_sql], check=True)
    subprocess.run(["sqlite3", str(db_path), delete_persons_sql], check=True)

    proc = subprocess.run(
        ["sqlite3", str(db_path), f"SELECT COUNT(*) FROM persons WHERE name IN ({placeholders});"],
        capture_output=True, text=True, check=True,
    )
    remaining = int(proc.stdout.strip() or "0")
    print(f"Deleted {len(mr_ids)} medical_records + {len(pids)} persons")
    print(f"Remaining pollution persons: {remaining}")
    if remaining != 0:
        print("WARNING: pollution remains. Investigate before re-running.")
        return 1
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

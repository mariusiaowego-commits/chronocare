"""Backup/Restore API endpoints."""

import asyncio
import json
import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from chronocare.config import settings

router = APIRouter(prefix="/api/backup", tags=["backup"])

_DB_PATH = settings.base_dir / "data" / "chronocare.db"
_BACKUP_DIR = settings.base_dir / "data" / "backups"


class BackupStatusResponse(BaseModel):
    last_backup_at: str | None = None
    backup_count: int = 0


class BackupResponse(BaseModel):
    ok: bool
    path: str
    created_at: str


class RestoreResponse(BaseModel):
    ok: bool
    restored_from: str


def _get_backup_files() -> list[Path]:
    _BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(_BACKUP_DIR.glob("chronocare_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)


@router.post("", response_model=BackupResponse, status_code=status.HTTP_201_CREATED)
async def create_backup() -> BackupResponse:
    """Create an online backup of the SQLite database."""
    if not _DB_PATH.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database file not found")

    _BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_name = f"chronocare_{timestamp}.db"
    backup_path = _BACKUP_DIR / backup_name

    # Online backup via sqlite3 backup API — runs in thread to avoid blocking
    def _do_backup() -> None:
        import sqlite3
        src = sqlite3.connect(str(_DB_PATH), timeout=30)
        dst = sqlite3.connect(str(backup_path))
        src.backup(dst)
        dst.close()
        src.close()

    await asyncio.to_thread(_do_backup)

    # Write metadata sidecar
    meta = {"created_at": datetime.utcnow().isoformat(), "original": str(_DB_PATH)}
    meta_path = backup_path.with_suffix(".db.meta.json")
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2))

    return BackupResponse(
        ok=True,
        path=str(backup_path),
        created_at=datetime.utcnow().isoformat(),
    )


@router.post("/restore", response_model=RestoreResponse)
async def restore_backup(filename: str) -> RestoreResponse:
    """Restore the database from a named backup file."""
    backup_path = _BACKUP_DIR / filename
    if not filename.endswith(".db"):
        filename += ".db"
        backup_path = _BACKUP_DIR / filename
    if not backup_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Backup not found: {filename}")

    # Verify it is a valid sqlite file
    def _verify() -> bool:
        import sqlite3
        try:
            conn = sqlite3.connect(str(backup_path))
            conn.execute("SELECT 1")
            conn.close()
            return True
        except Exception:
            return False

    if not await asyncio.to_thread(_verify):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid backup file")

    restore_path = _DB_PATH
    # Close any existing connections first (best-effort)
    # Copy backup over current db
    def _do_restore() -> None:
        shutil.copy2(str(backup_path), str(restore_path))

    await asyncio.to_thread(_do_restore)

    return RestoreResponse(ok=True, restored_from=filename)


@router.get("/status", response_model=BackupStatusResponse)
async def backup_status() -> BackupStatusResponse:
    """Return the last backup timestamp and total backup count."""
    files = _get_backup_files()
    if not files:
        return BackupStatusResponse(last_backup_at=None, backup_count=0)

    # Try to read metadata for precise timestamp
    latest = files[0]
    meta_path = latest.with_suffix(".db.meta.json")
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text())
            last_at = meta.get("created_at")
        except Exception:
            last_at = datetime.fromtimestamp(latest.stat().st_mtime).isoformat()
    else:
        last_at = datetime.fromtimestamp(latest.stat().st_mtime).isoformat()

    return BackupStatusResponse(last_backup_at=last_at, backup_count=len(files))

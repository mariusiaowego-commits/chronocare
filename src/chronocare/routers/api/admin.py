"""Backup & Restore API — SQLite database backup and restore."""

import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import FileResponse

from chronocare.config import settings

router = APIRouter(prefix="/api/admin", tags=["admin-api"])

# Resolve DB path from settings.database_url (sqlite+aiosqlite:///./data/chronocare.db)
_DB_PATH = Path(settings.database_url.replace("sqlite+aiosqlite:///", ""))
_BACKUP_DIR = Path("./data/backups")


@router.get("/backup/download")
async def download_backup():
    """Download current SQLite database as backup."""
    if not _DB_PATH.exists():
        return {"error": "Database file not found"}

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"chronocare_backup_{timestamp}.db"

    return FileResponse(
        path=str(_DB_PATH),
        filename=backup_name,
        media_type="application/x-sqlite3",
    )


@router.post("/backup/restore")
async def restore_backup(file: UploadFile = File(...)):
    """Restore database from uploaded backup file."""
    if not file.filename.endswith(".db"):
        return {"error": "Only .db files are accepted"}

    # Create backup of current DB before restore
    if _DB_PATH.exists():
        _BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        pre_restore_backup = _BACKUP_DIR / f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(_DB_PATH, pre_restore_backup)

    # Save uploaded file as new DB
    contents = await file.read()
    _DB_PATH.write_bytes(contents)

    return {
        "message": "Database restored successfully",
        "restored_from": file.filename,
        "pre_restore_backup": str(pre_restore_backup) if _DB_PATH.exists() else None,
    }


@router.get("/backup/list")
async def list_backups():
    """List available backup files."""
    if not _BACKUP_DIR.exists():
        return {"backups": []}

    backups = []
    for f in sorted(_BACKUP_DIR.glob("*.db"), reverse=True):
        stat = f.stat()
        backups.append({
            "filename": f.name,
            "size_kb": round(stat.st_size / 1024, 1),
            "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })

    return {"backups": backups}

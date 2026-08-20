"""Original-file preview helpers — images as-is, PDF first-page thumbnails."""

from __future__ import annotations

import asyncio
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

IMAGE_EXTS = frozenset({".png", ".jpg", ".jpeg", ".webp", ".gif", ".heic"})
PDF_EXTS = frozenset({".pdf"})

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
THUMBNAIL_DIR = _PROJECT_ROOT / "uploads" / "thumbnails"

_ALLOWED_ROOTS = (
    (_PROJECT_ROOT / "uploads").resolve(),
    (_PROJECT_ROOT / "data").resolve(),
)


def project_root() -> Path:
    return _PROJECT_ROOT


def resolve_record_file(image_path: str | None) -> Path | None:
    """Resolve a stored image_path against the project root, with traversal guard."""
    if not image_path:
        return None
    raw = Path(image_path)
    path = raw if raw.is_absolute() else (_PROJECT_ROOT / raw)
    try:
        resolved = path.resolve()
    except OSError:
        return None
    if not any(_is_relative_to(resolved, root) for root in _ALLOWED_ROOTS):
        return None
    return resolved if resolved.is_file() else None


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def is_pdf_path(path: Path | str | None) -> bool:
    if path is None:
        return False
    return Path(path).suffix.lower() in PDF_EXTS


def is_image_path(path: Path | str | None) -> bool:
    if path is None:
        return False
    return Path(path).suffix.lower() in IMAGE_EXTS


def thumbnail_file(record_id: int) -> Path:
    return THUMBNAIL_DIR / f"{record_id}.png"


@dataclass(frozen=True)
class PreviewInfo:
    exists: bool
    is_pdf: bool
    is_image: bool
    preview_url: str | None
    file_url: str | None
    filename: str
    missing_path: str | None


def preview_info(record_id: int, image_path: str | None) -> PreviewInfo:
    filename = Path(image_path).name if image_path else ""
    source = resolve_record_file(image_path)
    if source is None:
        return PreviewInfo(
            exists=False,
            is_pdf=is_pdf_path(image_path),
            is_image=is_image_path(image_path),
            preview_url=None,
            file_url=None,
            filename=filename,
            missing_path=image_path,
        )
    return PreviewInfo(
        exists=True,
        is_pdf=is_pdf_path(source),
        is_image=is_image_path(source),
        preview_url=f"/medical-records/{record_id}/preview",
        file_url=f"/medical-records/{record_id}/file",
        filename=source.name,
        missing_path=None,
    )


def _run_pdftoppm(source: Path, dest: Path) -> None:
    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        raise RuntimeError("pdftoppm 未安装（需要 poppler）")
    dest.parent.mkdir(parents=True, exist_ok=True)
    prefix = dest.with_suffix("")
    subprocess.run(
        [
            pdftoppm,
            "-png",
            "-f",
            "1",
            "-l",
            "1",
            "-singlefile",
            "-r",
            "120",
            str(source),
            str(prefix),
        ],
        check=True,
        timeout=30,
        capture_output=True,
    )
    if not dest.is_file():
        raise RuntimeError(f"pdftoppm 未生成缩略图: {dest}")


async def ensure_thumbnail(record_id: int, source: Path) -> Path:
    """Return a PNG path for preview. Images are returned as-is; PDFs are rasterized."""
    if is_image_path(source):
        return source
    if not is_pdf_path(source):
        raise RuntimeError(f"不支持的预览格式: {source.suffix}")
    dest = thumbnail_file(record_id)
    if dest.is_file() and dest.stat().st_mtime >= source.stat().st_mtime:
        return dest
    await asyncio.to_thread(_run_pdftoppm, source, dest)
    return dest


def media_type_for(path: Path) -> str:
    ext = path.suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".pdf": "application/pdf",
    }.get(ext, "application/octet-stream")

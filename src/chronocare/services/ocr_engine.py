"""OCR engine wrapper using macOS Vision Framework via Swift subprocess."""

import asyncio
import shutil
from pathlib import Path

# Base directory for the chronocare project (worktree)
SCRIPT_DIR = Path(__file__).parent.parent.parent.parent / "scripts"
SWIFT_SCRIPT = SCRIPT_DIR / "vision_ocr.swift"

# Timeout for Swift OCR subprocess (seconds)
_OCR_TIMEOUT_SECONDS = 30


async def is_ocr_available() -> bool:
    """Check if Swift runtime and Vision OCR are available on this system.

    Returns True if:
    - Swift is installed and executable
    - The vision_ocr.swift script exists
    - Swift can be invoked without immediate error

    Returns False otherwise.
    """
    # Check Swift exists
    swift_path = shutil.which("swift")
    if not swift_path:
        return False

    # Check script exists
    if not SWIFT_SCRIPT.exists():
        return False

    # Quick sanity-check: try launching swift with --version (no image arg)
    # We pass a non-existent file path just to verify swift starts without crashing
    # The script itself will emit "file not found" to stderr, but exit 1 vs crash
    try:
        proc = await asyncio.create_subprocess_exec(
            "swift",
            str(SWIFT_SCRIPT),
            "/nonexistent_path_placeholder",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        # We expect it to exit 1 with "file not found" — that's fine
        await asyncio.wait_for(proc.communicate(), timeout=10)
        return True
    except (OSError, TimeoutError):
        return False


async def extract_text(image_path: str) -> str:
    """Extract text from an image using the macOS Vision Framework Swift script.

    Args:
        image_path: Absolute path to the image file (PNG, JPG, HEIC, etc.)

    Returns:
        Recognized text as a plain string. Empty string if no text found.

    Raises:
        FileNotFoundError: The image file does not exist.
        RuntimeError: Swift OCR is not available on this system.
        asyncio.TimeoutError: OCR took longer than 30 seconds.
    """
    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    # Verify Swift + script are available
    if not await is_ocr_available():
        raise RuntimeError(
            "Swift OCR is not available. "
            "Ensure Swift is installed and scripts/vision_ocr.swift exists."
        )

    try:
        proc = await asyncio.create_subprocess_exec(
            "swift",
            str(SWIFT_SCRIPT),
            str(path.absolute()),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(), timeout=_OCR_TIMEOUT_SECONDS
        )

        if proc.returncode != 0:
            stderr_text = stderr_bytes.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"Swift OCR failed: {stderr_text}")

        text = stdout_bytes.decode("utf-8", errors="replace")
        return text.strip()

    except TimeoutError:
        raise TimeoutError(
            f"Swift OCR timed out after {_OCR_TIMEOUT_SECONDS} seconds for: {image_path}"
        ) from None

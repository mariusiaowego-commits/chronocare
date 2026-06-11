"""API routes for health report generation."""

from __future__ import annotations

import asyncio
import re
import shutil

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.schemas.report_generation import (
    ReportGenerateRequest,
    ReportGenerationBrief,
    ReportGenerationRead,
)
from chronocare.services import report_generation as svc

router = APIRouter(prefix="/api", tags=["reports"])


# --- Preflight (must be before /reports/{report_id} to avoid route conflict) ---

@router.get("/reports/preflight")
async def report_preflight():
    """Pre-flight check: verify hermes CLI and image generation readiness.

    Checks two layers:
    1. Tool Gateway: is FAL image generation available via Nous Portal?
    2. Chat model: can hermes chat actually respond? (lightweight test)
    """
    result = {
        "hermes_available": False,
        "portal_logged_in": False,
        "fal_image_gen": False,
        "chat_model_working": False,
        "chat_provider": None,
        "chat_model": None,
        "tool_gateway": None,
        "errors": [],
    }

    # 1. Check hermes binary
    hermes_bin = shutil.which("hermes")
    if not hermes_bin:
        result["errors"].append("hermes CLI not found in PATH")
        return result
    result["hermes_available"] = True

    # 2. Check portal tools — is FAL image generation available?
    try:
        proc = await asyncio.create_subprocess_exec(
            "hermes", "portal", "tools",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
        tools_text = stdout.decode()

        # Check FAL image gen
        for line in tools_text.splitlines():
            if "Image generation" in line:
                if "✓" in line and "FAL" in line:
                    result["fal_image_gen"] = True
                    result["tool_gateway"] = "FAL via Nous Portal"
                break

        # Check portal login from tools output
        if "via Nous Portal" in tools_text:
            result["portal_logged_in"] = True

    except (TimeoutError, FileNotFoundError) as e:
        result["errors"].append(f"hermes portal tools check failed: {e}")

    # 3. Verify chat model actually works (lightweight test)
    #    This catches auth failures (401) before the user tries to generate
    try:
        proc = await asyncio.create_subprocess_exec(
            "hermes", "chat", "-q", "Reply with exactly: OK", "-Q",
            "--max-turns", "1",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        chat_output = stdout.decode()
        chat_stderr = stderr.decode()

        # Check for auth errors
        if "401" in chat_stderr or "authentication" in chat_stderr.lower():
            # Extract provider/model from error
            provider_match = re.search(r"Provider:\s+(\S+)", chat_stderr)
            model_match = re.search(r"Model:\s+(\S+)", chat_stderr)
            if provider_match:
                result["chat_provider"] = provider_match.group(1)
            if model_match:
                result["chat_model"] = model_match.group(1)
            result["errors"].append(f"Chat model auth failed: {chat_stderr[:200]}")
        elif proc.returncode == 0 and "OK" in chat_output:
            result["chat_model_working"] = True
            # Try to extract what model was used from stderr
            # hermes logs the model used in stderr
            model_match = re.search(r"Model:\s+(\S+)", chat_stderr)
            provider_match = re.search(r"Provider:\s+(\S+)", chat_stderr)
            if model_match:
                result["chat_model"] = model_match.group(1)
            if provider_match:
                result["chat_provider"] = provider_match.group(1)
        else:
            result["errors"].append(f"Chat test unexpected output: {chat_output[:200]}")

    except TimeoutError:
        result["errors"].append("Chat model test timed out (30s)")
    except FileNotFoundError:
        result["errors"].append("hermes chat command not found")

    # 4. Fallback: get config info if chat test didn't reveal model
    if not result["chat_provider"]:
        try:
            proc = await asyncio.create_subprocess_exec(
                "hermes", "status",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
            status_text = stdout.decode()

            model_match = re.search(r"Model:\s+(.+)", status_text)
            provider_match = re.search(r"Provider:\s+(.+)", status_text)
            if model_match and not result["chat_model"]:
                result["chat_model"] = model_match.group(1).strip()
            if provider_match and not result["chat_provider"]:
                result["chat_provider"] = provider_match.group(1).strip()

        except (TimeoutError, FileNotFoundError):
            pass

    return result


# --- Generate ---

@router.post(
    "/persons/{person_id}/reports/generate",
    response_model=ReportGenerationRead,
    status_code=202,
)
async def generate_report(
    person_id: int,
    body: ReportGenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Trigger async report generation. Returns the pending record."""
    from chronocare.services.report_data import aggregate_person_data

    # Validate person exists
    try:
        await aggregate_person_data(db, person_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=f"Person {person_id} not found") from exc

    # Create pending record
    report = await svc.create_report_record(db, person_id, body.layout)

    # Run generation in background
    background_tasks.add_task(_run_generation, report.id)

    return report


async def _run_generation(report_id: int):
    """Background task: generate report image."""
    from chronocare.database import async_session_factory

    async with async_session_factory() as db:
        try:
            await svc.generate_report(db, report_id)
        except Exception:
            pass  # status already updated to 'failed' in generate_report


# --- Status & History ---

@router.get("/reports/{report_id}", response_model=ReportGenerationRead)
async def get_report_status(
    report_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get report generation status and result."""
    report = await svc.get_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get(
    "/persons/{person_id}/reports",
    response_model=list[ReportGenerationBrief],
)
async def list_person_reports(
    person_id: int,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """List report generation history for a person."""
    return await svc.list_person_reports(db, person_id, limit=limit)

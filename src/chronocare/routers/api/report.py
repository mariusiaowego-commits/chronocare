"""API routes for health report generation."""

from __future__ import annotations

import asyncio
import json
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

    Returns environment info so the frontend can show the user what
    provider/model will be used before triggering generation.
    """
    result = {
        "hermes_available": False,
        "portal_logged_in": False,
        "image_gen_available": False,
        "provider": None,
        "model": None,
        "errors": [],
    }

    # 1. Check hermes binary
    hermes_bin = shutil.which("hermes")
    if not hermes_bin:
        result["errors"].append("hermes CLI not found in PATH")
        return result
    result["hermes_available"] = True

    # 2. Run `hermes status` to get provider/model + portal info
    try:
        proc = await asyncio.create_subprocess_exec(
            "hermes", "status",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=15)
        status_text = stdout.decode()

        # Extract model and provider
        model_match = re.search(r"Model:\s+(.+)", status_text)
        provider_match = re.search(r"Provider:\s+(.+)", status_text)
        if model_match:
            result["model"] = model_match.group(1).strip()
        if provider_match:
            result["provider"] = provider_match.group(1).strip()

        # Check portal login
        if "Nous Portal" in status_text and "✓ logged in" in status_text:
            result["portal_logged_in"] = True

        # Check image generation availability
        if "Image generation" in status_text and "✓ active" in status_text:
            result["image_gen_available"] = True

    except (asyncio.TimeoutError, FileNotFoundError) as e:
        result["errors"].append(f"hermes status check failed: {e}")

    # 3. Run `hermes portal info` for more detail
    try:
        proc = await asyncio.create_subprocess_exec(
            "hermes", "portal", "info",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
        portal_text = stdout.decode()

        # Check image gen routing
        if "Image generation" in portal_text:
            img_line = [
                l for l in portal_text.splitlines()
                if "Image generation" in l
            ]
            if img_line:
                img_info = img_line[0].strip()
                if "via Nous Portal" in img_info:
                    result["image_gen_available"] = True
                elif "not configured" in img_info:
                    result["image_gen_available"] = False
                    result["errors"].append("Image generation not configured in Tool Gateway")

    except (asyncio.TimeoutError, FileNotFoundError) as e:
        result["errors"].append(f"hermes portal info check failed: {e}")

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

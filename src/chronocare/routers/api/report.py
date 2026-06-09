"""API routes for health report generation."""

from __future__ import annotations

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
            await svc.generate_report(db, report_id, _mock_image_generate)
        except Exception:
            pass  # status already updated to 'failed' in generate_report


def _mock_image_generate(prompt: str, aspect_ratio: str = "portrait") -> str:
    """Placeholder image generator — returns a placeholder path.

    Will be replaced with actual image_generate call when integrated.
    """
    return f"/static/placeholders/report_{aspect_ratio}.png"


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

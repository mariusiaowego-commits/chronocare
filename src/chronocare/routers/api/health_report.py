"""Health Report API — weekly/monthly report generation."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.services.health_report import generate_monthly_report, generate_weekly_report

router = APIRouter(prefix="/api/health-report", tags=["health-report-api"])


@router.get("/weekly")
async def get_weekly_report(
    person_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Generate weekly health report."""
    return await generate_weekly_report(person_id, db)


@router.get("/monthly")
async def get_monthly_report(
    person_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Generate monthly health report."""
    return await generate_monthly_report(person_id, db)

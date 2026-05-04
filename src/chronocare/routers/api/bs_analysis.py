"""Blood Sugar Variability API — advanced analysis endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.services.bs_variability import analyze_blood_sugar_by_time, analyze_blood_sugar_variability

router = APIRouter(prefix="/api/bs-analysis", tags=["bs-analysis-api"])


@router.get("/variability")
async def get_variability(
    person_id: int,
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get blood sugar variability analysis."""
    return await analyze_blood_sugar_variability(person_id, days, db)


@router.get("/time-patterns")
async def get_time_patterns(
    person_id: int,
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get blood sugar patterns by time of day."""
    return await analyze_blood_sugar_by_time(person_id, days, db)

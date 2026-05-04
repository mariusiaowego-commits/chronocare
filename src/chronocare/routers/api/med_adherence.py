"""Medication Adherence API."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.services.medication_adherence import analyze_medication_adherence

router = APIRouter(prefix="/api/med-adherence", tags=["med-adherence-api"])


@router.get("/analysis")
async def get_adherence_analysis(
    person_id: int,
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get medication adherence analysis."""
    return await analyze_medication_adherence(person_id, days, db)

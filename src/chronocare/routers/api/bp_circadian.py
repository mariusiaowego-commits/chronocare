"""BP Circadian Analysis API."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.services.bp_circadian import analyze_bp_circadian

router = APIRouter(prefix="/api/bp-circadian", tags=["bp-circadian-api"])


@router.get("/analysis")
async def get_circadian_analysis(
    person_id: int,
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get BP circadian rhythm analysis."""
    return await analyze_bp_circadian(person_id, days, db)

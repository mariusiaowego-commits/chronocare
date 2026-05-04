"""Trend Alert API — detect abnormal health patterns."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.services.trend_alert import get_all_alerts

router = APIRouter(prefix="/api/alerts", tags=["alerts-api"])


@router.get("/trend")
async def get_trend_alerts(
    person_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all trend alerts for a person."""
    return await get_all_alerts(person_id, db)

"""Health Profile API — comprehensive health overview."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.services.health_profile import get_health_overview

router = APIRouter(prefix="/api/health-profile", tags=["health-profile-api"])


@router.get("/overview")
async def health_overview(
    person_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive health overview for a person."""
    overview = await get_health_overview(db, person_id)
    return overview

"""Lab metric query API."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.services.lab_query import result_to_dict, run_lab_query

router = APIRouter(prefix="/api/lab-query", tags=["Lab Query"])


@router.get("")
async def api_lab_query(
    q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    result = await run_lab_query(db, q)
    return result_to_dict(result)

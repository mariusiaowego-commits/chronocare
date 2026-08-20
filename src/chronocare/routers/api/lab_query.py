"""Lab metric query API."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.services.lab_query import result_to_dict, run_lab_query, suggest_lab_queries

router = APIRouter(prefix="/api/lab-query", tags=["Lab Query"])


@router.get("/suggest")
async def api_lab_suggest(
    q: str = Query(""),
    person_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    items = await suggest_lab_queries(db, q, person_id=person_id)
    return {"items": items}


@router.get("")
async def api_lab_query(
    q: str = Query(..., min_length=1),
    person_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    result = await run_lab_query(db, q, person_id=person_id)
    return result_to_dict(result)

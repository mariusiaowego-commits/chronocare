"""Visit REST API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.schemas.visit import VisitCreate, VisitRead, VisitUpdate
from chronocare.services.visit import create_visit, delete_visit, get_visit, list_visits, update_visit

router = APIRouter(prefix="/api/visits", tags=["visits"])


@router.get("", response_model=list[VisitRead])
async def api_list(person_id: int | None = Query(None), db: AsyncSession = Depends(get_db)):
    return await list_visits(db, person_id)


@router.get("/{visit_id}", response_model=VisitRead)
async def api_get(visit_id: int, db: AsyncSession = Depends(get_db)):
    visit = await get_visit(db, visit_id)
    if visit is None:
        raise HTTPException(404, "Visit not found")
    return visit


@router.post("", response_model=VisitRead, status_code=201)
async def api_create(data: VisitCreate, db: AsyncSession = Depends(get_db)):
    return await create_visit(db, data)


@router.patch("/{visit_id}", response_model=VisitRead)
async def api_update(visit_id: int, data: VisitUpdate, db: AsyncSession = Depends(get_db)):
    visit = await update_visit(db, visit_id, data)
    if visit is None:
        raise HTTPException(404, "Visit not found")
    return visit


@router.delete("/{visit_id}", status_code=204)
async def api_delete(visit_id: int, db: AsyncSession = Depends(get_db)):
    if not await delete_visit(db, visit_id):
        raise HTTPException(404, "Visit not found")

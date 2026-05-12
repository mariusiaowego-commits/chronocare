"""Person REST API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.schemas.person import ConditionCreate, ConditionRead, PersonCreate, PersonRead, PersonUpdate
from chronocare.services.person import (
    add_condition,
    create_person,
    delete_condition,
    delete_person,
    get_person,
    list_conditions,
    list_persons,
    update_person,
)

router = APIRouter(prefix="/api/persons", tags=["persons"])

_SORT_COLS = frozenset(["id", "name", "created_at"])


@router.get("", response_model=list[PersonRead])
async def api_list_persons(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    sort_by: str | None = Query(None, description=f"Sort field. Options: {', '.join(sorted(_SORT_COLS))}"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort direction: asc or desc"),
    db: AsyncSession = Depends(get_db),
):
    rows = await list_persons(db)
    if sort_by and sort_by in _SORT_COLS:
        reverse = sort_order == "desc"
        rows = sorted(rows, key=lambda r: getattr(r, sort_by), reverse=reverse)
    return rows[skip : skip + limit]


@router.get("/{person_id}", response_model=PersonRead)
async def api_get_person(person_id: int, db: AsyncSession = Depends(get_db)):
    person = await get_person(db, person_id)
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


@router.post("", response_model=PersonRead, status_code=201)
async def api_create_person(data: PersonCreate, db: AsyncSession = Depends(get_db)):
    return await create_person(db, data)


@router.patch("/{person_id}", response_model=PersonRead)
async def api_update_person(person_id: int, data: PersonUpdate, db: AsyncSession = Depends(get_db)):
    person = await update_person(db, person_id, data)
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


@router.delete("/{person_id}", status_code=204)
async def api_delete_person(person_id: int, db: AsyncSession = Depends(get_db)):
    if not await delete_person(db, person_id):
        raise HTTPException(status_code=404, detail="Person not found")


# --- Conditions sub-resource ---

_SORT_COLS_COND = frozenset(["id", "name", "diagnosed_date", "severity", "status"])


@router.get("/{person_id}/conditions", response_model=list[ConditionRead])
async def api_list_conditions(
    person_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sort_by: str | None = Query(None),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    rows = await list_conditions(db, person_id)
    if sort_by and sort_by in _SORT_COLS_COND:
        reverse = sort_order == "desc"
        rows = sorted(rows, key=lambda r: getattr(r, sort_by) or "", reverse=reverse)
    return rows[skip : skip + limit]


@router.post("/{person_id}/conditions", response_model=ConditionRead, status_code=201)
async def api_add_condition(person_id: int, data: ConditionCreate, db: AsyncSession = Depends(get_db)):
    condition = await add_condition(db, person_id, data)
    if condition is None:
        raise HTTPException(status_code=404, detail="Person not found")
    return condition


@router.delete("/conditions/{condition_id}", status_code=204)
async def api_delete_condition(condition_id: int, db: AsyncSession = Depends(get_db)):
    if not await delete_condition(db, condition_id):
        raise HTTPException(status_code=404, detail="Condition not found")

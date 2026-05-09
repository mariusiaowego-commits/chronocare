"""Blood sugar REST API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.schemas.blood_sugar import BloodSugarCreate, BloodSugarRead, BloodSugarUpdate
from chronocare.services.blood_sugar import (
    create_blood_sugar,
    delete_blood_sugar,
    get_blood_sugar,
    list_blood_sugar,
    update_blood_sugar,
)

router = APIRouter(prefix="/api/blood-sugar", tags=["blood-sugar"])


@router.get("", response_model=list[BloodSugarRead])
async def api_list(person_id: int | None = Query(None), db: AsyncSession = Depends(get_db)):
    return await list_blood_sugar(db, person_id)


@router.get("/{record_id}", response_model=BloodSugarRead)
async def api_get(record_id: int, db: AsyncSession = Depends(get_db)):
    record = await get_blood_sugar(db, record_id)
    if record is None:
        raise HTTPException(404, "Record not found")
    return record


@router.post("", response_model=BloodSugarRead, status_code=201)
async def api_create(data: BloodSugarCreate, db: AsyncSession = Depends(get_db)):
    return await create_blood_sugar(db, data)


@router.patch("/{record_id}", response_model=BloodSugarRead)
async def api_update(record_id: int, data: BloodSugarUpdate, db: AsyncSession = Depends(get_db)):
    record = await update_blood_sugar(db, record_id, data)
    if record is None:
        raise HTTPException(404, "Record not found")
    return record


@router.delete("/{record_id}", status_code=204)
async def api_delete(record_id: int, db: AsyncSession = Depends(get_db)):
    if not await delete_blood_sugar(db, record_id):
        raise HTTPException(404, "Record not found")

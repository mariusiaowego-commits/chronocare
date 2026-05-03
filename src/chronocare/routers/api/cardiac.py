"""Cardiac REST API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.schemas.cardiac import BloodPressureCreate, BloodPressureRead, BloodPressureUpdate
from chronocare.services.cardiac import create_bp, delete_bp, get_bp, list_bp, update_bp

router = APIRouter(prefix="/api/cardiac", tags=["cardiac"])


@router.get("/bp", response_model=list[BloodPressureRead])
async def api_list_bp(person_id: int | None = Query(None), db: AsyncSession = Depends(get_db)):
    return await list_bp(db, person_id)


@router.get("/bp/{record_id}", response_model=BloodPressureRead)
async def api_get_bp(record_id: int, db: AsyncSession = Depends(get_db)):
    record = await get_bp(db, record_id)
    if record is None:
        raise HTTPException(404, "Record not found")
    return record


@router.post("/bp", response_model=BloodPressureRead, status_code=201)
async def api_create_bp(data: BloodPressureCreate, db: AsyncSession = Depends(get_db)):
    return await create_bp(db, data)


@router.patch("/bp/{record_id}", response_model=BloodPressureRead)
async def api_update_bp(record_id: int, data: BloodPressureUpdate, db: AsyncSession = Depends(get_db)):
    record = await update_bp(db, record_id, data)
    if record is None:
        raise HTTPException(404, "Record not found")
    return record


@router.delete("/bp/{record_id}", status_code=204)
async def api_delete_bp(record_id: int, db: AsyncSession = Depends(get_db)):
    if not await delete_bp(db, record_id):
        raise HTTPException(404, "Record not found")

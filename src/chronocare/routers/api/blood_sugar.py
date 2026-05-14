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

_SORT_COLS = frozenset(["id", "measured_at", "value", "meal_context"])


@router.get("", response_model=list[BloodSugarRead])
async def api_list(
    person_id: int | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sort_by: str | None = Query(None),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    rows = await list_blood_sugar(db, person_id)
    if sort_by and sort_by in _SORT_COLS:
        reverse = sort_order == "desc"
        rows = sorted(rows, key=lambda r: getattr(r, sort_by) or "", reverse=reverse)
    return rows[skip : skip + limit]


@router.get("/{record_id}", response_model=BloodSugarRead)
async def api_get(record_id: int, db: AsyncSession = Depends(get_db)):
    record = await get_blood_sugar(db, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.post("", response_model=BloodSugarRead, status_code=201)
async def api_create(data: BloodSugarCreate, db: AsyncSession = Depends(get_db)):
    return await create_blood_sugar(db, data)


@router.patch("/{record_id}", response_model=BloodSugarRead)
async def api_update(record_id: int, data: BloodSugarUpdate, db: AsyncSession = Depends(get_db)):
    record = await update_blood_sugar(db, record_id, data)
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.delete("/{record_id}", status_code=204)
async def api_delete(record_id: int, db: AsyncSession = Depends(get_db)):
    if not await delete_blood_sugar(db, record_id):
        raise HTTPException(status_code=404, detail="Record not found")


@router.get("/trend/{person_id}", response_model=dict)
async def api_trend(
    person_id: int,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """获取血糖趋势分析"""
    from chronocare.services.blood_sugar import get_blood_sugar_trend
    return await get_blood_sugar_trend(db, person_id, days)


@router.get("/chart-data/{person_id}", response_model=dict)
async def api_chart_data(
    person_id: int,
    days: int = Query(14, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """获取血糖趋势图表数据"""
    from chronocare.services.blood_sugar import get_blood_sugar_chart_data
    return await get_blood_sugar_chart_data(db, person_id, days)

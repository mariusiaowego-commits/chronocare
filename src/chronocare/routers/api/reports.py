"""Reports API — statistics and export endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.models.blood_sugar import BloodSugarRecord
from chronocare.models.cardiac import BloodPressureRecord
from chronocare.models.person import Person

import csv
import io

router = APIRouter(prefix="/api/reports", tags=["reports-api"])


@router.get("/blood-sugar-trend")
async def blood_sugar_trend(
    person_id: int,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Return blood sugar trend data for Chart.js."""
    from datetime import timedelta

    cutoff = datetime.now() - timedelta(days=days)
    stmt = (
        select(BloodSugarRecord)
        .where(BloodSugarRecord.person_id == person_id)
        .where(BloodSugarRecord.measured_at >= cutoff)
        .order_by(BloodSugarRecord.measured_at.asc())
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    return {
        "labels": [r.measured_at.strftime("%m-%d %H:%M") for r in records],
        "values": [r.value for r in records],
        "contexts": [r.meal_context or "random" for r in records],
        "alerts": [r.is_alert for r in records],
    }


@router.get("/blood-sugar-stats")
async def blood_sugar_stats(
    person_id: int,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Blood sugar summary statistics."""
    from datetime import timedelta

    cutoff = datetime.now() - timedelta(days=days)
    stmt = (
        select(
            func.count(BloodSugarRecord.id).label("count"),
            func.avg(BloodSugarRecord.value).label("avg"),
            func.min(BloodSugarRecord.value).label("min"),
            func.max(BloodSugarRecord.value).label("max"),
            func.sum(func.cast(BloodSugarRecord.is_alert, int)).label("alert_count"),
        )
        .where(BloodSugarRecord.person_id == person_id)
        .where(BloodSugarRecord.measured_at >= cutoff)
    )
    result = await db.execute(stmt)
    row = result.one()

    return {
        "count": row.count or 0,
        "avg": round(float(row.avg), 1) if row.avg else None,
        "min": round(float(row.min), 1) if row.min else None,
        "max": round(float(row.max), 1) if row.max else None,
        "alert_count": row.alert_count or 0,
    }


@router.get("/bp-trend")
async def bp_trend(
    person_id: int,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Blood pressure trend data for Chart.js."""
    from datetime import timedelta

    cutoff = datetime.now() - timedelta(days=days)
    stmt = (
        select(BloodPressureRecord)
        .where(BloodPressureRecord.person_id == person_id)
        .where(BloodPressureRecord.measured_at >= cutoff)
        .order_by(BloodPressureRecord.measured_at.asc())
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    return {
        "labels": [r.measured_at.strftime("%m-%d %H:%M") for r in records],
        "systolic": [r.systolic for r in records],
        "diastolic": [r.diastolic for r in records],
        "heart_rate": [r.heart_rate for r in records],
    }


@router.get("/export/blood-sugar")
async def export_blood_sugar(
    person_id: int,
    format: str = Query("csv", pattern="^(csv)$"),
    db: AsyncSession = Depends(get_db),
):
    """Export blood sugar records as CSV."""
    stmt = (
        select(BloodSugarRecord)
        .where(BloodSugarRecord.person_id == person_id)
        .order_by(BloodSugarRecord.measured_at.desc())
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["日期时间", "血糖值(mmol/L)", "测量时机", "预警", "备注"])
    for r in records:
        writer.writerow([
            r.measured_at.strftime("%Y-%m-%d %H:%M"),
            r.value,
            r.meal_context or "",
            "是" if r.is_alert else "否",
            r.notes or "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=blood_sugar_{person_id}.csv"},
    )


@router.get("/export/health-report")
async def export_health_report(
    person_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Export comprehensive health report as CSV."""
    # Get person info
    person = await db.get(Person, person_id)
    if not person:
        return {"error": "Person not found"}

    # Get blood sugar records
    bs_stmt = (
        select(BloodSugarRecord)
        .where(BloodSugarRecord.person_id == person_id)
        .order_by(BloodSugarRecord.measured_at.desc())
    )
    bs_result = await db.execute(bs_stmt)
    bs_records = bs_result.scalars().all()

    # Get BP records
    bp_stmt = (
        select(BloodPressureRecord)
        .where(BloodPressureRecord.person_id == person_id)
        .order_by(BloodPressureRecord.measured_at.desc())
    )
    bp_result = await db.execute(bp_stmt)
    bp_records = bp_result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Person info
    writer.writerow(["=== 个人健康报告 ==="])
    writer.writerow(["姓名", person.name])
    writer.writerow(["出生日期", person.birth_date or ""])
    writer.writerow(["身高(cm)", person.height_cm or ""])
    writer.writerow(["体重(kg)", person.weight_kg or ""])
    writer.writerow(["血型", person.blood_type or ""])
    writer.writerow([])

    # Blood sugar summary
    writer.writerow(["=== 血糖记录 ==="])
    writer.writerow(["日期时间", "血糖值(mmol/L)", "测量时机", "预警", "备注"])
    for r in bs_records:
        writer.writerow([
            r.measured_at.strftime("%Y-%m-%d %H:%M"),
            r.value,
            r.meal_context or "",
            "是" if r.is_alert else "否",
            r.notes or "",
        ])
    writer.writerow([])

    # BP summary
    writer.writerow(["=== 血压记录 ==="])
    writer.writerow(["日期时间", "收缩压", "舒张压", "心率", "预警", "备注"])
    for r in bp_records:
        writer.writerow([
            r.measured_at.strftime("%Y-%m-%d %H:%M"),
            r.systolic,
            r.diastolic,
            r.heart_rate or "",
            "是" if r.is_alert else "否",
            r.notes or "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=health_report_{person.name}.csv"},
    )

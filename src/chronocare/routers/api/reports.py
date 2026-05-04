"""Reports API — statistics and export endpoints."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import case, func, select
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


@router.get("/blood-sugar-distribution")
async def blood_sugar_distribution(
    person_id: int,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Blood sugar value distribution for pie/doughnut chart."""
    cutoff = datetime.now() - timedelta(days=days)
    stmt = (
        select(
            func.sum(case((BloodSugarRecord.value < 3.9, 1), else_=0)).label("low"),
            func.sum(case(
                (BloodSugarRecord.value >= 3.9, 1),
                (BloodSugarRecord.value < 6.1, 1),
                else_=0
            )).label("normal"),
            func.sum(case(
                (BloodSugarRecord.value >= 6.1, 1),
                (BloodSugarRecord.value < 7.8, 1),
                else_=0
            )).label("elevated"),
            func.sum(case(
                (BloodSugarRecord.value >= 7.8, 1),
                (BloodSugarRecord.value < 11.1, 1),
                else_=0
            )).label("high"),
            func.sum(case((BloodSugarRecord.value >= 11.1, 1), else_=0)).label("very_high"),
        )
        .where(BloodSugarRecord.person_id == person_id)
        .where(BloodSugarRecord.measured_at >= cutoff)
    )
    result = await db.execute(stmt)
    row = result.one()

    return {
        "labels": ["偏低(<3.9)", "正常(3.9-6.1)", "偏高(6.1-7.8)", "高(7.8-11.1)", "很高(>11.1)"],
        "values": [row.low or 0, row.normal or 0, row.elevated or 0, row.high or 0, row.very_high or 0],
        "colors": ["#3b82f6", "#22c55e", "#eab308", "#f97316", "#ef4444"],
    }


@router.get("/blood-sugar-by-context")
async def blood_sugar_by_context(
    person_id: int,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Blood sugar statistics by measurement context."""
    cutoff = datetime.now() - timedelta(days=days)
    stmt = (
        select(
            BloodSugarRecord.meal_context,
            func.count(BloodSugarRecord.id).label("count"),
            func.avg(BloodSugarRecord.value).label("avg"),
            func.min(BloodSugarRecord.value).label("min"),
            func.max(BloodSugarRecord.value).label("max"),
        )
        .where(BloodSugarRecord.person_id == person_id)
        .where(BloodSugarRecord.measured_at >= cutoff)
        .group_by(BloodSugarRecord.meal_context)
    )
    result = await db.execute(stmt)
    rows = result.all()

    context_names = {
        "fasting": "空腹",
        "before_meal": "餐前",
        "after_meal": "餐后",
        "bedtime": "睡前",
        "random": "随机",
    }

    return [
        {
            "context": context_names.get(row.meal_context or "random", "随机"),
            "count": row.count,
            "avg": round(float(row.avg), 1) if row.avg else None,
            "min": round(float(row.min), 1) if row.min else None,
            "max": round(float(row.max), 1) if row.max else None,
        }
        for row in rows
    ]


@router.get("/bp-trend")
async def bp_trend(
    person_id: int,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Blood pressure trend data for Chart.js."""
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


@router.get("/bp-stats")
async def bp_stats(
    person_id: int,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Blood pressure summary statistics."""
    cutoff = datetime.now() - timedelta(days=days)
    stmt = (
        select(
            func.count(BloodPressureRecord.id).label("count"),
            func.avg(BloodPressureRecord.systolic).label("avg_sys"),
            func.avg(BloodPressureRecord.diastolic).label("avg_dia"),
            func.avg(BloodPressureRecord.heart_rate).label("avg_hr"),
            func.min(BloodPressureRecord.systolic).label("min_sys"),
            func.max(BloodPressureRecord.systolic).label("max_sys"),
            func.min(BloodPressureRecord.diastolic).label("min_dia"),
            func.max(BloodPressureRecord.diastolic).label("max_dia"),
            func.sum(func.cast(BloodPressureRecord.is_alert, int)).label("alert_count"),
        )
        .where(BloodPressureRecord.person_id == person_id)
        .where(BloodPressureRecord.measured_at >= cutoff)
    )
    result = await db.execute(stmt)
    row = result.one()

    return {
        "count": row.count or 0,
        "avg_systolic": round(float(row.avg_sys), 1) if row.avg_sys else None,
        "avg_diastolic": round(float(row.avg_dia), 1) if row.avg_dia else None,
        "avg_heart_rate": round(float(row.avg_hr), 1) if row.avg_hr else None,
        "min_systolic": row.min_sys,
        "max_systolic": row.max_sys,
        "min_diastolic": row.min_dia,
        "max_diastolic": row.max_dia,
        "alert_count": row.alert_count or 0,
    }


@router.get("/bp-distribution")
async def bp_distribution(
    person_id: int,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Blood pressure grade distribution."""
    cutoff = datetime.now() - timedelta(days=days)
    stmt = (
        select(
            func.sum(case(
                (BloodPressureRecord.systolic < 120, 1),
                (BloodPressureRecord.diastolic < 80, 1),
                else_=0
            )).label("normal"),
            func.sum(case(
                (BloodPressureRecord.systolic >= 120, 1),
                (BloodPressureRecord.systolic < 140, 1),
                else_=0
            )).label("elevated"),
            func.sum(case(
                (BloodPressureRecord.systolic >= 140, 1),
                (BloodPressureRecord.systolic < 160, 1),
                else_=0
            )).label("stage1"),
            func.sum(case(
                (BloodPressureRecord.systolic >= 160, 1),
                (BloodPressureRecord.systolic < 180, 1),
                else_=0
            )).label("stage2"),
            func.sum(case((BloodPressureRecord.systolic >= 180, 1), else_=0)).label("stage3"),
        )
        .where(BloodPressureRecord.person_id == person_id)
        .where(BloodPressureRecord.measured_at >= cutoff)
    )
    result = await db.execute(stmt)
    row = result.one()

    return {
        "labels": ["理想(<120/80)", "正常高值", "高血压1级", "高血压2级", "高血压3级"],
        "values": [row.normal or 0, row.elevated or 0, row.stage1 or 0, row.stage2 or 0, row.stage3 or 0],
        "colors": ["#22c55e", "#eab308", "#f97316", "#ef4444", "#7c3aed"],
    }


@router.get("/weekly-comparison")
async def weekly_comparison(
    person_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Compare this week vs last week."""
    now = datetime.now()
    this_week_start = now - timedelta(days=now.weekday())
    last_week_start = this_week_start - timedelta(days=7)

    # Blood sugar this week
    bs_this_stmt = (
        select(func.avg(BloodSugarRecord.value))
        .where(BloodSugarRecord.person_id == person_id)
        .where(BloodSugarRecord.measured_at >= this_week_start)
    )
    bs_this = (await db.execute(bs_this_stmt)).scalar()

    # Blood sugar last week
    bs_last_stmt = (
        select(func.avg(BloodSugarRecord.value))
        .where(BloodSugarRecord.person_id == person_id)
        .where(BloodSugarRecord.measured_at >= last_week_start)
        .where(BloodSugarRecord.measured_at < this_week_start)
    )
    bs_last = (await db.execute(bs_last_stmt)).scalar()

    # BP this week
    bp_this_stmt = (
        select(
            func.avg(BloodPressureRecord.systolic),
            func.avg(BloodPressureRecord.diastolic),
        )
        .where(BloodPressureRecord.person_id == person_id)
        .where(BloodPressureRecord.measured_at >= this_week_start)
    )
    bp_this = (await db.execute(bp_this_stmt)).one()

    # BP last week
    bp_last_stmt = (
        select(
            func.avg(BloodPressureRecord.systolic),
            func.avg(BloodPressureRecord.diastolic),
        )
        .where(BloodPressureRecord.person_id == person_id)
        .where(BloodPressureRecord.measured_at >= last_week_start)
        .where(BloodPressureRecord.measured_at < this_week_start)
    )
    bp_last = (await db.execute(bp_last_stmt)).one()

    return {
        "blood_sugar": {
            "this_week": round(float(bs_this), 1) if bs_this else None,
            "last_week": round(float(bs_last), 1) if bs_last else None,
            "change": round(float(bs_this - bs_last), 1) if bs_this and bs_last else None,
        },
        "blood_pressure": {
            "this_week": {
                "systolic": round(float(bp_this[0]), 1) if bp_this[0] else None,
                "diastolic": round(float(bp_this[1]), 1) if bp_this[1] else None,
            },
            "last_week": {
                "systolic": round(float(bp_last[0]), 1) if bp_last[0] else None,
                "diastolic": round(float(bp_last[1]), 1) if bp_last[1] else None,
            },
        },
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

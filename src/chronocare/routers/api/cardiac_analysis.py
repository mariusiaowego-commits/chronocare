"""Cardiac Analysis API — BP grading, statistics, alerts."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.models.cardiac import BloodPressureRecord
from chronocare.services.cardiac_analysis import (
    grade_bp,
    grade_heart_rate,
    get_bp_alerts,
    get_bp_comparison,
    get_bp_stats,
    should_alert,
)

import csv
import io

router = APIRouter(prefix="/api/cardiac", tags=["cardiac-api"])


@router.get("/grade")
async def bp_grade(systolic: int, diastolic: int, heart_rate: int | None = None):
    """Grade a blood pressure reading."""
    bp_grade = grade_bp(systolic, diastolic)
    hr_grade = grade_heart_rate(heart_rate)
    alert = should_alert(systolic, diastolic, heart_rate)

    return {
        "bp": bp_grade,
        "heart_rate": hr_grade,
        "is_alert": alert,
    }


@router.get("/stats")
async def bp_stats(
    person_id: int,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get blood pressure statistics."""
    stats = await get_bp_stats(db, person_id, days)
    return stats


@router.get("/comparison")
async def bp_comparison(
    person_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Compare latest reading with previous."""
    comp = await get_bp_comparison(db, person_id)
    if comp.get("latest"):
        latest = comp["latest"]
        comp["latest_grade"] = grade_bp(latest.systolic, latest.diastolic)
        comp["latest_hr_grade"] = grade_heart_rate(latest.heart_rate)
    if comp.get("previous"):
        prev = comp["previous"]
        comp["previous_grade"] = grade_bp(prev.systolic, prev.diastolic)
    return comp


@router.get("/alerts")
async def bp_alerts(
    person_id: int,
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """Get recent alert records."""
    alerts = await get_bp_alerts(db, person_id, limit)
    return [
        {
            "id": r.id,
            "measured_at": r.measured_at.isoformat(),
            "systolic": r.systolic,
            "diastolic": r.diastolic,
            "heart_rate": r.heart_rate,
            "grade": grade_bp(r.systolic, r.diastolic),
        }
        for r in alerts
    ]


@router.post("/auto-alert/{record_id}")
async def auto_alert_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Auto-calculate and update alert status for a record."""
    result = await db.execute(
        select(BloodPressureRecord).where(BloodPressureRecord.id == record_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        return {"error": "Record not found"}

    record.is_alert = should_alert(record.systolic, record.diastolic, record.heart_rate)
    await db.commit()
    return {
        "id": record.id,
        "is_alert": record.is_alert,
        "grade": grade_bp(record.systolic, record.diastolic),
    }


@router.post("/auto-alert-all")
async def auto_alert_all(
    person_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Recalculate alerts for all records."""
    stmt = select(BloodPressureRecord)
    if person_id:
        stmt = stmt.where(BloodPressureRecord.person_id == person_id)

    result = await db.execute(stmt)
    records = result.scalars().all()

    updated = 0
    for record in records:
        new_alert = should_alert(record.systolic, record.diastolic, record.heart_rate)
        if record.is_alert != new_alert:
            record.is_alert = new_alert
            updated += 1

    await db.commit()
    return {"total": len(records), "updated": updated}


@router.get("/export")
async def export_bp(
    person_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Export blood pressure records as CSV with grading."""
    stmt = (
        select(BloodPressureRecord)
        .where(BloodPressureRecord.person_id == person_id)
        .order_by(BloodPressureRecord.measured_at.desc())
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["日期时间", "收缩压", "舒张压", "心率", "血压分级", "心率状态", "预警", "备注"])

    for r in records:
        bp = grade_bp(r.systolic, r.diastolic)
        hr = grade_heart_rate(r.heart_rate)
        writer.writerow([
            r.measured_at.strftime("%Y-%m-%d %H:%M"),
            r.systolic,
            r.diastolic,
            r.heart_rate or "",
            bp["grade"],
            hr["grade"],
            "是" if r.is_alert else "否",
            r.notes or "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=bp_records_{person_id}.csv"},
    )

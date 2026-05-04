"""Cardiac analysis service — BP grading, heart rate alerts, statistics."""

from datetime import datetime, timedelta

import sqlalchemy
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.models.cardiac import BloodPressureRecord


# WHO/中国高血压分级标准
BP_GRADES = [
    # (name, systolic_max, diastolic_max, color, icon)
    ("理想", 120, 80, "green", "💚"),
    ("正常高值", 139, 89, "yellow", "💛"),
    ("高血压1级", 159, 99, "orange", "🧡"),
    ("高血压2级", 179, 109, "red", "❤️"),
    ("高血压3级", 999, 999, "purple", "💜"),
]


def grade_bp(systolic: int, diastolic: int) -> dict:
    """Grade blood pressure reading according to guidelines."""
    for name, sys_max, dia_max, color, icon in BP_GRADES:
        if systolic <= sys_max and diastolic <= dia_max:
            return {"grade": name, "color": color, "icon": icon}
    return {"grade": "高血压3级", "color": "purple", "icon": "💜"}


def grade_heart_rate(hr: int | None) -> dict:
    """Grade heart rate reading."""
    if hr is None:
        return {"grade": "未记录", "color": "gray", "icon": "➖"}
    if hr < 60:
        return {"grade": "心动过缓", "color": "blue", "icon": "💙"}
    if hr <= 100:
        return {"grade": "正常", "color": "green", "icon": "💚"}
    return {"grade": "心动过速", "color": "red", "icon": "❤️‍🔥"}


def should_alert(systolic: int, diastolic: int, heart_rate: int | None = None) -> bool:
    """Determine if reading should trigger alert."""
    # BP alert: hypertension grade 1+
    if systolic >= 140 or diastolic >= 90:
        return True
    # Heart rate alert
    if heart_rate is not None and (heart_rate < 50 or heart_rate > 120):
        return True
    return False


async def get_bp_stats(db: AsyncSession, person_id: int, days: int = 30) -> dict:
    """Get blood pressure statistics for a person."""
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
            func.sum(func.cast(BloodPressureRecord.is_alert, sqlalchemy.Integer)).label("alert_count"),
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
        "avg_grade": grade_bp(
            round(float(row.avg_sys)) if row.avg_sys else 0,
            round(float(row.avg_dia)) if row.avg_dia else 0,
        ) if row.avg_sys else None,
    }


async def get_bp_comparison(db: AsyncSession, person_id: int) -> dict:
    """Compare latest reading with previous reading."""
    stmt = (
        select(BloodPressureRecord)
        .where(BloodPressureRecord.person_id == person_id)
        .order_by(BloodPressureRecord.measured_at.desc())
        .limit(2)
    )
    result = await db.execute(stmt)
    records = list(result.scalars().all())

    if len(records) < 2:
        return {"has_comparison": False, "latest": records[0] if records else None}

    latest, previous = records[0], records[1]
    return {
        "has_comparison": True,
        "latest": latest,
        "previous": previous,
        "systolic_change": latest.systolic - previous.systolic,
        "diastolic_change": latest.diastolic - previous.diastolic,
        "heart_rate_change": (
            (latest.heart_rate or 0) - (previous.heart_rate or 0)
            if latest.heart_rate and previous.heart_rate
            else None
        ),
    }


async def get_bp_alerts(db: AsyncSession, person_id: int, limit: int = 5) -> list[BloodPressureRecord]:
    """Get recent alert records."""
    stmt = (
        select(BloodPressureRecord)
        .where(BloodPressureRecord.person_id == person_id)
        .where(BloodPressureRecord.is_alert == True)
        .order_by(BloodPressureRecord.measured_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())

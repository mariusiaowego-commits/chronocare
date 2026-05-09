"""Trend alert service — detect abnormal trends in health data."""

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.models.blood_sugar import BloodSugarRecord
from chronocare.models.cardiac import BloodPressureRecord


async def detect_blood_sugar_alerts(
    person_id: int,
    db: AsyncSession,
) -> list[dict]:
    """Detect blood sugar abnormal patterns:
    1. Consecutive high readings (3+ in a row > 7.8)
    2. Sustained elevation (7-day avg > 7.0)
    3. Rapid increase (>3 mmol/L increase in 3 days)
    """
    alerts = []
    now = datetime.now()

    # Get recent 7 days data
    stmt = (
        select(BloodSugarRecord)
        .where(BloodSugarRecord.person_id == person_id)
        .where(BloodSugarRecord.measured_at >= now - timedelta(days=7))
        .order_by(BloodSugarRecord.measured_at.asc())
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    if len(records) < 2:
        return alerts

    values = [r.value for r in records]

    # Check 1: Consecutive high readings
    consecutive_high = 0
    for v in reversed(values):
        if v > 7.8:
            consecutive_high += 1
        else:
            break
    if consecutive_high >= 3:
        alerts.append({
            "type": "consecutive_high",
            "severity": "high",
            "title": "连续高血糖",
            "message": f"最近 {consecutive_high} 次血糖记录均高于 7.8 mmol/L",
            "icon": "🔴",
        })

    # Check 2: 7-day average
    avg_7d = sum(values) / len(values)
    if avg_7d > 7.0:
        alerts.append({
            "type": "sustained_elevation",
            "severity": "medium",
            "title": "血糖持续偏高",
            "message": f"近 7 天平均血糖 {avg_7d:.1f} mmol/L（正常 < 6.1）",
            "icon": "🟡",
        })

    # Check 3: Rapid increase
    if len(values) >= 3:
        recent_3d = values[-3:]
        if recent_3d[-1] - recent_3d[0] > 3:
            alerts.append({
                "type": "rapid_increase",
                "severity": "high",
                "title": "血糖快速上升",
                "message": f"3 天内血糖上升 {recent_3d[-1] - recent_3d[0]:.1f} mmol/L",
                "icon": "🔺",
            })

    # Check 4: Very high single reading
    latest = values[-1]
    if latest > 11.1:
        alerts.append({
            "type": "very_high",
            "severity": "critical",
            "title": "血糖严重偏高",
            "message": f"最新血糖 {latest:.1f} mmol/L，已超过 11.1 mmol/L",
            "icon": "🚨",
        })

    return alerts


async def detect_blood_pressure_alerts(
    person_id: int,
    db: AsyncSession,
) -> list[dict]:
    """Detect blood pressure abnormal patterns."""
    alerts = []
    now = datetime.now()

    # Get recent 7 days data
    stmt = (
        select(BloodPressureRecord)
        .where(BloodPressureRecord.person_id == person_id)
        .where(BloodPressureRecord.measured_at >= now - timedelta(days=7))
        .order_by(BloodPressureRecord.measured_at.asc())
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    if len(records) < 2:
        return alerts

    sys_values = [r.systolic for r in records]
    dia_values = [r.diastolic for r in records]

    # Check 1: Consecutive high BP
    consecutive_high = 0
    for i in range(len(records) - 1, -1, -1):
        if sys_values[i] >= 140 or dia_values[i] >= 90:
            consecutive_high += 1
        else:
            break
    if consecutive_high >= 3:
        alerts.append({
            "type": "consecutive_high_bp",
            "severity": "high",
            "title": "连续高血压",
            "message": f"最近 {consecutive_high} 次血压记录均为高血压",
            "icon": "🔴",
        })

    # Check 2: 7-day average
    avg_sys = sum(sys_values) / len(sys_values)
    avg_dia = sum(dia_values) / len(dia_values)
    if avg_sys >= 140 or avg_dia >= 90:
        alerts.append({
            "type": "sustained_high_bp",
            "severity": "medium",
            "title": "血压持续偏高",
            "message": f"近 7 天平均血压 {avg_sys:.0f}/{avg_dia:.0f} mmHg",
            "icon": "🟡",
        })

    # Check 3: Very high single reading (hypertensive crisis)
    latest_sys = sys_values[-1]
    latest_dia = dia_values[-1]
    if latest_sys >= 180 or latest_dia >= 110:
        alerts.append({
            "type": "hypertensive_crisis",
            "severity": "critical",
            "title": "高血压危象",
            "message": f"最新血压 {latest_sys}/{latest_dia} mmHg，建议立即就医",
            "icon": "🚨",
        })

    # Check 4: Low heart rate
    hr_values = [r.heart_rate for r in records if r.heart_rate]
    if hr_values:
        latest_hr = hr_values[-1]
        if latest_hr < 50:
            alerts.append({
                "type": "bradycardia",
                "severity": "medium",
                "title": "心率过缓",
                "message": f"最新心率 {latest_hr} bpm，低于 50 bpm",
                "icon": "💙",
            })
        elif latest_hr > 100:
            alerts.append({
                "type": "tachycardia",
                "severity": "medium",
                "title": "心率过速",
                "message": f"最新心率 {latest_hr} bpm，超过 100 bpm",
                "icon": "💓",
            })

    return alerts


async def get_all_alerts(
    person_id: int,
    db: AsyncSession,
) -> dict:
    """Get all trend alerts for a person."""
    bs_alerts = await detect_blood_sugar_alerts(person_id, db)
    bp_alerts = await detect_blood_pressure_alerts(person_id, db)

    all_alerts = bs_alerts + bp_alerts

    # Sort by severity: critical > high > medium
    severity_order = {"critical": 0, "high": 1, "medium": 2}
    all_alerts.sort(key=lambda a: severity_order.get(a["severity"], 3))

    return {
        "person_id": person_id,
        "alert_count": len(all_alerts),
        "has_critical": any(a["severity"] == "critical" for a in all_alerts),
        "alerts": all_alerts,
    }

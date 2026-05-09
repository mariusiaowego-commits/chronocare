"""Blood sugar variability analysis — standard deviation, CV, control indicators."""

import math
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.models.blood_sugar import BloodSugarRecord


async def analyze_blood_sugar_variability(
    person_id: int,
    days: int = 30,
    db: AsyncSession = None,
) -> dict:
    """Analyze blood sugar variability over a period."""
    cutoff = datetime.now() - timedelta(days=days)

    stmt = (
        select(BloodSugarRecord.value)
        .where(BloodSugarRecord.person_id == person_id)
        .where(BloodSugarRecord.measured_at >= cutoff)
        .order_by(BloodSugarRecord.measured_at.asc())
    )
    result = await db.execute(stmt)
    values = [row[0] for row in result.all()]

    if len(values) < 2:
        return {
            "count": len(values),
            "error": "Insufficient data (need at least 2 readings)",
        }

    # Basic statistics
    n = len(values)
    mean = sum(values) / n
    min_val = min(values)
    max_val = max(values)
    range_val = max_val - min_val

    # Standard deviation
    variance = sum((x - mean) ** 2 for x in values) / (n - 1)
    std_dev = math.sqrt(variance)

    # Coefficient of variation (CV)
    cv = (std_dev / mean) * 100 if mean > 0 else 0

    # Mean amplitude of glycemic excursions (MAGE) - simplified
    # MAGE = average of glucose excursions > 1 SD
    mage_excursions = []
    for i in range(1, len(values)):
        diff = abs(values[i] - values[i-1])
        if diff > std_dev:
            mage_excursions.append(diff)
    mage = sum(mage_excursions) / len(mage_excursions) if mage_excursions else 0

    # Time in range (TIR) - percentage of readings in 3.9-10.0 mmol/L
    in_range = sum(1 for v in values if 3.9 <= v <= 10.0)
    tir = (in_range / n) * 100

    # Time below range (< 3.9)
    below_range = sum(1 for v in values if v < 3.9)
    tbr = (below_range / n) * 100

    # Time above range (> 10.0)
    above_range = sum(1 for v in values if v > 10.0)
    tar = (above_range / n) * 100

    # Glucose Management Indicator (GMI) - estimated HbA1c
    # GMI (%) = 3.31 + 0.02392 × mean glucose (mg/dL)
    # Convert mmol/L to mg/dL: multiply by 18.0182
    mean_mg_dl = mean * 18.0182
    gmi = 3.31 + 0.02392 * mean_mg_dl

    # Control rating
    if tir >= 70 and cv <= 36:
        control_rating = "优秀"
        control_color = "green"
    elif tir >= 50 and cv <= 50:
        control_rating = "良好"
        control_color = "blue"
    elif tir >= 30:
        control_rating = "一般"
        control_color = "yellow"
    else:
        control_rating = "需改善"
        control_color = "red"

    return {
        "count": n,
        "period_days": days,
        "mean": round(mean, 2),
        "std_dev": round(std_dev, 2),
        "cv": round(cv, 1),
        "min": round(min_val, 1),
        "max": round(max_val, 1),
        "range": round(range_val, 1),
        "mage": round(mage, 2),
        "tir": round(tir, 1),
        "tbr": round(tbr, 1),
        "tar": round(tar, 1),
        "gmi": round(gmi, 1),
        "control_rating": control_rating,
        "control_color": control_color,
        "interpretation": _interpret_results(cv, tir, mage, gmi),
    }


def _interpret_results(cv: float, tir: float, mage: float, gmi: float) -> list[str]:
    """Generate interpretation notes."""
    notes = []

    # CV interpretation
    if cv <= 20:
        notes.append("血糖波动很小，控制非常稳定")
    elif cv <= 36:
        notes.append("血糖波动适中，控制良好")
    elif cv <= 50:
        notes.append("血糖波动较大，建议关注饮食和运动")
    else:
        notes.append("血糖波动很大，建议就医调整方案")

    # TIR interpretation
    if tir >= 70:
        notes.append(f"血糖在目标范围内时间 {tir:.0f}%，达标（目标 ≥70%）")
    elif tir >= 50:
        notes.append(f"血糖在目标范围内时间 {tir:.0f}%，接近达标")
    else:
        notes.append(f"血糖在目标范围内时间 {tir:.0f}%，未达标（目标 ≥70%）")

    # MAGE interpretation
    if mage > 5:
        notes.append(f"平均血糖波动幅度 {mage:.1f} mmol/L，波动较大")
    elif mage > 3:
        notes.append(f"平均血糖波动幅度 {mage:.1f} mmol/L，波动适中")

    # GMI interpretation
    if gmi < 6.5:
        notes.append(f"预估糖化血红蛋白 {gmi:.1f}%，控制优秀")
    elif gmi < 7.0:
        notes.append(f"预估糖化血红蛋白 {gmi:.1f}%，控制良好")
    elif gmi < 8.0:
        notes.append(f"预估糖化血红蛋白 {gmi:.1f}%，需改善")
    else:
        notes.append(f"预估糖化血红蛋白 {gmi:.1f}%，控制不佳")

    return notes


async def analyze_blood_sugar_by_time(
    person_id: int,
    days: int = 30,
    db: AsyncSession = None,
) -> dict:
    """Analyze blood sugar patterns by time of day."""
    cutoff = datetime.now() - timedelta(days=days)

    stmt = (
        select(BloodSugarRecord)
        .where(BloodSugarRecord.person_id == person_id)
        .where(BloodSugarRecord.measured_at >= cutoff)
        .order_by(BloodSugarRecord.measured_at.asc())
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    # Group by hour
    hourly = {}
    for r in records:
        hour = r.measured_at.hour
        if hour not in hourly:
            hourly[hour] = []
        hourly[hour].append(r.value)

    # Calculate stats for each hour
    time_patterns = []
    for hour in sorted(hourly.keys()):
        values = hourly[hour]
        avg = sum(values) / len(values)
        time_patterns.append({
            "hour": hour,
            "label": f"{hour:02d}:00",
            "count": len(values),
            "avg": round(avg, 1),
            "min": round(min(values), 1),
            "max": round(max(values), 1),
        })

    # Find peak and trough
    if time_patterns:
        peak = max(time_patterns, key=lambda x: x["avg"])
        trough = min(time_patterns, key=lambda x: x["avg"])
    else:
        peak = trough = None

    return {
        "count": len(records),
        "time_patterns": time_patterns,
        "peak": peak,
        "trough": trough,
        "dawn_phenomenon": _detect_dawn_phenomenon(time_patterns),
    }


def _detect_dawn_phenomenon(time_patterns: list[dict]) -> dict | None:
    """Detect dawn phenomenon (early morning glucose rise)."""
    # Look for glucose rise between 3-8 AM
    morning_readings = [p for p in time_patterns if 3 <= p["hour"] <= 8]
    if len(morning_readings) < 2:
        return None

    # Check if there's a rising trend
    values = [p["avg"] for p in morning_readings]
    if len(values) >= 2 and values[-1] > values[0] + 1.0:
        return {
            "detected": True,
            "rise": round(values[-1] - values[0], 1),
            "message": f"检测到黎明现象：凌晨血糖上升 {values[-1] - values[0]:.1f} mmol/L",
        }
    return {"detected": False}

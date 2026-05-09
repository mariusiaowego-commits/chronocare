"""Medication adherence analysis — dosage compliance tracking."""

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.models.medication import MedicationLog, MedicationPlan


async def analyze_medication_adherence(
    person_id: int,
    days: int = 30,
    db: AsyncSession = None,
) -> dict:
    """Analyze medication adherence patterns."""
    cutoff = datetime.now() - timedelta(days=days)

    # Get medication plans
    plans_stmt = (
        select(MedicationPlan)
        .where(MedicationPlan.person_id == person_id)
        .where(MedicationPlan.is_active)
    )
    plans_result = await db.execute(plans_stmt)
    plans = plans_result.scalars().all()

    if not plans:
        return {
            "error": "No active medication plans found",
            "plans_count": 0,
        }

    # Get dosage records
    records_stmt = (
        select(MedicationLog)
        .where(MedicationLog.person_id == person_id)
        .where(MedicationLog.taken_at >= cutoff)
        .order_by(MedicationLog.taken_at.asc())
    )
    records_result = await db.execute(records_stmt)
    records = records_result.scalars().all()

    # Analyze each plan
    plan_adherence = []
    for plan in plans:
        plan_records = [r for r in records if r.plan_id == plan.id]
        adherence = _calculate_plan_adherence(plan, plan_records, days)
        plan_adherence.append(adherence)

    # Overall adherence
    total_expected = sum(p["expected_doses"] for p in plan_adherence)
    total_taken = sum(p["taken_doses"] for p in plan_adherence)
    overall_rate = (total_taken / total_expected * 100) if total_expected > 0 else 0

    # Adherence rating
    if overall_rate >= 90:
        rating = "优秀"
        color = "green"
    elif overall_rate >= 80:
        rating = "良好"
        color = "blue"
    elif overall_rate >= 60:
        rating = "一般"
        color = "yellow"
    else:
        rating = "需改善"
        color = "red"

    # Recent streak
    streak = _calculate_streak(records)

    # Time pattern analysis
    time_pattern = _analyze_time_pattern(records)

    return {
        "period_days": days,
        "plans_count": len(plans),
        "total_expected": total_expected,
        "total_taken": total_taken,
        "overall_rate": round(overall_rate, 1),
        "rating": rating,
        "color": color,
        "streak": streak,
        "time_pattern": time_pattern,
        "plan_adherence": plan_adherence,
        "interpretation": _interpret_adherence(overall_rate, streak, plan_adherence),
    }


def _calculate_plan_adherence(plan: MedicationPlan, records: list, days: int) -> dict:
    """Calculate adherence for a single medication plan."""
    # Parse timing to estimate expected doses
    timing_count = 1  # Default once daily
    if plan.timing:
        timing_count = len([t for t in plan.timing.split(",") if t.strip()])

    expected_doses = timing_count * days
    taken_doses = len(records)
    rate = (taken_doses / expected_doses * 100) if expected_doses > 0 else 0

    return {
        "plan_id": plan.id,
        "drug_name": plan.drug_name,
        "dosage": plan.dosage,
        "frequency": plan.frequency,
        "timing": plan.timing,
        "expected_doses": expected_doses,
        "taken_doses": taken_doses,
        "rate": round(rate, 1),
        "last_taken": records[-1].taken_at.isoformat() if records else None,
    }


def _calculate_streak(records: list) -> dict:
    """Calculate current adherence streak."""
    if not records:
        return {"current": 0, "max": 0}

    # Group by date
    dates = set()
    for r in records:
        dates.add(r.taken_at.date())

    sorted_dates = sorted(dates, reverse=True)
    
    # Calculate current streak
    current_streak = 0
    today = datetime.now().date()
    check_date = today

    for d in sorted_dates:
        if d == check_date:
            current_streak += 1
            check_date -= timedelta(days=1)
        elif d < check_date:
            break

    return {
        "current": current_streak,
        "max": len(sorted_dates),  # Simplified
        "last_date": sorted_dates[0].isoformat() if sorted_dates else None,
    }


def _analyze_time_pattern(records: list) -> dict:
    """Analyze medication time patterns."""
    if not records:
        return {"patterns": []}

    hourly = {}
    for r in records:
        hour = r.taken_at.hour
        if hour not in hourly:
            hourly[hour] = 0
        hourly[hour] += 1

    patterns = []
    for hour in sorted(hourly.keys()):
        patterns.append({
            "hour": hour,
            "label": f"{hour:02d}:00",
            "count": hourly[hour],
        })

    # Find peak time
    peak = max(patterns, key=lambda x: x["count"]) if patterns else None

    return {
        "patterns": patterns,
        "peak": peak,
    }


def _interpret_adherence(rate: float, streak: dict, plan_adherence: list) -> list[str]:
    """Generate interpretation notes."""
    notes = []

    # Overall rating
    if rate >= 90:
        notes.append(f"用药依从性优秀 ({rate:.0f}%)，坚持得很好")
    elif rate >= 80:
        notes.append(f"用药依从性良好 ({rate:.0f}%)，继续保持")
    elif rate >= 60:
        notes.append(f"用药依从性一般 ({rate:.0f}%)，有漏服情况")
        notes.append("建议：设置手机提醒或使用药盒")
    else:
        notes.append(f"用药依从性较差 ({rate:.0f}%)，漏服较多")
        notes.append("建议：与医生沟通调整方案或加强提醒")

    # Streak
    if streak["current"] > 0:
        notes.append(f"当前连续服药 {streak['current']} 天")

    # Individual plan issues
    for p in plan_adherence:
        if p["rate"] < 80:
            notes.append(f"⚠️ {p['drug_name']} 依从率仅 {p['rate']:.0f}%，需关注")

    return notes

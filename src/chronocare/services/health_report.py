"""Health report service — generate weekly/monthly reports."""

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.models.blood_sugar import BloodSugarRecord
from chronocare.models.cardiac import BloodPressureRecord
from chronocare.models.medication import MedicationPlan
from chronocare.models.person import Person
from chronocare.models.visit import Visit
from chronocare.services.trend_alert import get_all_alerts


async def generate_weekly_report(
    person_id: int,
    db: AsyncSession,
) -> dict:
    """Generate a weekly health report."""
    now = datetime.now()
    week_start = now - timedelta(days=now.weekday())  # Monday
    last_week_start = week_start - timedelta(days=7)

    # Get person info
    person = await db.get(Person, person_id)
    if not person:
        return {"error": "Person not found"}

    # Blood sugar data
    bs_stmt = (
        select(
            func.count(BloodSugarRecord.id).label("count"),
            func.avg(BloodSugarRecord.value).label("avg"),
            func.min(BloodSugarRecord.value).label("min"),
            func.max(BloodSugarRecord.value).label("max"),
            func.sum(func.cast(BloodSugarRecord.is_alert, int)).label("alert_count"),
        )
        .where(BloodSugarRecord.person_id == person_id)
        .where(BloodSugarRecord.measured_at >= week_start)
    )
    bs_result = await db.execute(bs_stmt)
    bs = bs_result.one()

    # Blood pressure data
    bp_stmt = (
        select(
            func.count(BloodPressureRecord.id).label("count"),
            func.avg(BloodPressureRecord.systolic).label("avg_sys"),
            func.avg(BloodPressureRecord.diastolic).label("avg_dia"),
            func.avg(BloodPressureRecord.heart_rate).label("avg_hr"),
            func.sum(func.cast(BloodPressureRecord.is_alert, int)).label("alert_count"),
        )
        .where(BloodPressureRecord.person_id == person_id)
        .where(BloodPressureRecord.measured_at >= week_start)
    )
    bp_result = await db.execute(bp_stmt)
    bp = bp_result.one()

    # Last week comparison
    bs_last_stmt = (
        select(func.avg(BloodSugarRecord.value))
        .where(BloodSugarRecord.person_id == person_id)
        .where(BloodSugarRecord.measured_at >= last_week_start)
        .where(BloodSugarRecord.measured_at < week_start)
    )
    bs_last_avg = (await db.execute(bs_last_stmt)).scalar()

    bp_last_stmt = (
        select(
            func.avg(BloodPressureRecord.systolic),
            func.avg(BloodPressureRecord.diastolic),
        )
        .where(BloodPressureRecord.person_id == person_id)
        .where(BloodPressureRecord.measured_at >= last_week_start)
        .where(BloodPressureRecord.measured_at < week_start)
    )
    bp_last = (await db.execute(bp_last_stmt)).one()

    # Get alerts
    alerts_data = await get_all_alerts(person_id, db)

    # Get visits this week
    visits_stmt = (
        select(Visit)
        .where(Visit.person_id == person_id)
        .where(Visit.visit_date >= week_start.strftime("%Y-%m-%d"))
        .order_by(Visit.visit_date.desc())
    )
    visits_result = await db.execute(visits_stmt)
    visits = visits_result.scalars().all()

    # Get active medication plans
    plans_stmt = (
        select(MedicationPlan)
        .where(MedicationPlan.person_id == person_id)
        .where(MedicationPlan.is_active)
    )
    plans_result = await db.execute(plans_stmt)
    plans = plans_result.scalars().all()

    return {
        "report_type": "weekly",
        "period": {
            "start": week_start.strftime("%Y-%m-%d"),
            "end": now.strftime("%Y-%m-%d"),
        },
        "person": {
            "name": person.name,
            "age": _calculate_age(person.birth_date) if person.birth_date else None,
        },
        "blood_sugar": {
            "count": bs.count or 0,
            "avg": round(float(bs.avg), 1) if bs.avg else None,
            "min": round(float(bs.min), 1) if bs.min else None,
            "max": round(float(bs.max), 1) if bs.max else None,
            "alert_count": bs.alert_count or 0,
            "last_week_avg": round(float(bs_last_avg), 1) if bs_last_avg else None,
            "trend": _calculate_trend(bs.avg, bs_last_avg),
        },
        "blood_pressure": {
            "count": bp.count or 0,
            "avg_systolic": round(float(bp.avg_sys), 1) if bp.avg_sys else None,
            "avg_diastolic": round(float(bp.avg_dia), 1) if bp.avg_dia else None,
            "avg_heart_rate": round(float(bp.avg_hr), 1) if bp.avg_hr else None,
            "alert_count": bp.alert_count or 0,
            "last_week_avg_sys": round(float(bp_last[0]), 1) if bp_last[0] else None,
            "last_week_avg_dia": round(float(bp_last[1]), 1) if bp_last[1] else None,
            "trend": _calculate_trend(bp.avg_sys, bp_last[0]),
        },
        "alerts": alerts_data["alerts"],
        "visits": [
            {
                "date": v.visit_date,
                "hospital": v.hospital,
                "diagnosis": v.diagnosis,
            }
            for v in visits
        ],
        "medications": [
            {
                "name": p.medication.name if p.medication else f"药品 #{p.medication_id}",
                "dosage": p.dosage,
                "frequency": p.frequency,
            }
            for p in plans
        ],
        "generated_at": now.isoformat(),
    }


async def generate_monthly_report(
    person_id: int,
    db: AsyncSession,
) -> dict:
    """Generate a monthly health report."""
    now = datetime.now()
    month_start = now.replace(day=1)
    last_month_end = month_start - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)

    # Get person info
    person = await db.get(Person, person_id)
    if not person:
        return {"error": "Person not found"}

    # Blood sugar data
    bs_stmt = (
        select(
            func.count(BloodSugarRecord.id).label("count"),
            func.avg(BloodSugarRecord.value).label("avg"),
            func.min(BloodSugarRecord.value).label("min"),
            func.max(BloodSugarRecord.value).label("max"),
            func.sum(func.cast(BloodSugarRecord.is_alert, int)).label("alert_count"),
        )
        .where(BloodSugarRecord.person_id == person_id)
        .where(BloodSugarRecord.measured_at >= month_start)
    )
    bs_result = await db.execute(bs_stmt)
    bs = bs_result.one()

    # Blood pressure data
    bp_stmt = (
        select(
            func.count(BloodPressureRecord.id).label("count"),
            func.avg(BloodPressureRecord.systolic).label("avg_sys"),
            func.avg(BloodPressureRecord.diastolic).label("avg_dia"),
            func.avg(BloodPressureRecord.heart_rate).label("avg_hr"),
            func.sum(func.cast(BloodPressureRecord.is_alert, int)).label("alert_count"),
        )
        .where(BloodPressureRecord.person_id == person_id)
        .where(BloodPressureRecord.measured_at >= month_start)
    )
    bp_result = await db.execute(bp_stmt)
    bp = bp_result.one()

    # Last month comparison
    bs_last_stmt = (
        select(func.avg(BloodSugarRecord.value))
        .where(BloodSugarRecord.person_id == person_id)
        .where(BloodSugarRecord.measured_at >= last_month_start)
        .where(BloodSugarRecord.measured_at < month_start)
    )
    bs_last_avg = (await db.execute(bs_last_stmt)).scalar()

    bp_last_stmt = (
        select(
            func.avg(BloodPressureRecord.systolic),
            func.avg(BloodPressureRecord.diastolic),
        )
        .where(BloodPressureRecord.person_id == person_id)
        .where(BloodPressureRecord.measured_at >= last_month_start)
        .where(BloodPressureRecord.measured_at < month_start)
    )
    bp_last = (await db.execute(bp_last_stmt)).one()

    # Get alerts
    alerts_data = await get_all_alerts(person_id, db)

    # Get visits this month
    visits_stmt = (
        select(Visit)
        .where(Visit.person_id == person_id)
        .where(Visit.visit_date >= month_start.strftime("%Y-%m-%d"))
        .order_by(Visit.visit_date.desc())
    )
    visits_result = await db.execute(visits_stmt)
    visits = visits_result.scalars().all()

    # Get active medication plans
    plans_stmt = (
        select(MedicationPlan)
        .where(MedicationPlan.person_id == person_id)
        .where(MedicationPlan.is_active)
    )
    plans_result = await db.execute(plans_stmt)
    plans = plans_result.scalars().all()

    return {
        "report_type": "monthly",
        "period": {
            "start": month_start.strftime("%Y-%m-%d"),
            "end": now.strftime("%Y-%m-%d"),
            "month": now.strftime("%Y年%m月"),
        },
        "person": {
            "name": person.name,
            "age": _calculate_age(person.birth_date) if person.birth_date else None,
        },
        "blood_sugar": {
            "count": bs.count or 0,
            "avg": round(float(bs.avg), 1) if bs.avg else None,
            "min": round(float(bs.min), 1) if bs.min else None,
            "max": round(float(bs.max), 1) if bs.max else None,
            "alert_count": bs.alert_count or 0,
            "last_month_avg": round(float(bs_last_avg), 1) if bs_last_avg else None,
            "trend": _calculate_trend(bs.avg, bs_last_avg),
        },
        "blood_pressure": {
            "count": bp.count or 0,
            "avg_systolic": round(float(bp.avg_sys), 1) if bp.avg_sys else None,
            "avg_diastolic": round(float(bp.avg_dia), 1) if bp.avg_dia else None,
            "avg_heart_rate": round(float(bp.avg_hr), 1) if bp.avg_hr else None,
            "alert_count": bp.alert_count or 0,
            "last_month_avg_sys": round(float(bp_last[0]), 1) if bp_last[0] else None,
            "last_month_avg_dia": round(float(bp_last[1]), 1) if bp_last[1] else None,
            "trend": _calculate_trend(bp.avg_sys, bp_last[0]),
        },
        "alerts": alerts_data["alerts"],
        "visits": [
            {
                "date": v.visit_date,
                "hospital": v.hospital,
                "diagnosis": v.diagnosis,
            }
            for v in visits
        ],
        "medications": [
            {
                "name": p.medication.name if p.medication else f"药品 #{p.medication_id}",
                "dosage": p.dosage,
                "frequency": p.frequency,
            }
            for p in plans
        ],
        "generated_at": now.isoformat(),
    }


def _calculate_age(birth_date: str | None) -> int | None:
    """Calculate age from birth date string."""
    if not birth_date:
        return None
    try:
        birth = datetime.strptime(birth_date, "%Y-%m-%d")
        today = datetime.now()
        age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        return age
    except (ValueError, TypeError):
        return None


def _calculate_trend(current: float | None, previous: float | None) -> str | None:
    """Calculate trend direction."""
    if current is None or previous is None:
        return None
    diff = current - previous
    if abs(diff) < 0.1:
        return "stable"
    return "up" if diff > 0 else "down"

"""Health profile service — comprehensive health overview."""

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from chronocare.models.blood_sugar import BloodSugarRecord
from chronocare.models.cardiac import BloodPressureRecord
from chronocare.models.medication import MedicationPlan
from chronocare.models.person import Person
from chronocare.models.visit import Visit
from chronocare.services.cardiac_analysis import grade_bp, grade_heart_rate


async def get_health_overview(db: AsyncSession, person_id: int) -> dict:
    """Get comprehensive health overview for a person."""
    person = await db.get(Person, person_id)
    if not person:
        return {"error": "Person not found"}

    now = datetime.now()
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)

    # Blood sugar stats (30 days)
    bs_stmt = (
        select(
            func.count(BloodSugarRecord.id).label("count"),
            func.avg(BloodSugarRecord.value).label("avg"),
            func.min(BloodSugarRecord.value).label("min"),
            func.max(BloodSugarRecord.value).label("max"),
            func.sum(func.cast(BloodSugarRecord.is_alert, int)).label("alerts"),
        )
        .where(BloodSugarRecord.person_id == person_id)
        .where(BloodSugarRecord.measured_at >= thirty_days_ago)
    )
    bs_result = await db.execute(bs_stmt)
    bs_stats = bs_result.one()

    # Latest blood sugar
    bs_latest_stmt = (
        select(BloodSugarRecord)
        .where(BloodSugarRecord.person_id == person_id)
        .order_by(BloodSugarRecord.measured_at.desc())
        .limit(1)
    )
    bs_latest_result = await db.execute(bs_latest_stmt)
    bs_latest = bs_latest_result.scalar_one_or_none()

    # BP stats (30 days)
    bp_stmt = (
        select(
            func.count(BloodPressureRecord.id).label("count"),
            func.avg(BloodPressureRecord.systolic).label("avg_sys"),
            func.avg(BloodPressureRecord.diastolic).label("avg_dia"),
            func.avg(BloodPressureRecord.heart_rate).label("avg_hr"),
            func.sum(func.cast(BloodPressureRecord.is_alert, int)).label("alerts"),
        )
        .where(BloodPressureRecord.person_id == person_id)
        .where(BloodPressureRecord.measured_at >= thirty_days_ago)
    )
    bp_result = await db.execute(bp_stmt)
    bp_stats = bp_result.one()

    # Latest BP
    bp_latest_stmt = (
        select(BloodPressureRecord)
        .where(BloodPressureRecord.person_id == person_id)
        .order_by(BloodPressureRecord.measured_at.desc())
        .limit(1)
    )
    bp_latest_result = await db.execute(bp_latest_stmt)
    bp_latest = bp_latest_result.scalar_one_or_none()

    # Active medication plans
    med_stmt = (
        select(MedicationPlan)
        .options(selectinload(MedicationPlan.medication))
        .where(MedicationPlan.person_id == person_id)
        .where(MedicationPlan.is_active == True)
    )
    med_result = await db.execute(med_stmt)
    active_meds = med_result.scalars().all()

    # Recent visits (7 days)
    visit_stmt = (
        select(Visit)
        .where(Visit.person_id == person_id)
        .where(Visit.visit_date >= seven_days_ago.date())
        .order_by(Visit.visit_date.desc())
    )
    visit_result = await db.execute(visit_stmt)
    recent_visits = visit_result.scalars().all()

    # Upcoming visits (next 30 days)
    upcoming_stmt = (
        select(Visit)
        .where(Visit.person_id == person_id)
        .where(Visit.visit_date > now.date())
        .where(Visit.visit_date <= (now + timedelta(days=30)).date())
        .order_by(Visit.visit_date.asc())
    )
    upcoming_result = await db.execute(upcoming_stmt)
    upcoming_visits = upcoming_result.scalars().all()

    # Weekly trend (blood sugar - last 7 days vs previous 7 days)
    prev_week = seven_days_ago - timedelta(days=7)
    bs_week_stmt = (
        select(func.avg(BloodSugarRecord.value))
        .where(BloodSugarRecord.person_id == person_id)
        .where(BloodSugarRecord.measured_at >= seven_days_ago)
    )
    bs_prev_week_stmt = (
        select(func.avg(BloodSugarRecord.value))
        .where(BloodSugarRecord.person_id == person_id)
        .where(BloodSugarRecord.measured_at >= prev_week)
        .where(BloodSugarRecord.measured_at < seven_days_ago)
    )
    bs_week_avg = (await db.execute(bs_week_stmt)).scalar()
    bs_prev_week_avg = (await db.execute(bs_prev_week_stmt)).scalar()

    return {
        "person": {
            "id": person.id,
            "name": person.name,
            "gender": person.gender,
            "birth_date": person.birth_date,
            "height_cm": person.height_cm,
            "weight_kg": person.weight_kg,
            "blood_type": person.blood_type,
            "disease_tags": person.disease_tags,
        },
        "blood_sugar": {
            "count_30d": bs_stats.count or 0,
            "avg_30d": round(float(bs_stats.avg), 1) if bs_stats.avg else None,
            "min_30d": round(float(bs_stats.min), 1) if bs_stats.min else None,
            "max_30d": round(float(bs_stats.max), 1) if bs_stats.max else None,
            "alerts_30d": bs_stats.alerts or 0,
            "latest": {
                "value": bs_latest.value,
                "measured_at": bs_latest.measured_at.isoformat(),
                "meal_context": bs_latest.meal_context,
            } if bs_latest else None,
            "trend": {
                "this_week": round(float(bs_week_avg), 1) if bs_week_avg else None,
                "last_week": round(float(bs_prev_week_avg), 1) if bs_prev_week_avg else None,
                "change": round(float(bs_week_avg - bs_prev_week_avg), 1) if bs_week_avg and bs_prev_week_avg else None,
            },
        },
        "blood_pressure": {
            "count_30d": bp_stats.count or 0,
            "avg_systolic": round(float(bp_stats.avg_sys), 1) if bp_stats.avg_sys else None,
            "avg_diastolic": round(float(bp_stats.avg_dia), 1) if bp_stats.avg_dia else None,
            "avg_heart_rate": round(float(bp_stats.avg_hr), 1) if bp_stats.avg_hr else None,
            "alerts_30d": bp_stats.alerts or 0,
            "latest": {
                "systolic": bp_latest.systolic,
                "diastolic": bp_latest.diastolic,
                "heart_rate": bp_latest.heart_rate,
                "measured_at": bp_latest.measured_at.isoformat(),
                "grade": grade_bp(bp_latest.systolic, bp_latest.diastolic),
                "hr_grade": grade_heart_rate(bp_latest.heart_rate),
            } if bp_latest else None,
            "avg_grade": grade_bp(
                round(float(bp_stats.avg_sys)) if bp_stats.avg_sys else 0,
                round(float(bp_stats.avg_dia)) if bp_stats.avg_dia else 0,
            ) if bp_stats.avg_sys else None,
        },
        "medications": {
            "active_count": len(active_meds),
            "plans": [
                {
                    "id": plan.id,
                    "name": plan.medication.name if plan.medication else f"药品#{plan.medication_id}",
                    "dosage": plan.dosage,
                    "frequency": plan.frequency,
                }
                for plan in active_meds
            ],
        },
        "visits": {
            "recent_count": len(recent_visits),
            "upcoming_count": len(upcoming_visits),
            "upcoming": [
                {
                    "id": v.id,
                    "hospital": v.hospital,
                    "visit_date": v.visit_date.isoformat() if v.visit_date else None,
                    "diagnosis": v.diagnosis,
                }
                for v in upcoming_visits
            ],
        },
        "health_score": _calculate_health_score(bs_stats, bp_stats),
    }


def _calculate_health_score(bs_stats, bp_stats) -> dict:
    """Calculate a simple health score (0-100)."""
    score = 100
    issues = []

    # Blood sugar scoring
    if bs_stats.avg:
        avg_bs = float(bs_stats.avg)
        if avg_bs > 7.8:
            score -= 20
            issues.append("血糖偏高")
        elif avg_bs > 6.1:
            score -= 10
            issues.append("血糖偏高")

    if bs_stats.alerts and bs_stats.alerts > 0:
        score -= min(bs_stats.alerts * 5, 20)

    # BP scoring
    if bp_stats.avg_sys:
        avg_sys = float(bp_stats.avg_sys)
        avg_dia = float(bp_stats.avg_dia)
        if avg_sys >= 140 or avg_dia >= 90:
            score -= 20
            issues.append("血压偏高")
        elif avg_sys >= 130 or avg_dia >= 85:
            score -= 10
            issues.append("血压偏高")

    if bp_stats.alerts and bp_stats.alerts > 0:
        score -= min(bp_stats.alerts * 5, 20)

    score = max(0, score)

    if score >= 90:
        level = "优秀"
        color = "green"
    elif score >= 70:
        level = "良好"
        color = "blue"
    elif score >= 50:
        level = "一般"
        color = "yellow"
    else:
        level = "需关注"
        color = "red"

    return {
        "score": score,
        "level": level,
        "color": color,
        "issues": issues,
    }

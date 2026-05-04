"""Medication reminder service — logic for due medications."""

from datetime import date, datetime, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from chronocare.models.medication import MedicationLog, MedicationPlan


async def get_due_reminders(db: AsyncSession, person_id: int) -> list[dict]:
    """Get medications that are due today but not yet taken."""
    today = date.today()
    now = datetime.now()

    # Get active plans for this person
    stmt = (
        select(MedicationPlan)
        .options(selectinload(MedicationPlan.medication))
        .where(MedicationPlan.person_id == person_id)
        .where(MedicationPlan.is_active == True)
        .where(MedicationPlan.start_date <= today)
        .where(
            (MedicationPlan.end_date == None) | (MedicationPlan.end_date >= today)
        )
    )
    result = await db.execute(stmt)
    plans = result.scalars().all()

    # Get today's logs
    log_stmt = (
        select(MedicationLog)
        .where(MedicationLog.person_id == person_id)
        .where(MedicationLog.taken_at >= datetime.combine(today, time.min))
        .where(MedicationLog.taken_at <= datetime.combine(today, time.max))
    )
    log_result = await db.execute(log_stmt)
    taken_logs = {log.plan_id for log in log_result.scalars().all()}

    reminders = []
    for plan in plans:
        if plan.id in taken_logs:
            status = "taken"
        else:
            status = "pending"

        # Parse timing to determine reminder time slots
        timing_slots = _parse_timing(plan.timing or plan.frequency)

        reminders.append({
            "plan_id": plan.id,
            "medication_name": plan.medication.name if plan.medication else f"药品#{plan.medication_id}",
            "dosage": plan.dosage,
            "frequency": plan.frequency,
            "timing": plan.timing,
            "timing_slots": timing_slots,
            "status": status,
            "notes": plan.notes,
        })

    return reminders


async def mark_medication_taken(
    db: AsyncSession, plan_id: int, person_id: int, status: str = "taken"
) -> MedicationLog:
    """Mark a medication plan as taken for today."""
    log = MedicationLog(
        plan_id=plan_id,
        person_id=person_id,
        taken_at=datetime.now(),
        status=status,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


def _parse_timing(timing_str: str) -> list[str]:
    """Parse timing string into reminder time slots."""
    if not timing_str:
        return ["早上"]

    timing_lower = timing_str.lower()
    slots = []

    if any(k in timing_lower for k in ["早", "晨", "morning", "早饭", "早餐"]):
        slots.append("早上")
    if any(k in timing_lower for k in ["中", "午", "noon", "午饭", "午餐"]):
        slots.append("中午")
    if any(k in timing_lower for k in ["晚", "夜", "evening", "night", "晚饭", "晚餐"]):
        slots.append("晚上")
    if any(k in timing_lower for k in ["睡前", "bedtime"]):
        slots.append("睡前")

    return slots if slots else ["早上"]

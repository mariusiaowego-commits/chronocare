"""Medication Reminder API."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.services.medication_reminder import get_due_reminders, mark_medication_taken

router = APIRouter(prefix="/api/medication", tags=["medication-api"])


@router.get("/reminders")
async def medication_reminders(
    person_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Get today's medication reminders for a person."""
    reminders = await get_due_reminders(db, person_id)
    pending_count = sum(1 for r in reminders if r["status"] == "pending")

    return {
        "person_id": person_id,
        "total": len(reminders),
        "pending": pending_count,
        "taken": len(reminders) - pending_count,
        "reminders": reminders,
    }


@router.post("/reminders/{plan_id}/take")
async def take_medication(
    plan_id: int,
    person_id: int = Query(...),
    status: str = Query("taken"),
    db: AsyncSession = Depends(get_db),
):
    """Mark a medication as taken."""
    log = await mark_medication_taken(db, plan_id, person_id, status)
    return {
        "message": "Medication marked as taken",
        "log_id": log.id,
        "status": status,
    }

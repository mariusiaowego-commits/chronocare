"""Medication Reminder HTML pages."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.services.medication_reminder import get_due_reminders
from chronocare.services.person import list_persons

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent / "templates"))


@router.get("/medication/reminders", response_class=HTMLResponse)
async def medication_reminders_page(
    request: Request,
    person_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Medication reminders page showing today's due medications."""
    persons = await list_persons(db)

    selected = None
    if person_id:
        selected = next((p for p in persons if p.id == person_id), None)
    if not selected and persons:
        selected = persons[0]
        person_id = selected.id

    reminders = await get_due_reminders(db, person_id) if person_id else []
    pending_count = sum(1 for r in reminders if r["status"] == "pending")

    return templates.TemplateResponse(request, "medication/reminders.html", {
        "request": request,
        "persons": persons,
        "selected": selected,
        "selected_person_id": person_id,
        "reminders": reminders,
        "pending_count": pending_count,
        "now": datetime.now(),
    })

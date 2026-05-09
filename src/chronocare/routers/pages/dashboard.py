"""Dashboard HTML pages."""

from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.services.blood_sugar import list_blood_sugar
from chronocare.services.cardiac import list_bp
from chronocare.services.medication import list_plans
from chronocare.services.person import list_persons
from chronocare.services.trend_alert import get_all_alerts
from chronocare.services.visit import list_visits

router = APIRouter(tags=["pages"])
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, person_id: int | None = Query(None), db: AsyncSession = Depends(get_db)):
    persons = await list_persons(db)

    # Find selected person or default to first
    selected = None
    if person_id:
        selected = next((p for p in persons if p.id == person_id), None)
    if not selected and persons:
        selected = persons[0]
        person_id = selected.id

    # Fetch recent records for selected person
    bs_records = await list_blood_sugar(db, person_id) if person_id else []
    bp_records = await list_bp(db, person_id) if person_id else []
    plans = await list_plans(db, person_id) if person_id else []
    visits = await list_visits(db, person_id) if person_id else []
    alerts_data = (
        await get_all_alerts(person_id, db)
        if person_id
        else {"alerts": [], "alert_count": 0, "has_critical": False}
    )

    return templates.TemplateResponse(request, "dashboard.html", {
        "request": request,
        "persons": persons,
        "selected": selected,
        "selected_person_id": person_id,
        "bs_records": bs_records[:5],
        "bp_records": bp_records[:5],
        "plans": plans,
        "visits": visits[:3],
        "alerts": alerts_data["alerts"],
        "alert_count": alerts_data["alert_count"],
        "has_critical": alerts_data["has_critical"],
    })

"""Dashboard HTML pages."""

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.services.blood_sugar import list_blood_sugar
from chronocare.services.cardiac import list_bp
from chronocare.services.medication import list_plans
from chronocare.services.person import list_persons
from chronocare.services.visit import list_visits

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent / "templates"))


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

    return templates.TemplateResponse(request, "dashboard.html", {
        "request": request,
        "persons": persons,
        "selected": selected,
        "selected_person_id": person_id,
        "bs_records": bs_records[:5],
        "bp_records": bp_records[:5],
        "plans": plans,
        "visits": visits[:3],
    })

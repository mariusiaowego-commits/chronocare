"""Health Report HTML page."""

from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.services.health_report import generate_monthly_report, generate_weekly_report
from chronocare.services.person import list_persons

router = APIRouter(tags=["pages"])
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


@router.get("/health-report", response_class=HTMLResponse)
async def health_report_page(
    request: Request,
    person_id: int | None = Query(None),
    report_type: str = Query("weekly"),
    db: AsyncSession = Depends(get_db),
):
    persons = await list_persons(db)

    # Find selected person or default to first
    selected = None
    if person_id:
        selected = next((p for p in persons if p.id == person_id), None)
    if not selected and persons:
        selected = persons[0]
        person_id = selected.id

    report = None
    if selected:
        if report_type == "monthly":
            report = await generate_monthly_report(person_id, db)
        else:
            report = await generate_weekly_report(person_id, db)

    return templates.TemplateResponse(request, "health_report/index.html", {
        "request": request,
        "persons": persons,
        "selected": selected,
        "selected_person_id": person_id,
        "report": report,
        "report_type": report_type,
    })

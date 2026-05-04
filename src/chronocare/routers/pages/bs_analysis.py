"""Blood Sugar Analysis HTML page."""

from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.models.person import Person
from chronocare.services.bs_variability import analyze_blood_sugar_by_time, analyze_blood_sugar_variability

router = APIRouter(tags=["bs-analysis-pages"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent.parent / "templates"))


@router.get("/bs-analysis", response_class=HTMLResponse)
async def bs_analysis_page(
    request: Request,
    person_id: int = Query(None),
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Blood sugar analysis page."""
    persons = (await db.execute(select(Person).order_by(Person.name))).scalars().all()
    if not person_id and persons:
        person_id = persons[0].id

    analysis = None
    time_analysis = None
    if person_id:
        analysis = await analyze_blood_sugar_variability(person_id, days, db)
        time_analysis = await analyze_blood_sugar_by_time(person_id, days, db)

    return templates.TemplateResponse(
        request,
        "bs_analysis/index.html",
        {
            "persons": persons,
            "selected_person_id": person_id,
            "analysis": analysis,
            "time_analysis": time_analysis,
            "days": days,
        },
    )

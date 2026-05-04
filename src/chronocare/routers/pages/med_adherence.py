"""Medication Adherence HTML page."""

from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.models.person import Person
from chronocare.services.medication_adherence import analyze_medication_adherence

router = APIRouter(tags=["med-adherence-pages"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent.parent / "templates"))


@router.get("/med-adherence", response_class=HTMLResponse)
async def med_adherence_page(
    request: Request,
    person_id: int = Query(None),
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Medication adherence page."""
    persons = (await db.execute(select(Person).order_by(Person.name))).scalars().all()
    if not person_id and persons:
        person_id = persons[0].id

    analysis = None
    if person_id:
        analysis = await analyze_medication_adherence(person_id, days, db)

    return templates.TemplateResponse(
        request,
        "med_adherence/index.html",
        {
            "persons": persons,
            "selected_person_id": person_id,
            "analysis": analysis,
            "days": days,
        },
    )

"""BP Circadian Analysis HTML page."""

from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.models.person import Person
from chronocare.services.bp_circadian import analyze_bp_circadian

router = APIRouter(tags=["bp-circadian-pages"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent.parent / "templates"))


@router.get("/bp-circadian", response_class=HTMLResponse)
async def bp_circadian_page(
    request: Request,
    person_id: int = Query(None),
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
):
    """BP circadian rhythm analysis page."""
    persons = (await db.execute(select(Person).order_by(Person.name))).scalars().all()
    if not person_id and persons:
        person_id = persons[0].id

    analysis = None
    if person_id:
        analysis = await analyze_bp_circadian(person_id, days, db)

    return templates.TemplateResponse(
        request,
        "bp_circadian/index.html",
        {
            "persons": persons,
            "selected_person_id": person_id,
            "analysis": analysis,
            "days": days,
        },
    )

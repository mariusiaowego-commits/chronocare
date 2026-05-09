"""Reports HTML pages."""

from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.services.person import list_persons

router = APIRouter(tags=["pages"])
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


@router.get("/reports", response_class=HTMLResponse)
async def reports_page(
    request: Request,
    person_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Reports and statistics page."""
    persons = await list_persons(db)

    selected = None
    if person_id:
        selected = next((p for p in persons if p.id == person_id), None)
    if not selected and persons:
        selected = persons[0]
        person_id = selected.id

    return templates.TemplateResponse(request, "reports/index.html", {
        "request": request,
        "persons": persons,
        "selected": selected,
        "selected_person_id": person_id,
    })

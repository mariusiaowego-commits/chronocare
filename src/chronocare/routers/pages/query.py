"""Lab metric query page."""

from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.services.lab_query import run_lab_query
from chronocare.services.person import get_person, list_persons

router = APIRouter(tags=["pages"])
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


@router.get("/query", response_class=HTMLResponse)
async def lab_query_page(
    request: Request,
    q: str | None = Query(None),
    person_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    persons = await list_persons(db)
    if person_id is None and persons:
        person_id = persons[0].id
    selected = await get_person(db, person_id) if person_id else None

    result = None
    preview = None
    if q and q.strip() and selected:
        result = await run_lab_query(db, q.strip(), person_id=selected.id)
        if result.hit:
            preview = {
                "preview_url": f"/medical-records/{result.hit.record_id}/preview",
                "file_url": f"/medical-records/{result.hit.record_id}/file",
                "detail_url": f"/medical-records/{result.hit.record_id}",
            }
    examples = [
        "最近一次化验",
        "胆固醇",
        "肝功能",
        "糖化血红蛋白",
        "空腹血糖",
        "甘油三酯",
    ]
    return templates.TemplateResponse(
        request,
        "query/result.html",
        {
            "request": request,
            "q": q or "",
            "result": result,
            "preview": preview,
            "examples": examples,
            "persons": persons,
            "selected": selected,
        },
    )

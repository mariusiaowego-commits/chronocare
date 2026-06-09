"""Page routes for health report generation UI."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from chronocare.services import report_generation as report_svc

router = APIRouter(tags=["pages"])
TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/reports/modal/{person_id}")
async def report_modal(request: Request, person_id: int):
    """HTMX: render the report generation modal content."""
    from chronocare.database import async_session_factory
    from chronocare.services.person import get_person

    async with async_session_factory() as db:
        person = await get_person(db, person_id)
        reports = await report_svc.list_person_reports(db, person_id, limit=5)

    return templates.TemplateResponse(
        request, "report/modal.html", {"person": person, "reports": reports}
    )


@router.get("/reports/history/{person_id}")
async def report_history(request: Request, person_id: int):
    """HTMX: render report history list fragment."""
    from chronocare.database import async_session_factory

    async with async_session_factory() as db:
        reports = await report_svc.list_person_reports(db, person_id, limit=20)

    return templates.TemplateResponse(
        request, "report/history.html", {"reports": reports, "person_id": person_id}
    )


@router.get("/reports/status/{report_id}")
async def report_status(request: Request, report_id: int):
    """HTMX: poll report generation status."""
    from chronocare.database import async_session_factory

    async with async_session_factory() as db:
        report = await report_svc.get_report(db, report_id)

    return templates.TemplateResponse(
        request, "report/status.html", {"report": report}
    )

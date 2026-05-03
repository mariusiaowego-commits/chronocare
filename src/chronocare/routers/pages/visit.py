"""Visit HTML pages."""

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.schemas.visit import VisitCreate
from chronocare.services.person import list_persons
from chronocare.services.visit import create_visit, list_visits

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent / "templates"))


@router.get("/visits", response_class=HTMLResponse)
async def visit_list(request: Request, person_id: int | None = Query(None), db: AsyncSession = Depends(get_db)):
    visits = await list_visits(db, person_id)
    persons = await list_persons(db)
    return templates.TemplateResponse(request, "visit/list.html", {
        "request": request, "visits": visits, "persons": persons, "selected_person_id": person_id,
    })


@router.get("/visits/new", response_class=HTMLResponse)
async def visit_new(request: Request, person_id: int | None = Query(None), db: AsyncSession = Depends(get_db)):
    persons = await list_persons(db)
    return templates.TemplateResponse(request, "visit/form.html", {
        "request": request, "persons": persons, "selected_person_id": person_id,
    })


@router.post("/visits/new", response_class=HTMLResponse)
async def visit_create(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()
    data = VisitCreate(
        person_id=int(form["person_id"]),
        visit_date=form["visit_date"],
        hospital=form.get("hospital") or None,
        department=form.get("department") or None,
        doctor=form.get("doctor") or None,
        visit_type=form.get("visit_type") or None,
        chief_complaint=form.get("chief_complaint") or None,
        diagnosis=form.get("diagnosis") or None,
        prescription=form.get("prescription") or None,
        doctor_advice=form.get("doctor_advice") or None,
        next_followup_date=form.get("next_followup_date") or None,
    )
    await create_visit(db, data)
    return RedirectResponse(url=f"/visits?person_id={data.person_id}", status_code=303)

"""Person HTML pages."""

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.schemas.person import PersonCreate, PersonUpdate
from chronocare.services.person import create_person, get_person, list_persons, update_person

router = APIRouter(tags=["pages"])
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


@router.get("/persons", response_class=HTMLResponse)
async def person_list(request: Request, db: AsyncSession = Depends(get_db)):
    persons = await list_persons(db)
    return templates.TemplateResponse(request, "person/list.html", {"request": request, "persons": persons})


@router.get("/persons/new", response_class=HTMLResponse)
async def person_new(request: Request):
    return templates.TemplateResponse(request, "person/form.html", {"request": request, "person": None})


@router.post("/persons/new", response_class=HTMLResponse)
async def person_create(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()
    data = PersonCreate(
        name=form["name"],
        gender=form.get("gender") or None,
        birth_date=form.get("birth_date") or None,
        height_cm=float(form["height_cm"]) if form.get("height_cm") else None,
        weight_kg=float(form["weight_kg"]) if form.get("weight_kg") else None,
        blood_type=form.get("blood_type") or None,
        notes=form.get("notes") or None,
    )
    person = await create_person(db, data)
    return RedirectResponse(url=f"/persons/{person.id}", status_code=303)


@router.get("/persons/{person_id}", response_class=HTMLResponse)
async def person_detail(request: Request, person_id: int, db: AsyncSession = Depends(get_db)):
    person = await get_person(db, person_id)
    if person is None:
        return HTMLResponse("Not found", status_code=404)
    return templates.TemplateResponse(request, "person/detail.html", {"request": request, "person": person})


@router.get("/persons/{person_id}/edit", response_class=HTMLResponse)
async def person_edit(request: Request, person_id: int, db: AsyncSession = Depends(get_db)):
    person = await get_person(db, person_id)
    if person is None:
        return HTMLResponse("Not found", status_code=404)
    return templates.TemplateResponse(request, "person/form.html", {"request": request, "person": person})


@router.post("/persons/{person_id}/edit", response_class=HTMLResponse)
async def person_update(request: Request, person_id: int, db: AsyncSession = Depends(get_db)):
    form = await request.form()
    data = PersonUpdate(
        name=form["name"],
        gender=form.get("gender") or None,
        birth_date=form.get("birth_date") or None,
        height_cm=float(form["height_cm"]) if form.get("height_cm") else None,
        weight_kg=float(form["weight_kg"]) if form.get("weight_kg") else None,
        blood_type=form.get("blood_type") or None,
        preferred_hospital=form.get("preferred_hospital") or None,
        primary_doctor=form.get("primary_doctor") or None,
        notes=form.get("notes") or None,
    )
    updated = await update_person(db, person_id, data)
    if updated is None:
        return HTMLResponse("Not found", status_code=404)
    return RedirectResponse(url=f"/persons/{person_id}", status_code=303)

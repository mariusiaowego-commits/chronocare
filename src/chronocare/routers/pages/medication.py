"""Medication HTML pages."""

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.schemas.medication import MedicationCreate, MedicationPlanCreate
from chronocare.services.medication import create_medication, create_plan, list_medications, list_plans
from chronocare.services.person import list_persons

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent / "templates"))


@router.get("/medication", response_class=HTMLResponse)
async def medication_list(request: Request, person_id: int | None = Query(None), db: AsyncSession = Depends(get_db)):
    plans = await list_plans(db, person_id)
    medications = await list_medications(db)
    persons = await list_persons(db)
    return templates.TemplateResponse("medication/list.html", {
        "request": request, "plans": plans, "medications": medications,
        "persons": persons, "selected_person_id": person_id,
    })


@router.get("/medication/new", response_class=HTMLResponse)
async def medication_new(request: Request, person_id: int | None = Query(None), db: AsyncSession = Depends(get_db)):
    medications = await list_medications(db)
    persons = await list_persons(db)
    return templates.TemplateResponse("medication/form.html", {
        "request": request, "medications": medications, "persons": persons, "selected_person_id": person_id,
    })


@router.post("/medication/new", response_class=HTMLResponse)
async def medication_create(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()
    data = MedicationPlanCreate(
        person_id=int(form["person_id"]),
        medication_id=int(form["medication_id"]),
        dosage=form["dosage"],
        frequency=form["frequency"],
        timing=form.get("timing") or None,
        start_date=form["start_date"],
        end_date=form.get("end_date") or None,
        is_active=form.get("is_active") == "on",
        notes=form.get("notes") or None,
    )
    await create_plan(db, data)
    return RedirectResponse(url=f"/medication?person_id={data.person_id}", status_code=303)


@router.get("/medication/meds/new", response_class=HTMLResponse)
async def med_new(request: Request):
    return templates.TemplateResponse("medication/med_form.html", {"request": request})


@router.post("/medication/meds/new", response_class=HTMLResponse)
async def med_create(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()
    data = MedicationCreate(
        name=form["name"],
        generic_name=form.get("generic_name") or None,
        specification=form.get("specification") or None,
        category=form.get("category") or None,
        usage_description=form.get("usage_description") or None,
        side_effects=form.get("side_effects") or None,
        storage_notes=form.get("storage_notes") or None,
        notes=form.get("notes") or None,
    )
    await create_medication(db, data)
    return RedirectResponse(url="/medication", status_code=303)

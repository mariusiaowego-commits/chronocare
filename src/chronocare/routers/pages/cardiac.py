"""Cardiac HTML pages."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.schemas.cardiac import BloodPressureCreate
from chronocare.services.cardiac import create_bp, list_bp
from chronocare.services.person import list_persons

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent / "templates"))


@router.get("/cardiac", response_class=HTMLResponse)
async def cardiac_list(request: Request, person_id: int | None = Query(None), db: AsyncSession = Depends(get_db)):
    bp_records = await list_bp(db, person_id)
    persons = await list_persons(db)
    return templates.TemplateResponse(request, "cardiac/list.html", {
        "request": request, "bp_records": bp_records,
        "persons": persons, "selected_person_id": person_id,
    })


@router.get("/cardiac/bp/new", response_class=HTMLResponse)
async def bp_new(request: Request, person_id: int | None = Query(None), db: AsyncSession = Depends(get_db)):
    persons = await list_persons(db)
    return templates.TemplateResponse(request, "cardiac/bp_form.html", {
        "request": request, "persons": persons, "selected_person_id": person_id,
    })


@router.post("/cardiac/bp/new", response_class=HTMLResponse)
async def bp_create(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()
    # Combine date + time into datetime
    date_str = form["record_date"]
    time_str = form.get("record_time") or "00:00"
    measured_at = datetime.fromisoformat(f"{date_str}T{time_str}")

    data = BloodPressureCreate(
        person_id=int(form["person_id"]),
        measured_at=measured_at,
        systolic=int(form["systolic"]),
        diastolic=int(form["diastolic"]),
        heart_rate=int(form["heart_rate"]) if form.get("heart_rate") else None,
        notes=form.get("notes") or None,
    )
    await create_bp(db, data)
    return RedirectResponse(url=f"/cardiac?person_id={data.person_id}", status_code=303)

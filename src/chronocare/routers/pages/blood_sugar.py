"""Blood sugar HTML pages."""

from datetime import date, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.schemas.blood_sugar import BloodSugarCreate
from chronocare.services.blood_sugar import create_blood_sugar, list_blood_sugar
from chronocare.services.person import list_persons

router = APIRouter(tags=["pages"])
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


def _bs_status_classes(value: float) -> str:
    if value > 11.1:
        return "text-red-600"
    if value > 7.8:
        return "text-amber-500"
    if value < 3.9:
        return "text-blue-600"
    return "text-teal-600"


@router.get("/blood-sugar", response_class=HTMLResponse)
async def blood_sugar_list(request: Request, person_id: int | None = Query(None), db: AsyncSession = Depends(get_db)):
    records = await list_blood_sugar(db, person_id)
    persons = await list_persons(db)

    # Sort records by date descending
    records = sorted(records, key=lambda r: r.measured_at, reverse=True)

    # Build chart data: last 14 data points for selected person
    chart_labels = []
    chart_values = []
    if person_id:
        all_for_person = await list_blood_sugar(db, person_id)
        all_for_person = sorted(all_for_person, key=lambda r: r.measured_at)[-14:]
        chart_labels = [r.measured_at.strftime("%m-%d") for r in all_for_person]
        chart_values = [r.value for r in all_for_person]

    return templates.TemplateResponse(request, "blood_sugar/list.html", {
        "request": request,
        "records": records,
        "persons": persons,
        "selected_person_id": person_id,
        "chart_labels": chart_labels,
        "chart_values": chart_values,
    })


@router.get("/blood-sugar/new", response_class=HTMLResponse)
async def blood_sugar_new(request: Request, person_id: int | None = Query(None), db: AsyncSession = Depends(get_db)):
    persons = await list_persons(db)
    return templates.TemplateResponse(request, "blood_sugar/form.html", {
        "request": request,
        "persons": persons,
        "selected_person_id": person_id,
        "today": date.today().isoformat(),
    })


@router.post("/blood-sugar/new", response_class=HTMLResponse)
async def blood_sugar_create(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()
    date_str = form["record_date"]
    time_str = form.get("record_time") or "00:00"
    measured_at = datetime.fromisoformat(f"{date_str}T{time_str}")

    data = BloodSugarCreate(
        person_id=int(form["person_id"]),
        measured_at=measured_at,
        value=float(form["value"]),
        meal_context=form.get("meal_context") or None,
        notes=form.get("notes") or None,
        is_alert=form.get("is_alert") == "on",
    )
    await create_blood_sugar(db, data)
    resp = RedirectResponse(url=f"/blood-sugar?person_id={data.person_id}", status_code=303)
    resp.headers["X-Toast"] = "血糖已记录|success"
    return resp

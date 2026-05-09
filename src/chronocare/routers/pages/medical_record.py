"""Medical Record HTML pages."""

from pathlib import Path

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.schemas.medical_record import MedicalRecordCreate
from chronocare.services.medical_record import (
    create_medical_record,
    delete_medical_record,
    get_medical_record,
    list_medical_records,
    process_doctor_order,
    process_lab_report,
    process_ocr,
    upload_image,
)
from chronocare.services.person import list_persons

router = APIRouter(tags=["pages"])

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


@router.get("/medical-records", response_class=HTMLResponse)
async def medical_record_list(
    request: Request,
    person_id: int | None = Query(None),
    record_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Medical records list page."""
    records = await list_medical_records(db, person_id, record_type)
    persons = await list_persons(db)
    return templates.TemplateResponse(request, "medical_record/list.html", {
        "request": request,
        "records": records,
        "persons": persons,
        "selected_person_id": person_id,
        "selected_record_type": record_type,
    })


@router.get("/medical-records/new", response_class=HTMLResponse)
async def medical_record_new(
    request: Request,
    person_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """New medical record form."""
    persons = await list_persons(db)
    return templates.TemplateResponse(request, "medical_record/form.html", {
        "request": request,
        "persons": persons,
        "selected_person_id": person_id,
    })


@router.post("/medical-records/new", response_class=HTMLResponse)
async def medical_record_create(request: Request, db: AsyncSession = Depends(get_db)):
    """Create a new medical record."""
    form = await request.form()
    data = MedicalRecordCreate(
        person_id=int(form["person_id"]),
        record_type=form["record_type"],
        visit_date=form.get("visit_date") or None,
        hospital=form.get("hospital") or None,
        department=form.get("department") or None,
        doctor=form.get("doctor") or None,
        notes=form.get("notes") or None,
    )
    record = await create_medical_record(db, data)
    return RedirectResponse(f"/medical-records/{record.id}", status_code=303)


@router.get("/medical-records/{record_id}", response_class=HTMLResponse)
async def medical_record_detail(request: Request, record_id: int, db: AsyncSession = Depends(get_db)):
    """Medical record detail page."""
    record = await get_medical_record(db, record_id)
    if record is None:
        return RedirectResponse("/medical-records", status_code=302)
    return templates.TemplateResponse(request, "medical_record/detail.html", {
        "request": request,
        "record": record,
    })


@router.get("/medical-records/{record_id}/edit", response_class=HTMLResponse)
async def medical_record_edit_form(request: Request, record_id: int, db: AsyncSession = Depends(get_db)):
    """Edit medical record form."""
    record = await get_medical_record(db, record_id)
    if record is None:
        return RedirectResponse("/medical-records", status_code=302)
    persons = await list_persons(db)
    return templates.TemplateResponse(request, "medical_record/form.html", {
        "request": request,
        "record": record,
        "persons": persons,
        "selected_person_id": record.person_id,
    })


@router.post("/medical-records/{record_id}/delete", response_class=HTMLResponse)
async def medical_record_delete(request: Request, record_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a medical record."""
    await delete_medical_record(db, record_id)
    return RedirectResponse("/medical-records", status_code=303)


@router.post("/medical-records/{record_id}/upload", response_class=HTMLResponse)
async def medical_record_upload(
    request: Request,
    record_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload an image for a medical record."""
    # Save uploaded file temporarily
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)

    await upload_image(db, record_id, temp_path)

    # Clean up temp file
    import os
    os.remove(temp_path)

    return RedirectResponse(f"/medical-records/{record_id}", status_code=303)


@router.post("/medical-records/{record_id}/ocr", response_class=HTMLResponse)
async def medical_record_ocr(request: Request, record_id: int, db: AsyncSession = Depends(get_db)):
    """Process OCR on a medical record."""
    await process_ocr(db, record_id)
    return RedirectResponse(f"/medical-records/{record_id}", status_code=303)


@router.post("/medical-records/{record_id}/process-lab", response_class=HTMLResponse)
async def medical_record_process_lab(request: Request, record_id: int, db: AsyncSession = Depends(get_db)):
    """Process lab report."""
    await process_lab_report(db, record_id)
    return RedirectResponse(f"/medical-records/{record_id}", status_code=303)


@router.post("/medical-records/{record_id}/process-order", response_class=HTMLResponse)
async def medical_record_process_order(request: Request, record_id: int, db: AsyncSession = Depends(get_db)):
    """Process doctor's order."""
    await process_doctor_order(db, record_id)
    return RedirectResponse(f"/medical-records/{record_id}", status_code=303)

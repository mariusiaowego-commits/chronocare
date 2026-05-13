"""Medical Record API — CRUD + OCR processing."""

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.schemas.medical_record import (
    MedicalRecordCreate,
    MedicalRecordRead,
    MedicalRecordUpdate,
)
from chronocare.services.medical_record import (
    create_medical_record,
    delete_medical_record,
    get_medical_record,
    list_medical_records,
    process_doctor_order,
    process_lab_report,
    process_ocr,
    update_medical_record,
    upload_image,
)

router = APIRouter(prefix="/api/medical-records", tags=["Medical Records"])

_SORT_COLS = frozenset(["id", "record_date", "record_type", "created_at"])


@router.get("", response_model=list[MedicalRecordRead])
async def api_list(
    person_id: int | None = Query(None),
    record_type: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sort_by: str | None = Query(None),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    """List medical records, optionally filtered by person_id and record_type."""
    rows = await list_medical_records(db, person_id, record_type)
    if sort_by and sort_by in _SORT_COLS:
        reverse = sort_order == "desc"
        rows = sorted(rows, key=lambda r: getattr(r, sort_by) or "", reverse=reverse)
    return rows[skip : skip + limit]


@router.get("/{record_id}", response_model=MedicalRecordRead)
async def api_get(record_id: int, db: AsyncSession = Depends(get_db)):
    """Get a medical record by ID."""
    record = await get_medical_record(db, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.post("", response_model=MedicalRecordRead, status_code=201)
async def api_create(data: MedicalRecordCreate, db: AsyncSession = Depends(get_db)):
    """Create a new medical record."""
    return await create_medical_record(db, data)


@router.patch("/{record_id}", response_model=MedicalRecordRead)
async def api_update(record_id: int, data: MedicalRecordUpdate, db: AsyncSession = Depends(get_db)):
    """Update a medical record."""
    record = await update_medical_record(db, record_id, data)
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.delete("/{record_id}", status_code=204)
async def api_delete(record_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a medical record."""
    if not await delete_medical_record(db, record_id):
        raise HTTPException(status_code=404, detail="Record not found")


@router.post("/{record_id}/upload")
async def api_upload_image(record_id: int, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """Upload an image for a medical record."""
    import os

    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)

    record = await upload_image(db, record_id, temp_path)
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")

    os.remove(temp_path)

    return {"message": "Image uploaded successfully", "image_path": record.image_path}


@router.post("/{record_id}/process")
async def api_process_record(record_id: int, db: AsyncSession = Depends(get_db)):
    """Unified endpoint — auto-routes to the right handler based on record_type.

    - lab_report  → process_lab_report
    - doctor_order / prescription → process_doctor_order
    - medical_record              → process_ocr
    """
    record = await get_medical_record(db, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")

    rt = record.record_type
    if rt == "lab_report":
        result = await process_lab_report(db, record_id)
    elif rt in ("doctor_order", "prescription"):
        result = await process_doctor_order(db, record_id)
    else:
        result = await process_ocr(db, record_id)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{record_id}/ocr")
async def api_process_ocr(record_id: int, db: AsyncSession = Depends(get_db)):
    """Process OCR on a medical record's image."""
    result = await process_ocr(db, record_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{record_id}/process-lab")
async def api_process_lab_report(record_id: int, db: AsyncSession = Depends(get_db)):
    """Process a lab report image and extract structured data."""
    result = await process_lab_report(db, record_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{record_id}/process-order")
async def api_process_doctor_order(record_id: int, db: AsyncSession = Depends(get_db)):
    """Process a doctor's order image and extract structured data."""
    result = await process_doctor_order(db, record_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

"""Medical record service — real OCR + LLM pipeline."""

import os
import shutil
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.models.medical_record import MedicalRecord
from chronocare.schemas.medical_record import MedicalRecordCreate, MedicalRecordUpdate
from chronocare.services.ocr_engine import extract_text, is_ocr_available
from chronocare.services.ocr_parser import parse_ocr_text

# Upload directory
UPLOAD_DIR = Path("uploads/medical_records")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


async def create_medical_record(db: AsyncSession, data: MedicalRecordCreate) -> MedicalRecord:
    """Create a new medical record."""
    record = MedicalRecord(**data.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def get_medical_record(db: AsyncSession, record_id: int) -> MedicalRecord | None:
    """Get a medical record by ID."""
    result = await db.execute(select(MedicalRecord).where(MedicalRecord.id == record_id))
    return result.scalar_one_or_none()


async def list_medical_records(
    db: AsyncSession, person_id: int | None = None, record_type: str | None = None
) -> list[MedicalRecord]:
    """List medical records, optionally filtered by person_id and record_type."""
    stmt = select(MedicalRecord).order_by(MedicalRecord.created_at.desc())
    if person_id is not None:
        stmt = stmt.where(MedicalRecord.person_id == person_id)
    if record_type is not None:
        stmt = stmt.where(MedicalRecord.record_type == record_type)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_medical_record(
    db: AsyncSession, record_id: int, data: MedicalRecordUpdate
) -> MedicalRecord | None:
    """Update a medical record."""
    record = await get_medical_record(db, record_id)
    if record is None:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(record, key, value)
    await db.commit()
    await db.refresh(record)
    return record


async def delete_medical_record(db: AsyncSession, record_id: int) -> bool:
    """Delete a medical record."""
    record = await get_medical_record(db, record_id)
    if record is None:
        return False
    if record.image_path and os.path.exists(record.image_path):
        os.remove(record.image_path)
    await db.delete(record)
    await db.commit()
    return True


async def upload_image(db: AsyncSession, record_id: int, file_path: str) -> MedicalRecord | None:
    """Upload an image for a medical record."""
    record = await get_medical_record(db, record_id)
    if record is None:
        return None

    dest_path = UPLOAD_DIR / f"{record_id}_{Path(file_path).name}"
    shutil.copy2(file_path, dest_path)

    record.image_path = str(dest_path)
    await db.commit()
    await db.refresh(record)
    return record


# ---------------------------------------------------------------------------
# OCR + LLM pipeline helpers
# ---------------------------------------------------------------------------


async def _ocr_and_parse(
    db: AsyncSession,
    record: MedicalRecord,
    record_type: str,
) -> dict[str, Any]:
    """Run OCR then LLM parsing; persist both ocr_text and structured field.

    Returns a dict that may contain:
      - ocr_text:      the raw OCR output (always present on success)
      - structured:    the LLM-parsed result (absent if LLM failed)
      - error:         friendly error message if OCR was unavailable

    The record is always committed before returning.
    """
    image_path = record.image_path

    # 1. OCR — Swift Vision
    if not await is_ocr_available():
        return {"error": "OCR服务不可用（Swift或vision_ocr.swift未找到）"}

    try:
        raw_text = await extract_text(image_path)
    except FileNotFoundError:
        return {"error": f"图片文件不存在: {image_path}"}
    except TimeoutError as exc:
        return {"error": f"OCR超时: {exc}"}
    except RuntimeError as exc:
        return {"error": f"OCR失败: {exc}"}

    # 2. Persist raw OCR text
    record.ocr_text = raw_text

    # 3. LLM structural parsing
    structured = await parse_ocr_text(raw_text, record_type)

    if "error" in structured:
        # LLM failed — keep ocr_text, mark structured as error marker
        record.structured_data = {"error": structured["error"]}
    else:
        record.structured_data = structured

    await db.commit()
    await db.refresh(record)

    return {
        "ocr_text": raw_text,
        "structured_data": record.structured_data,
    }


# ---------------------------------------------------------------------------
# Public OCR processing functions
# ---------------------------------------------------------------------------


async def process_ocr(db: AsyncSession, record_id: int) -> dict[str, Any]:
    """Run OCR + LLM parsing for a generic medical record.

    Pipeline: extract_text(image_path) → parse_ocr_text(raw_text, "medical_record")
    Stores: record.ocr_text + record.structured_data
    """
    record = await get_medical_record(db, record_id)
    if record is None:
        return {"error": "Record not found"}
    if not record.image_path:
        return {"error": "No image uploaded for this record"}

    return await _ocr_and_parse(db, record, "medical_record")


async def process_lab_report(db: AsyncSession, record_id: int) -> dict[str, Any]:
    """Run OCR + LLM parsing for a lab report.

    Pipeline: extract_text(image_path) → parse_ocr_text(raw_text, "lab_report")
    Stores: record.ocr_text + record.lab_results
    """
    record = await get_medical_record(db, record_id)
    if record is None:
        return {"error": "Record not found"}
    if not record.image_path:
        return {"error": "No image uploaded for this record"}

    image_path = record.image_path

    if not await is_ocr_available():
        return {"error": "OCR服务不可用（Swift或vision_ocr.swift未找到）"}

    try:
        raw_text = await extract_text(image_path)
    except FileNotFoundError:
        return {"error": f"图片文件不存在: {image_path}"}
    except TimeoutError as exc:
        return {"error": f"OCR超时: {exc}"}
    except RuntimeError as exc:
        return {"error": f"OCR失败: {exc}"}

    record.ocr_text = raw_text
    structured = await parse_ocr_text(raw_text, "lab_report")

    if "error" in structured:
        record.lab_results = {"error": structured["error"]}
    else:
        record.lab_results = structured

    await db.commit()
    await db.refresh(record)

    return {"lab_results": record.lab_results}


async def process_doctor_order(db: AsyncSession, record_id: int) -> dict[str, Any]:
    """Run OCR + LLM parsing for a doctor's order / prescription.

    Pipeline: extract_text(image_path) → parse_ocr_text(raw_text, "doctor_order")
    Stores: record.ocr_text + record.doctor_orders
    """
    record = await get_medical_record(db, record_id)
    if record is None:
        return {"error": "Record not found"}
    if not record.image_path:
        return {"error": "No image uploaded for this record"}

    image_path = record.image_path

    if not await is_ocr_available():
        return {"error": "OCR服务不可用（Swift或vision_ocr.swift未找到）"}

    try:
        raw_text = await extract_text(image_path)
    except FileNotFoundError:
        return {"error": f"图片文件不存在: {image_path}"}
    except TimeoutError as exc:
        return {"error": f"OCR超时: {exc}"}
    except RuntimeError as exc:
        return {"error": f"OCR失败: {exc}"}

    record.ocr_text = raw_text
    structured = await parse_ocr_text(raw_text, "doctor_order")

    if "error" in structured:
        record.doctor_orders = {"error": structured["error"]}
    else:
        record.doctor_orders = structured

    await db.commit()
    await db.refresh(record)

    return {"doctor_orders": record.doctor_orders}

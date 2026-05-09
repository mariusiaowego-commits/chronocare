"""Medical record service with OCR placeholder."""

import os
import shutil
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.models.medical_record import MedicalRecord
from chronocare.schemas.medical_record import MedicalRecordCreate, MedicalRecordUpdate

# Upload directory
UPLOAD_DIR = Path("uploads/medical_records")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


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
    # Delete associated image if exists
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

    # Copy file to upload directory
    dest_path = UPLOAD_DIR / f"{record_id}_{Path(file_path).name}"
    shutil.copy2(file_path, dest_path)

    record.image_path = str(dest_path)
    await db.commit()
    await db.refresh(record)
    return record


async def process_ocr(db: AsyncSession, record_id: int) -> dict[str, Any]:
    """Process OCR on a medical record's image (placeholder implementation).

    This is a placeholder that returns mock structured data.
    In production, integrate with PaddleOCR, Tesseract, or cloud OCR API.
    """
    record = await get_medical_record(db, record_id)
    if record is None:
        return {"error": "Record not found"}

    if not record.image_path:
        return {"error": "No image uploaded"}

    # Placeholder OCR result - in production, call actual OCR service
    mock_ocr_text = "这是OCR识别的占位文本。请集成实际OCR服务。"
    mock_structured_data = {
        "diagnosis": ["待OCR识别"],
        "symptoms": ["待OCR识别"],
        "treatment": "待OCR识别",
    }

    record.ocr_text = mock_ocr_text
    record.structured_data = mock_structured_data
    await db.commit()
    await db.refresh(record)

    return {
        "ocr_text": mock_ocr_text,
        "structured_data": mock_structured_data,
    }


async def process_lab_report(db: AsyncSession, record_id: int) -> dict[str, Any]:
    """Process a lab report image and extract structured lab results (placeholder).

    In production, this would parse OCR text to extract:
    - Test name
    - Value
    - Unit
    - Reference range
    - Status (normal/abnormal)
    """
    record = await get_medical_record(db, record_id)
    if record is None:
        return {"error": "Record not found"}

    if not record.image_path:
        return {"error": "No image uploaded"}

    # Placeholder lab results - in production, parse OCR text
    mock_lab_results = {
        "tests": [
            {
                "name": "空腹血糖",
                "value": "6.2",
                "unit": "mmol/L",
                "reference": "3.9-6.1",
                "status": "slightly_high",
            },
            {
                "name": "糖化血红蛋白",
                "value": "6.8",
                "unit": "%",
                "reference": "<6.5",
                "status": "slightly_high",
            },
        ],
        "summary": "血糖指标偏高，建议控制饮食",
    }

    record.record_type = "lab_report"
    record.lab_results = mock_lab_results
    record.ocr_text = "化验单OCR识别占位文本"
    await db.commit()
    await db.refresh(record)

    return {"lab_results": mock_lab_results}


async def process_doctor_order(db: AsyncSession, record_id: int) -> dict[str, Any]:
    """Process a doctor's order image and extract structured data (placeholder).

    In production, this would parse OCR text to extract:
    - Medications prescribed
    - Dosage and frequency
    - Duration
    - Special instructions
    """
    record = await get_medical_record(db, record_id)
    if record is None:
        return {"error": "Record not found"}

    if not record.image_path:
        return {"error": "No image uploaded"}

    # Placeholder doctor's orders - in production, parse OCR text
    mock_doctor_orders = {
        "medications": [
            {
                "name": "二甲双胍",
                "dosage": "500mg",
                "frequency": "每日两次",
                "duration": "长期",
                "notes": "餐后服用",
            },
        ],
        "lifestyle": ["控制饮食", "适量运动", "定期监测血糖"],
        "followup": "两周后复诊",
    }

    record.record_type = "doctor_order"
    record.doctor_orders = mock_doctor_orders
    record.ocr_text = "医嘱OCR识别占位文本"
    await db.commit()
    await db.refresh(record)

    return {"doctor_orders": mock_doctor_orders}

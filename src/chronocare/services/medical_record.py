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
# Output format normalization
# ---------------------------------------------------------------------------

# Status mapping from vision_analyze variants to template-expected values
_STATUS_MAP = {
    "abnormal": "high",
    "high": "high",
    "elevated": "high",
    "↑": "high",
    "偏高": "high",
    "明显偏高": "high",
    "abnormal_low": "low",
    "low": "low",
    "decreased": "low",
    "↓": "low",
    "偏低": "low",
    "明显偏低": "low",
    "borderline": "slightly_high",
    "mildly_high": "slightly_high",
    "slightly_high": "slightly_high",
    "略高": "slightly_high",
    "轻微偏高": "slightly_high",
    "borderline_low": "slightly_low",
    "mildly_low": "slightly_low",
    "slightly_low": "slightly_low",
    "略低": "slightly_low",
    "轻微偏低": "slightly_low",
    "normal": "normal",
    "within_range": "normal",
    "正常": "normal",
}


def _normalize_status(raw: Any) -> str:
    """Normalize status string to template-expected enum value."""
    if not raw or not isinstance(raw, str):
        return "normal"
    return _STATUS_MAP.get(raw.strip().lower(), "normal")


def _normalize_bool_status(is_abnormal: Any) -> str:
    """Convert boolean is_abnormal to status string."""
    if isinstance(is_abnormal, bool):
        return "high" if is_abnormal else "normal"
    return "normal"


def normalize_lab_results(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize lab_results to template-expected format.

    Template expects: {"tests": [{"name", "value", "unit", "reference", "status"}], "summary"}
    vision_analyze may return: {"lab_items": [{"item_name", "result", "reference_range", "is_abnormal"}]}
    """
    if data is None:
        return data
    if isinstance(data, dict) and "error" in data:
        return data

    # Handle top-level array → wrap in {"tests": [...]}
    if isinstance(data, list):
        data = {"tests": data}

    if not isinstance(data, dict):
        return data

    if "tests" in data:
        # Already correct format, just normalize status values
        for test in data["tests"]:
            if isinstance(test, dict):
                test["status"] = _normalize_status(test.get("status"))
        return data

    # Try common variant keys
    items = data.get("lab_items") or data.get("items") or data.get("lab_values")
    if not items and isinstance(data, list):
        items = data  # Top-level array

    if not items or not isinstance(items, list):
        return data

    tests = []
    for item in items:
        if not isinstance(item, dict):
            continue
        test = {
            "name": item.get("name") or item.get("item_name") or item.get("项目") or "",
            "value": str(item.get("value") or item.get("result") or item.get("结果") or ""),
            "unit": item.get("unit") or item.get("单位") or "",
            "reference": item.get("reference") or item.get("reference_range") or item.get("参考范围") or "",
        }
        # Status: try explicit status field, then boolean is_abnormal
        if "status" in item:
            test["status"] = _normalize_status(item["status"])
        elif "is_abnormal" in item:
            test["status"] = _normalize_bool_status(item["is_abnormal"])
        else:
            test["status"] = "normal"
        tests.append(test)

    result: dict[str, Any] = {"tests": tests}
    if "summary" in data:
        result["summary"] = data["summary"]
    return result


def normalize_doctor_orders(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize doctor_orders to template-expected format."""
    if data is None:
        return data
    if not isinstance(data, dict):
        return data
    if "error" in data:
        return data

    # Ensure all required keys exist
    normalized = {
        "medications": data.get("medications") or [],
        "lifestyle": data.get("lifestyle") or [],
        "followup": data.get("followup") or "未提及",
        "special_instructions": data.get("special_instructions") or "未提及",
    }
    return normalized


def normalize_structured_data(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize structured_data to template-expected format."""
    if data is None:
        return data
    if not isinstance(data, dict):
        return data
    if "error" in data:
        return data

    normalized = {
        "diagnosis": data.get("diagnosis") or [],
        "symptoms": data.get("symptoms") or [],
        "treatment": data.get("treatment") or "未提及",
        "followup": data.get("followup") or "未提及",
    }
    return normalized


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
    """Update a medical record with automatic format normalization."""
    record = await get_medical_record(db, record_id)
    if record is None:
        return None
    update_data = data.model_dump(exclude_unset=True)

    # Normalize structured fields before persisting
    if "lab_results" in update_data and update_data["lab_results"]:
        update_data["lab_results"] = normalize_lab_results(update_data["lab_results"])
    if "doctor_orders" in update_data and update_data["doctor_orders"]:
        update_data["doctor_orders"] = normalize_doctor_orders(update_data["doctor_orders"])
    if "structured_data" in update_data and update_data["structured_data"]:
        update_data["structured_data"] = normalize_structured_data(update_data["structured_data"])

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
        record.structured_data = normalize_structured_data(structured)

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
        record.lab_results = normalize_lab_results(structured)

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
        record.doctor_orders = normalize_doctor_orders(structured)

    await db.commit()
    await db.refresh(record)

    return {"doctor_orders": record.doctor_orders}

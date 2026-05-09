"""Medical record schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel


class MedicalRecordBase(BaseModel):
    person_id: int
    record_type: str  # 'medical_record', 'lab_report', 'prescription', 'doctor_order'
    visit_date: date | None = None
    hospital: str | None = None
    department: str | None = None
    doctor: str | None = None
    notes: str | None = None


class MedicalRecordCreate(MedicalRecordBase):
    pass


class MedicalRecordUpdate(BaseModel):
    record_type: str | None = None
    visit_date: date | None = None
    hospital: str | None = None
    department: str | None = None
    doctor: str | None = None
    ocr_text: str | None = None
    structured_data: dict[str, Any] | None = None
    doctor_orders: dict[str, Any] | None = None
    lab_results: dict[str, Any] | None = None
    notes: str | None = None


class MedicalRecordRead(MedicalRecordBase):
    id: int
    image_path: str | None = None
    ocr_text: str | None = None
    structured_data: dict[str, Any] | None = None
    doctor_orders: dict[str, Any] | None = None
    lab_results: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

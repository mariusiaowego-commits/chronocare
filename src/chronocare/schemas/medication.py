"""Pydantic schemas for Medication, Plan, Log, Prescription."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


# --- Medication ---

class MedicationBase(BaseModel):
    name: str
    generic_name: str | None = None
    specification: str | None = None
    category: str | None = None
    usage_description: str | None = None
    side_effects: str | None = None
    storage_notes: str | None = None
    notes: str | None = None


class MedicationCreate(MedicationBase):
    pass


class MedicationRead(MedicationBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# --- Medication Plan ---

class MedicationPlanBase(BaseModel):
    person_id: int
    medication_id: int
    dosage: str
    frequency: str  # daily, twice_daily, three_times_daily, weekly, as_needed
    timing: str | None = None
    start_date: date
    end_date: date | None = None
    is_active: bool = True
    notes: str | None = None


class MedicationPlanCreate(MedicationPlanBase):
    pass


class MedicationPlanUpdate(BaseModel):
    dosage: str | None = None
    frequency: str | None = None
    timing: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool | None = None
    notes: str | None = None


class MedicationPlanRead(MedicationPlanBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    medication: MedicationRead | None = None


# --- Medication Log ---

class MedicationLogBase(BaseModel):
    plan_id: int
    person_id: int
    taken_at: datetime
    status: str = "taken"  # taken, missed, adjusted, skipped
    actual_dosage: str | None = None
    notes: str | None = None


class MedicationLogCreate(MedicationLogBase):
    pass


class MedicationLogRead(MedicationLogBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# --- Prescription ---

class PrescriptionBase(BaseModel):
    person_id: int
    prescribed_date: date
    hospital: str | None = None
    doctor: str | None = None
    medications_json: dict
    next_refill_date: date | None = None
    notes: str | None = None


class PrescriptionCreate(PrescriptionBase):
    pass


class PrescriptionRead(PrescriptionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime

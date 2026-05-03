"""Pydantic schemas for BloodPressureRecord."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BloodPressureBase(BaseModel):
    person_id: int
    measured_at: datetime
    systolic: int
    diastolic: int
    heart_rate: int | None = None
    notes: str | None = None
    is_alert: bool = False


class BloodPressureCreate(BloodPressureBase):
    pass


class BloodPressureUpdate(BaseModel):
    measured_at: datetime | None = None
    systolic: int | None = None
    diastolic: int | None = None
    heart_rate: int | None = None
    notes: str | None = None
    is_alert: bool | None = None


class BloodPressureRead(BloodPressureBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime

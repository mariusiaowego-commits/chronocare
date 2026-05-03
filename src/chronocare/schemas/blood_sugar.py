"""Pydantic schemas for BloodSugarRecord."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BloodSugarBase(BaseModel):
    person_id: int
    measured_at: datetime
    value: float  # mmol/L
    meal_context: str | None = None  # fasting, before_meal, after_meal, bedtime, random
    notes: str | None = None
    is_alert: bool = False


class BloodSugarCreate(BloodSugarBase):
    pass


class BloodSugarUpdate(BaseModel):
    measured_at: datetime | None = None
    value: float | None = None
    meal_context: str | None = None
    notes: str | None = None
    is_alert: bool | None = None


class BloodSugarRead(BloodSugarBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime

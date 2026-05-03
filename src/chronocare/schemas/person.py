"""Pydantic schemas for Person and Condition."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


# --- Condition ---

class ConditionBase(BaseModel):
    name: str
    diagnosed_date: date | None = None
    diagnosed_by: str | None = None
    severity: str | None = None  # mild / moderate / severe
    status: str = "active"  # active / managed / resolved
    notes: str | None = None


class ConditionCreate(ConditionBase):
    pass


class ConditionRead(ConditionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    person_id: int
    created_at: datetime


# --- Person ---

class PersonBase(BaseModel):
    name: str
    gender: str | None = None  # M / F
    birth_date: date | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    blood_type: str | None = None
    allergies: list[str] | None = None
    emergency_contact: str | None = None
    preferred_hospital: str | None = None
    primary_doctor: str | None = None
    disease_tags: list[str] | None = None
    notes: str | None = None


class PersonCreate(PersonBase):
    pass


class PersonUpdate(BaseModel):
    name: str | None = None
    gender: str | None = None
    birth_date: date | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    blood_type: str | None = None
    allergies: list[str] | None = None
    emergency_contact: str | None = None
    preferred_hospital: str | None = None
    primary_doctor: str | None = None
    disease_tags: list[str] | None = None
    notes: str | None = None


class PersonRead(PersonBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    conditions: list[ConditionRead] = []

"""Pydantic schemas for Visit."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class VisitBase(BaseModel):
    person_id: int
    visit_date: date
    hospital: str | None = None
    department: str | None = None
    doctor: str | None = None
    visit_type: str | None = None  # initial, followup, emergency, checkup
    chief_complaint: str | None = None
    diagnosis: str | None = None
    prescription: str | None = None
    doctor_advice: str | None = None
    next_followup_date: date | None = None
    attachments: dict | None = None


class VisitCreate(VisitBase):
    pass


class VisitUpdate(BaseModel):
    visit_date: date | None = None
    hospital: str | None = None
    department: str | None = None
    doctor: str | None = None
    visit_type: str | None = None
    chief_complaint: str | None = None
    diagnosis: str | None = None
    prescription: str | None = None
    doctor_advice: str | None = None
    next_followup_date: date | None = None
    attachments: dict | None = None


class VisitRead(VisitBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime

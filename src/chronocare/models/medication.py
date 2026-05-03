"""Medication management models."""

from datetime import date, datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, JSON, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from chronocare.models.base import Base


class Medication(Base):
    """药品库"""

    __tablename__ = "medications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    generic_name: Mapped[str | None] = mapped_column(Text)
    specification: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(Text)
    usage_description: Mapped[str | None] = mapped_column(Text)
    side_effects: Mapped[str | None] = mapped_column(Text)
    storage_notes: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class MedicationPlan(Base):
    """用药计划"""

    __tablename__ = "medication_plans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id"), nullable=False)
    medication_id: Mapped[int] = mapped_column(ForeignKey("medications.id"), nullable=False)
    dosage: Mapped[str] = mapped_column(Text, nullable=False)
    frequency: Mapped[str] = mapped_column(Text, nullable=False)
    timing: Mapped[str | None] = mapped_column(Text)
    start_date: Mapped[date] = mapped_column(nullable=False)
    end_date: Mapped[date | None]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class MedicationLog(Base):
    """用药打卡记录"""

    __tablename__ = "medication_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("medication_plans.id"), nullable=False)
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id"), nullable=False)
    taken_at: Mapped[datetime] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(
        Text, CheckConstraint("status IN ('taken', 'missed', 'adjusted', 'skipped')"), default="taken"
    )
    actual_dosage: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Prescription(Base):
    """配药记录"""

    __tablename__ = "prescriptions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id"), nullable=False)
    prescribed_date: Mapped[date] = mapped_column(nullable=False)
    hospital: Mapped[str | None] = mapped_column(Text)
    doctor: Mapped[str | None] = mapped_column(Text)
    medications_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    next_refill_date: Mapped[date | None]
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

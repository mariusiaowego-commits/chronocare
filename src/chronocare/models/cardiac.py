"""Cardiac (blood pressure / heart rate) record model."""

from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from chronocare.models.base import Base


class BloodPressureRecord(Base):
    """血压/心率记录"""

    __tablename__ = "blood_pressure_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id"), nullable=False)
    measured_at: Mapped[datetime] = mapped_column(nullable=False)
    systolic: Mapped[int] = mapped_column(nullable=False)  # 收缩压
    diastolic: Mapped[int] = mapped_column(nullable=False)  # 舒张压
    heart_rate: Mapped[int | None]  # 心率
    notes: Mapped[str | None]
    is_alert: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    def __repr__(self) -> str:
        return f"<BloodPressureRecord(id={self.id}, {self.systolic}/{self.diastolic})>"

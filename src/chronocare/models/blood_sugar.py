"""Blood sugar record model."""

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from chronocare.models.base import Base


class BloodSugarRecord(Base):
    """血糖记录"""

    __tablename__ = "blood_sugar_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id"), nullable=False)
    measured_at: Mapped[datetime] = mapped_column(nullable=False)
    value: Mapped[float] = mapped_column(nullable=False)  # mmol/L
    meal_context: Mapped[str | None] = mapped_column(
        Text,
        CheckConstraint("meal_context IN ('fasting', 'before_meal', 'after_meal', 'bedtime', 'random')"),
    )
    notes: Mapped[str | None] = mapped_column(Text)
    is_alert: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    def __repr__(self) -> str:
        return f"<BloodSugarRecord(id={self.id}, value={self.value}, alert={self.is_alert})>"

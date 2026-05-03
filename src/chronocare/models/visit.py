"""Visit record model."""

from datetime import date, datetime

from sqlalchemy import CheckConstraint, ForeignKey, JSON, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from chronocare.models.base import Base


class Visit(Base):
    """就诊记录"""

    __tablename__ = "visits"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id"), nullable=False)
    visit_date: Mapped[date] = mapped_column(nullable=False)
    hospital: Mapped[str | None] = mapped_column(Text)
    department: Mapped[str | None] = mapped_column(Text)
    doctor: Mapped[str | None] = mapped_column(Text)
    visit_type: Mapped[str | None] = mapped_column(
        Text, CheckConstraint("visit_type IN ('initial', 'followup', 'emergency', 'checkup')")
    )
    chief_complaint: Mapped[str | None] = mapped_column(Text)
    diagnosis: Mapped[str | None] = mapped_column(Text)
    prescription: Mapped[str | None] = mapped_column(Text)
    doctor_advice: Mapped[str | None] = mapped_column(Text)
    next_followup_date: Mapped[date | None]
    attachments: Mapped[dict | None] = mapped_column(JSON)  # JSON array
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

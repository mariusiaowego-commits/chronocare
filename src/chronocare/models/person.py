"""Person and Condition models."""

from datetime import date, datetime

from sqlalchemy import JSON, CheckConstraint, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from chronocare.models.base import Base


class Person(Base):
    """老人档案"""

    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    gender: Mapped[str | None] = mapped_column(Text, CheckConstraint("gender IN ('M', 'F')"))
    birth_date: Mapped[date | None]
    height_cm: Mapped[float | None]
    weight_kg: Mapped[float | None]
    blood_type: Mapped[str | None] = mapped_column(Text)
    allergies: Mapped[dict | None] = mapped_column(JSON)  # JSON array
    emergency_contact: Mapped[str | None] = mapped_column(Text)
    preferred_hospital: Mapped[str | None] = mapped_column(Text)
    primary_doctor: Mapped[str | None] = mapped_column(Text)
    disease_tags: Mapped[dict | None] = mapped_column(JSON)  # JSON array
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    # Relationships
    conditions: Mapped[list["Condition"]] = relationship(back_populates="person", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Person(id={self.id}, name='{self.name}')>"


class Condition(Base):
    """慢性病/疾病记录"""

    __tablename__ = "conditions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)  # 如：2型糖尿病
    diagnosed_date: Mapped[date | None]
    diagnosed_by: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[str | None] = mapped_column(Text, CheckConstraint("severity IN ('mild', 'moderate', 'severe')"))
    status: Mapped[str] = mapped_column(
        Text, CheckConstraint("status IN ('active', 'managed', 'resolved')"), default="active"
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    person: Mapped["Person"] = relationship(back_populates="conditions")

    def __repr__(self) -> str:
        return f"<Condition(id={self.id}, name='{self.name}')>"

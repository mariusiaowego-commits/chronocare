"""Medical record model for OCR-processed documents."""

from datetime import date, datetime

from sqlalchemy import JSON, CheckConstraint, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from chronocare.models.base import Base


class MedicalRecord(Base):
    """就医记录 (OCR识别后的结构化存储)"""

    __tablename__ = "medical_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id"), nullable=False)
    record_type: Mapped[str] = mapped_column(
        Text,
        CheckConstraint("record_type IN ('medical_record', 'lab_report', 'prescription', 'doctor_order')"),
        nullable=False,
    )
    visit_date: Mapped[date | None]
    hospital: Mapped[str | None] = mapped_column(Text)
    department: Mapped[str | None] = mapped_column(Text)
    doctor: Mapped[str | None] = mapped_column(Text)
    image_path: Mapped[str | None] = mapped_column(Text)  # 原始图片路径
    ocr_text: Mapped[str | None] = mapped_column(Text)  # OCR识别的原始文本
    structured_data: Mapped[dict | None] = mapped_column(JSON)  # 结构化后的数据
    doctor_orders: Mapped[dict | None] = mapped_column(JSON)  # 医嘱结构化
    lab_results: Mapped[dict | None] = mapped_column(JSON)  # 化验结果结构化
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<MedicalRecord(id={self.id}, type='{self.record_type}', person_id={self.person_id})>"

"""ReportGeneration model — 健康报告生成记录."""

from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, LargeBinary, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from chronocare.models.base import Base


class ReportGeneration(Base):
    """每次生成健康报告的完整记录，含 prompt/data 快照."""

    __tablename__ = "report_generations"
    __table_args__ = (
        CheckConstraint("layout IN ('pc', 'mobile')", name="ck_report_layout"),
        CheckConstraint(
            "status IN ('pending', 'generating', 'completed', 'failed')",
            name="ck_report_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(
        ForeignKey("persons.id"), nullable=False, index=True
    )
    layout: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    prompt_snapshot: Mapped[str] = mapped_column(Text, nullable=False, default="")
    data_snapshot: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    generation_seconds: Mapped[float | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Relationships
    person = relationship("Person", back_populates="report_generations")

    def __repr__(self) -> str:
        return (
            f"<ReportGeneration id={self.id} person={self.person_id} "
            f"layout={self.layout} status={self.status}>"
        )

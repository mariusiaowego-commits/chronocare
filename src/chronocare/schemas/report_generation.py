"""Schemas for ReportGeneration."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReportGenerateRequest(BaseModel):
    """Request to generate a report."""

    layout: str = "pc"  # "pc" | "mobile"


class ReportGenerationRead(BaseModel):
    """Response for a single report generation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    person_id: int
    layout: str
    status: str
    image_path: str | None = None
    error_message: str | None = None
    generation_seconds: float | None = None
    created_at: datetime
    completed_at: datetime | None = None


class ReportGenerationBrief(BaseModel):
    """Brief response for report history list."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    person_id: int
    layout: str
    status: str
    image_path: str | None = None
    created_at: datetime
    completed_at: datetime | None = None

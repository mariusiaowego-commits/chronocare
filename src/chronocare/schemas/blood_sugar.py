"""Pydantic schemas for BloodSugarRecord."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BloodSugarBase(BaseModel):
    person_id: int
    measured_at: datetime
    value: float  # mmol/L
    meal_context: str | None = None  # fasting, before_meal, after_meal, bedtime, random
    notes: str | None = None
    is_alert: bool = False


class BloodSugarCreate(BloodSugarBase):
    pass


class BloodSugarUpdate(BaseModel):
    measured_at: datetime | None = None
    value: float | None = None
    meal_context: str | None = None
    notes: str | None = None
    is_alert: bool | None = None


class BloodSugarRead(BloodSugarBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class BloodSugarTrend(BaseModel):
    """血糖趋势分析结果"""
    person_id: int
    days: int
    avg_value: float
    min_value: float
    max_value: float
    std_dev: float
    cv: float  # 变异系数
    tir: float  # 目标范围时间百分比 (3.9-10.0 mmol/L)
    moving_avg_7d: float | None = None
    moving_avg_14d: float | None = None
    trend_direction: str  # "rising", "falling", "stable"
    trend_slope: float  # 线性回归斜率 (mmol/L/天)
    prediction_7d: float | None = None  # 7天后预测值
    alerts: list[dict] = []

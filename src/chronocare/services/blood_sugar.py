"""Blood sugar CRUD service."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.models.blood_sugar import BloodSugarRecord
from chronocare.schemas.blood_sugar import BloodSugarCreate, BloodSugarUpdate


async def list_blood_sugar(db: AsyncSession, person_id: int | None = None) -> list[BloodSugarRecord]:
    """List blood sugar records, optionally filtered by person."""
    stmt = select(BloodSugarRecord).order_by(BloodSugarRecord.measured_at.desc())
    if person_id is not None:
        stmt = stmt.where(BloodSugarRecord.person_id == person_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_blood_sugar(db: AsyncSession, record_id: int) -> BloodSugarRecord | None:
    result = await db.execute(select(BloodSugarRecord).where(BloodSugarRecord.id == record_id))
    return result.scalar_one_or_none()


async def create_blood_sugar(db: AsyncSession, data: BloodSugarCreate) -> BloodSugarRecord:
    record = BloodSugarRecord(**data.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def update_blood_sugar(db: AsyncSession, record_id: int, data: BloodSugarUpdate) -> BloodSugarRecord | None:
    record = await get_blood_sugar(db, record_id)
    if record is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    await db.commit()
    await db.refresh(record)
    return record


async def delete_blood_sugar(db: AsyncSession, record_id: int) -> bool:
    record = await get_blood_sugar(db, record_id)
    if record is None:
        return False
    await db.delete(record)
    await db.commit()
    return True


async def get_blood_sugar_trend(
    db: AsyncSession,
    person_id: int,
    days: int = 30,
) -> dict:
    """获取血糖趋势分析"""
    import statistics
    from datetime import datetime, timedelta
    
    # 获取指定天数内的记录
    start_date = datetime.now() - timedelta(days=days)
    stmt = (
        select(BloodSugarRecord)
        .where(BloodSugarRecord.person_id == person_id)
        .where(BloodSugarRecord.measured_at >= start_date)
        .order_by(BloodSugarRecord.measured_at.asc())
    )
    result = await db.execute(stmt)
    records = list(result.scalars().all())
    
    if not records:
        return {
            "person_id": person_id,
            "days": days,
            "avg_value": 0,
            "min_value": 0,
            "max_value": 0,
            "std_dev": 0,
            "cv": 0,
            "tir": 0,
            "moving_avg_7d": None,
            "moving_avg_14d": None,
            "trend_direction": "stable",
            "trend_slope": 0,
            "prediction_7d": None,
            "alerts": [],
        }
    
    values = [r.value for r in records]
    
    # 基础统计
    avg_value = statistics.mean(values)
    min_value = min(values)
    max_value = max(values)
    std_dev = statistics.stdev(values) if len(values) > 1 else 0
    cv = (std_dev / avg_value * 100) if avg_value > 0 else 0
    
    # TIR: 目标范围时间 (3.9-10.0 mmol/L)
    in_range = sum(1 for v in values if 3.9 <= v <= 10.0)
    tir = in_range / len(values) * 100
    
    # 移动平均
    moving_avg_7d = None
    moving_avg_14d = None
    if len(values) >= 7:
        moving_avg_7d = statistics.mean(values[-7:])
    if len(values) >= 14:
        moving_avg_14d = statistics.mean(values[-14:])
    
    # 线性回归趋势预测
    trend_direction = "stable"
    trend_slope = 0
    prediction_7d = None
    
    if len(values) >= 3:
        # 简单线性回归
        n = len(values)
        x = list(range(n))
        x_mean = statistics.mean(x)
        y_mean = avg_value
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator != 0:
            trend_slope = numerator / denominator
            intercept = y_mean - trend_slope * x_mean
            
            # 趋势方向
            if trend_slope > 0.05:
                trend_direction = "rising"
            elif trend_slope < -0.05:
                trend_direction = "falling"
            else:
                trend_direction = "stable"
            
            # 7天后预测
            prediction_7d = intercept + trend_slope * (n + 7)
    
    # 预警检测
    alerts = []
    consecutive_high = 0
    for v in reversed(values):
        if v > 7.8:
            consecutive_high += 1
        else:
            break
    if consecutive_high >= 3:
        alerts.append({
            "type": "consecutive_high",
            "severity": "high",
            "icon": "🔴",
            "message": f"连续{consecutive_high}次高血糖"
        })
    
    if avg_value > 7.0:
        alerts.append({
            "type": "sustained_elevation",
            "severity": "medium",
            "icon": "🟡",
            "message": f"{days}天平均值偏高 ({avg_value:.1f})"
        })
    
    if len(values) >= 3 and values[-1] - values[-3] > 3:
        alerts.append({"type": "rapid_increase", "severity": "high", "icon": "🔺", "message": "血糖快速上升"})
    
    if values[-1] > 11.1:
        alerts.append({
            "type": "very_high",
            "severity": "critical",
            "icon": "🚨",
            "message": f"当前血糖严重偏高 ({values[-1]:.1f})"
        })
    
    return {
        "person_id": person_id,
        "days": days,
        "avg_value": round(avg_value, 2),
        "min_value": round(min_value, 2),
        "max_value": round(max_value, 2),
        "std_dev": round(std_dev, 2),
        "cv": round(cv, 2),
        "tir": round(tir, 2),
        "moving_avg_7d": round(moving_avg_7d, 2) if moving_avg_7d is not None else None,
        "moving_avg_14d": round(moving_avg_14d, 2) if moving_avg_14d is not None else None,
        "trend_direction": trend_direction,
        "trend_slope": round(trend_slope, 4),
        "prediction_7d": round(prediction_7d, 2) if prediction_7d is not None else None,
        "alerts": alerts,
    }


async def get_blood_sugar_chart_data(
    db: AsyncSession,
    person_id: int,
    days: int = 14,
) -> dict:
    """获取血糖趋势图表数据"""
    from datetime import datetime, timedelta
    
    start_date = datetime.now() - timedelta(days=days)
    stmt = (
        select(BloodSugarRecord)
        .where(BloodSugarRecord.person_id == person_id)
        .where(BloodSugarRecord.measured_at >= start_date)
        .order_by(BloodSugarRecord.measured_at.asc())
    )
    result = await db.execute(stmt)
    records = list(result.scalars().all())
    
    labels = [r.measured_at.strftime("%m-%d") for r in records]
    values = [float(r.value) for r in records]
    alerts = [bool(r.is_alert) for r in records]
    
    return {
        "labels": labels,
        "values": values,
        "alerts": alerts,
    }

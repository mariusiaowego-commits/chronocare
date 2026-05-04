"""Blood pressure circadian rhythm analysis — day/night patterns."""

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.models.cardiac import BloodPressureRecord


async def analyze_bp_circadian(
    person_id: int,
    days: int = 30,
    db: AsyncSession = None,
) -> dict:
    """Analyze blood pressure circadian rhythm patterns."""
    cutoff = datetime.now() - timedelta(days=days)

    stmt = (
        select(BloodPressureRecord)
        .where(BloodPressureRecord.person_id == person_id)
        .where(BloodPressureRecord.measured_at >= cutoff)
        .order_by(BloodPressureRecord.measured_at.asc())
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    if len(records) < 5:
        return {
            "count": len(records),
            "error": "Insufficient data (need at least 5 readings)",
        }

    # Define time periods
    # Day: 6:00-22:00, Night: 22:00-6:00
    day_records = []
    night_records = []
    
    for r in records:
        hour = r.measured_at.hour
        if 6 <= hour < 22:
            day_records.append(r)
        else:
            night_records.append(r)

    def calc_stats(recs, label):
        if not recs:
            return {"count": 0, "label": label}
        sys_vals = [r.systolic for r in recs]
        dia_vals = [r.diastolic for r in recs]
        hr_vals = [r.heart_rate for r in recs if r.heart_rate]
        return {
            "count": len(recs),
            "label": label,
            "systolic_avg": round(sum(sys_vals) / len(sys_vals), 1),
            "systolic_min": min(sys_vals),
            "systolic_max": max(sys_vals),
            "diastolic_avg": round(sum(dia_vals) / len(dia_vals), 1),
            "diastolic_min": min(dia_vals),
            "diastolic_max": max(dia_vals),
            "heart_rate_avg": round(sum(hr_vals) / len(hr_vals), 1) if hr_vals else None,
        }

    day_stats = calc_stats(day_records, "日间 (6:00-22:00)")
    night_stats = calc_stats(night_records, "夜间 (22:00-6:00)")

    # Circadian pattern detection
    pattern = _detect_circadian_pattern(day_stats, night_stats)

    # Hourly analysis
    hourly = {}
    for r in records:
        hour = r.measured_at.hour
        if hour not in hourly:
            hourly[hour] = {"sys": [], "dia": [], "hr": []}
        hourly[hour]["sys"].append(r.systolic)
        hourly[hour]["dia"].append(r.diastolic)
        if r.heart_rate:
            hourly[hour]["hr"].append(r.heart_rate)

    hourly_stats = []
    for hour in sorted(hourly.keys()):
        h = hourly[hour]
        hourly_stats.append({
            "hour": hour,
            "label": f"{hour:02d}:00",
            "count": len(h["sys"]),
            "systolic_avg": round(sum(h["sys"]) / len(h["sys"]), 1),
            "diastolic_avg": round(sum(h["dia"]) / len(h["dia"]), 1),
            "heart_rate_avg": round(sum(h["hr"]) / len(h["hr"]), 1) if h["hr"] else None,
        })

    # Morning surge detection (6-10 AM vs night average)
    morning_surge = _detect_morning_surge(records, night_stats)

    return {
        "count": len(records),
        "period_days": days,
        "day_stats": day_stats,
        "night_stats": night_stats,
        "pattern": pattern,
        "hourly_stats": hourly_stats,
        "morning_surge": morning_surge,
        "interpretation": _interpret_circadian(pattern, morning_surge, day_stats, night_stats),
    }


def _detect_circadian_pattern(day_stats: dict, night_stats: dict) -> dict:
    """Detect BP circadian pattern (dipper/non-dipper/reverse-dipper)."""
    if day_stats["count"] == 0 or night_stats["count"] == 0:
        return {"type": "unknown", "label": "数据不足", "color": "gray"}

    # Calculate dip percentage
    day_sys = day_stats["systolic_avg"]
    night_sys = night_stats["systolic_avg"]
    dip_pct = ((day_sys - night_sys) / day_sys) * 100 if day_sys > 0 else 0

    if dip_pct >= 10 and dip_pct <= 20:
        return {
            "type": "dipper",
            "label": "杓型 (正常)",
            "color": "green",
            "dip_pct": round(dip_pct, 1),
            "description": "夜间血压较日间下降10-20%，属正常节律",
        }
    elif dip_pct > 20:
        return {
            "type": "extreme-dipper",
            "label": "超杓型",
            "color": "blue",
            "dip_pct": round(dip_pct, 1),
            "description": "夜间血压过度下降(>20%)，可能增加缺血风险",
        }
    elif 0 <= dip_pct < 10:
        return {
            "type": "non-dipper",
            "label": "非杓型",
            "color": "yellow",
            "dip_pct": round(dip_pct, 1),
            "description": "夜间血压下降不足(<10%)，心血管风险增加",
        }
    else:
        return {
            "type": "reverse-dipper",
            "label": "反杓型",
            "color": "red",
            "dip_pct": round(dip_pct, 1),
            "description": "夜间血压反升，心血管风险显著增加",
        }


def _detect_morning_surge(records, night_stats: dict) -> dict | None:
    """Detect morning BP surge."""
    # Get morning readings (6-10 AM)
    morning_records = [r for r in records if 6 <= r.measured_at.hour < 10]
    if len(morning_records) < 3 or night_stats["count"] == 0:
        return None

    morning_sys_avg = sum(r.systolic for r in morning_records) / len(morning_records)
    night_sys_avg = night_stats["systolic_avg"]
    surge = morning_sys_avg - night_sys_avg

    if surge > 35:
        return {
            "detected": True,
            "surge": round(surge, 1),
            "level": "high",
            "message": f"清晨血压激增 {surge:.0f} mmol/Hg (阈值35)，脑卒中风险增加",
        }
    elif surge > 20:
        return {
            "detected": True,
            "surge": round(surge, 1),
            "level": "moderate",
            "message": f"清晨血压上升 {surge:.0f} mmHg，建议关注",
        }
    return {
        "detected": False,
        "surge": round(surge, 1),
        "level": "normal",
        "message": f"清晨血压变化 {surge:.0f} mmHg，属正常范围",
    }


def _interpret_circadian(pattern: dict, morning_surge: dict | None, day_stats: dict, night_stats: dict) -> list[str]:
    """Generate interpretation notes."""
    notes = []

    # Pattern interpretation
    if pattern["type"] == "dipper":
        notes.append("血压节律正常（杓型），夜间血压适度下降")
    elif pattern["type"] == "non-dipper":
        notes.append("非杓型血压节律，夜间血压下降不足，心血管风险增加")
        notes.append("建议：检查夜间用药、睡眠质量、盐摄入量")
    elif pattern["type"] == "reverse-dipper":
        notes.append("反杓型血压节律，夜间血压反升，风险显著增加")
        notes.append("建议：尽快就医调整用药方案")
    elif pattern["type"] == "extreme-dipper":
        notes.append("超杓型血压节律，夜间血压过度下降")
        notes.append("注意：老年人可能增加脑缺血风险")

    # Morning surge
    if morning_surge and morning_surge["detected"]:
        if morning_surge["level"] == "high":
            notes.append(f"⚠️ 清晨血压激增 {morning_surge['surge']} mmHg，脑卒中风险增加")
        elif morning_surge["level"] == "moderate":
            notes.append(f"清晨血压上升 {morning_surge['surge']} mmHg，建议关注")

    # Day/Night comparison
    if day_stats["count"] > 0 and night_stats["count"] > 0:
        notes.append(f"日间平均 {day_stats['systolic_avg']}/{day_stats['diastolic_avg']} mmHg ({day_stats['count']}次)")
        notes.append(f"夜间平均 {night_stats['systolic_avg']}/{night_stats['diastolic_avg']} mmHg ({night_stats['count']}次)")

    return notes

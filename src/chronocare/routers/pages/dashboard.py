"""Dashboard HTML page — person overview with health summary cards."""

from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.services.blood_sugar import list_blood_sugar
from chronocare.services.person import get_person, list_persons
from chronocare.services.visit import list_visits

router = APIRouter(tags=["pages"])
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


def _bs_status(value: float) -> tuple[str, str]:
    """Return (color_class, label) based on blood sugar value."""
    if value > 11.1:
        return ("text-red-600", "偏高")
    if value > 7.8:
        return ("text-amber-500", "餐后正常")
    if value < 3.9:
        return ("text-blue-600", "偏低")
    return ("text-teal-600", "正常")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    person_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    persons = await list_persons(db)

    # Default to first person if none selected
    if not person_id and persons:
        person_id = persons[0].id

    selected = await get_person(db, person_id) if person_id else None

    # Fetch recent records for selected person
    bs_records = []
    visits = []
    alerts = []
    has_critical = False

    if selected:
        all_bs = await list_blood_sugar(db, selected.id)
        # Last 7 records
        bs_records = sorted(all_bs, key=lambda r: r.measured_at, reverse=True)[:7]

        visits = await list_visits(db, selected.id)
        visits = sorted(visits, key=lambda v: v.visit_date or "", reverse=True)[:5]

        # Generate alerts from latest BS reading
        if bs_records:
            latest = bs_records[0]
            if latest.value > 13.9:
                alerts.append({
                    "severity": "critical",
                    "icon": "🚨",
                    "title": "严重高血糖",
                    "message": f"血糖 {latest.value} mmol/L，需立即处理",
                })
                has_critical = True
            elif latest.value > 11.1:
                alerts.append({
                    "severity": "high",
                    "icon": "⚠️",
                    "title": "高血糖预警",
                    "message": f"血糖 {latest.value} mmol/L，注意饮食",
                })
            elif latest.value < 3.9:
                alerts.append({
                    "severity": "high",
                    "icon": "⚠️",
                    "title": "低血糖预警",
                    "message": f"血糖 {latest.value} mmol/L，及时补充糖分",
                })

        # Next follow-up alert
        upcoming = next((v for v in visits if v.next_followup_date), None)
        if upcoming:
            alerts.append({
                "severity": "medium",
                "icon": "📅",
                "title": "复诊提醒",
                "message": f"{upcoming.hospital or '待定'} · {upcoming.next_followup_date}",
            })

    # Chart data: last 14 days of BS readings
    chart_labels = []
    chart_values = []
    chart_statuses = []
    if selected:
        all_bs_14 = await list_blood_sugar(db, selected.id)
        all_bs_14 = [r for r in all_bs_14 if r.measured_at]
        all_bs_14 = sorted(all_bs_14, key=lambda r: r.measured_at)[-14:]

        for r in all_bs_14:
            chart_labels.append(r.measured_at.strftime("%m-%d"))
            chart_values.append(r.value)
            color, _ = _bs_status(r.value)
            chart_statuses.append(color)

    return templates.TemplateResponse(request, "dashboard.html", {
        "request": request,
        "persons": persons,
        "selected": selected,
        "bs_records": bs_records,
        "visits": visits,
        "alerts": alerts,
        "has_critical": has_critical,
        "alert_count": len(alerts),
        "chart_labels": chart_labels,
        "chart_values": chart_values,
        "chart_statuses": chart_statuses,
    })

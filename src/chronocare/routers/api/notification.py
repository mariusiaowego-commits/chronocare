"""Notification API — send alerts and reports."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.services.health_report import generate_weekly_report
from chronocare.services.notification import notification_service
from chronocare.services.person import get_person
from chronocare.services.trend_alert import get_all_alerts

router = APIRouter(prefix="/api/notification", tags=["notification-api"])


class EmailRequest(BaseModel):
    to_email: str


class AlertRequest(BaseModel):
    person_id: int
    to_email: str | None = None


class ReportRequest(BaseModel):
    person_id: int
    to_email: str | None = None


@router.post("/send-alert")
async def send_alert(
    request: AlertRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send health alert notification."""
    person = await get_person(db, request.person_id)
    if not person:
        return {"error": "Person not found"}

    alerts_data = await get_all_alerts(request.person_id, db)
    if not alerts_data["alerts"]:
        return {"message": "No alerts to send"}

    result = await notification_service.send_health_alert(
        person_name=person.name,
        alerts=alerts_data["alerts"],
        to_email=request.to_email,
    )
    return result


@router.post("/send-weekly-report")
async def send_weekly_report(
    request: ReportRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send weekly report notification."""
    person = await get_person(db, request.person_id)
    if not person:
        return {"error": "Person not found"}

    report = await generate_weekly_report(request.person_id, db)
    if "error" in report:
        return report

    result = await notification_service.send_weekly_report(
        person_name=person.name,
        report=report,
        to_email=request.to_email,
    )
    return result


@router.get("/config")
async def get_config():
    """Check notification configuration status."""
    return {
        "smtp_configured": all([
            notification_service.smtp_host,
            notification_service.smtp_user,
            notification_service.smtp_pass,
        ]),
        "default_email": notification_service.notify_email,
    }

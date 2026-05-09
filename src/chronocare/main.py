"""ChronoCare — FastAPI application entry point."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from chronocare.routers.api.admin import router as api_admin_router
from chronocare.routers.api.alerts import router as api_alerts_router
from chronocare.routers.api.blood_sugar import router as api_bs_router
from chronocare.routers.api.bp_circadian import router as api_bp_circadian_router
from chronocare.routers.api.bs_analysis import router as api_bs_analysis_router
from chronocare.routers.api.cardiac import router as api_cardiac_router
from chronocare.routers.api.cardiac_analysis import router as api_cardiac_analysis_router
from chronocare.routers.api.health_profile import router as api_health_profile_router
from chronocare.routers.api.health_report import router as api_health_report_router
from chronocare.routers.api.med_adherence import router as api_med_adherence_router
from chronocare.routers.api.medication import router as api_med_router
from chronocare.routers.api.medication_reminder import router as api_med_reminder_router
from chronocare.routers.api.news import router as api_news_router
from chronocare.routers.api.notification import router as api_notification_router
from chronocare.routers.api.pdf_report import router as api_pdf_report_router

# API routers
from chronocare.routers.api.person import router as api_person_router
from chronocare.routers.api.reports import router as api_reports_router
from chronocare.routers.api.visit import router as api_visit_router
from chronocare.routers.api.wiki import router as api_wiki_router
from chronocare.routers.pages.blood_sugar import router as pages_bs_router
from chronocare.routers.pages.bp_circadian import router as pages_bp_circadian_router
from chronocare.routers.pages.bs_analysis import router as pages_bs_analysis_router
from chronocare.routers.pages.cardiac import router as pages_cardiac_router

# Page routers
from chronocare.routers.pages.dashboard import router as pages_dashboard_router
from chronocare.routers.pages.health_profile import router as pages_health_profile_router
from chronocare.routers.pages.health_report import router as pages_health_report_router
from chronocare.routers.pages.med_adherence import router as pages_med_adherence_router
from chronocare.routers.pages.medication import router as pages_med_router
from chronocare.routers.pages.medication_reminder import router as pages_med_reminder_router
from chronocare.routers.pages.news import router as pages_news_router
from chronocare.routers.pages.person import router as pages_person_router
from chronocare.routers.pages.reports import router as pages_reports_router
from chronocare.routers.pages.visit import router as pages_visit_router
from chronocare.routers.pages.wiki import router as pages_wiki_router

app = FastAPI(title="ChronoCare", description="老年父母健康管理平台", version="0.2.0")

# Paths
_BASE = Path(__file__).resolve().parent
_STATIC = _BASE / "static"
_TEMPLATES = _BASE / "templates"

# Mount static files
app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")

# Template engine
templates = Jinja2Templates(directory=str(_TEMPLATES))

# Register API routers
app.include_router(api_person_router)
app.include_router(api_bs_router)
app.include_router(api_cardiac_router)
app.include_router(api_med_router)
app.include_router(api_visit_router)
app.include_router(api_wiki_router)
app.include_router(api_news_router)
app.include_router(api_reports_router)
app.include_router(api_admin_router)
app.include_router(api_med_reminder_router)
app.include_router(api_cardiac_analysis_router)
app.include_router(api_health_profile_router)
app.include_router(api_alerts_router)
app.include_router(api_health_report_router)
app.include_router(api_notification_router)
app.include_router(api_bs_analysis_router)
app.include_router(api_bp_circadian_router)
app.include_router(api_med_adherence_router)
app.include_router(api_pdf_report_router)

# Register page routers
app.include_router(pages_dashboard_router)
app.include_router(pages_person_router)
app.include_router(pages_bs_router)
app.include_router(pages_cardiac_router)
app.include_router(pages_med_router)
app.include_router(pages_visit_router)
app.include_router(pages_wiki_router)
app.include_router(pages_news_router)
app.include_router(pages_reports_router)
app.include_router(pages_med_reminder_router)
app.include_router(pages_health_profile_router)
app.include_router(pages_health_report_router)
app.include_router(pages_bs_analysis_router)
app.include_router(pages_bp_circadian_router)
app.include_router(pages_med_adherence_router)


@app.get("/")
async def root():
    """Redirect to dashboard."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard")


@app.get("/health")
async def health_check():
    """Health probe for monitoring."""
    return {"status": "healthy"}

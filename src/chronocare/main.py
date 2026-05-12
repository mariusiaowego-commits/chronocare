"""ChronoCare — FastAPI application entry point."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# API routers
from chronocare.routers.api.backup import router as api_backup_router
from chronocare.routers.api.blood_sugar import router as api_bs_router
from chronocare.routers.api.medical_record import router as api_medical_record_router
from chronocare.routers.api.person import router as api_person_router
from chronocare.routers.api.visit import router as api_visit_router

# Page routers
from chronocare.routers.pages.blood_sugar import router as pages_bs_router
from chronocare.routers.pages.dashboard import router as pages_dashboard_router
from chronocare.routers.pages.medical_record import router as pages_medical_record_router
from chronocare.routers.pages.person import router as pages_person_router
from chronocare.routers.pages.visit import router as pages_visit_router

app = FastAPI(title="ChronoCare", description="老年父母健康管理平台", version="0.3.0")

# Paths
_BASE = Path(__file__).resolve().parent
_STATIC = _BASE / "static"
_TEMPLATES = _BASE / "templates"

# Mount static files
app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")

# Template engine
templates = Jinja2Templates(directory=str(_TEMPLATES))

# Register API routers
app.include_router(api_backup_router)
app.include_router(api_person_router)
app.include_router(api_bs_router)
app.include_router(api_visit_router)
app.include_router(api_medical_record_router)

# Register page routers
app.include_router(pages_dashboard_router)
app.include_router(pages_person_router)
app.include_router(pages_bs_router)
app.include_router(pages_visit_router)
app.include_router(pages_medical_record_router)


@app.get("/")
async def root():
    """Redirect to dashboard."""
    return RedirectResponse(url="/dashboard")


@app.get("/health")
async def health_check():
    """Health probe for monitoring."""
    return {"status": "healthy"}

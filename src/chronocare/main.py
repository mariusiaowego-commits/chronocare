"""ChronoCare — FastAPI application entry point."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from chronocare.routers.api.person import router as api_person_router
from chronocare.routers.pages.person import router as pages_person_router

app = FastAPI(title="ChronoCare", description="老年父母健康管理平台", version="0.1.0")

# Paths
_BASE = Path(__file__).resolve().parent
_STATIC = _BASE / "static"
_TEMPLATES = _BASE / "templates"

# Mount static files
app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")

# Template engine
templates = Jinja2Templates(directory=str(_TEMPLATES))

# Register routers
app.include_router(api_person_router)
app.include_router(pages_person_router)


@app.get("/")
async def root():
    """Health check / landing."""
    return {"message": "Welcome to ChronoCare", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    """Health probe for monitoring."""
    return {"status": "healthy"}

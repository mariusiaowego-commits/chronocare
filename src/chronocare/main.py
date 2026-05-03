"""ChronoCare — FastAPI application entry point."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# API routers
from chronocare.routers.api.person import router as api_person_router
from chronocare.routers.api.blood_sugar import router as api_bs_router
from chronocare.routers.api.cardiac import router as api_cardiac_router
from chronocare.routers.api.medication import router as api_med_router
from chronocare.routers.api.visit import router as api_visit_router

# Page routers
from chronocare.routers.pages.dashboard import router as pages_dashboard_router
from chronocare.routers.pages.person import router as pages_person_router
from chronocare.routers.pages.blood_sugar import router as pages_bs_router
from chronocare.routers.pages.cardiac import router as pages_cardiac_router
from chronocare.routers.pages.medication import router as pages_med_router
from chronocare.routers.pages.visit import router as pages_visit_router

app = FastAPI(title="ChronoCare", description="老年父母健康管理平台", version="0.1.0")

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

# Register page routers
app.include_router(pages_dashboard_router)
app.include_router(pages_person_router)
app.include_router(pages_bs_router)
app.include_router(pages_cardiac_router)
app.include_router(pages_med_router)
app.include_router(pages_visit_router)


@app.get("/")
async def root():
    """Redirect to dashboard."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard")


@app.get("/health")
async def health_check():
    """Health probe for monitoring."""
    return {"status": "healthy"}


@app.get("/wiki")
async def wiki_placeholder():
    """Wiki — coming soon."""
    from fastapi.responses import HTMLResponse
    return HTMLResponse(
        "<!DOCTYPE html><html><head><title>知识库 - ChronoCare</title>"
        "<script src='https://cdn.tailwindcss.com'></script></head>"
        "<body class='bg-slate-50 min-h-screen flex items-center justify-center'>"
        "<div class='text-center'>"
        "<p class='text-6xl mb-4'>📚</p>"
        "<h1 class='text-2xl font-bold mb-2'>知识库</h1>"
        "<p class='text-slate-500'>功能开发中，敬请期待</p>"
        "<a href='/dashboard' class='text-blue-600 hover:underline mt-4 inline-block'>← 返回仪表盘</a>"
        "</div></body></html>"
    )


@app.get("/news")
async def news_placeholder():
    """News — coming soon."""
    from fastapi.responses import HTMLResponse
    return HTMLResponse(
        "<!DOCTYPE html><html><head><title>资讯 - ChronoCare</title>"
        "<script src='https://cdn.tailwindcss.com'></script></head>"
        "<body class='bg-slate-50 min-h-screen flex items-center justify-center'>"
        "<div class='text-center'>"
        "<p class='text-6xl mb-4'>📰</p>"
        "<h1 class='text-2xl font-bold mb-2'>健康资讯</h1>"
        "<p class='text-slate-500'>功能开发中，敬请期待</p>"
        "<a href='/dashboard' class='text-blue-600 hover:underline mt-4 inline-block'>← 返回仪表盘</a>"
        "</div></body></html>"
    )

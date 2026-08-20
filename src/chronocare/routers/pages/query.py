"""Lab metric query page."""

from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.services.lab_query import run_lab_query

router = APIRouter(tags=["pages"])
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


@router.get("/query", response_class=HTMLResponse)
async def lab_query_page(
    request: Request,
    q: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    result = None
    preview = None
    if q and q.strip():
        result = await run_lab_query(db, q.strip())
        if result.hit:
            preview = {
                "preview_url": f"/medical-records/{result.hit.record_id}/preview",
                "file_url": f"/medical-records/{result.hit.record_id}/file",
                "detail_url": f"/medical-records/{result.hit.record_id}",
            }
    examples = [
        "qian 最近一次糖化血红蛋白怎么样",
        "妈妈上次肌酐",
        "qian 尿微量白蛋白",
        "qian 2025-12-30 ALT",
    ]
    return templates.TemplateResponse(
        request,
        "query/result.html",
        {
            "request": request,
            "q": q or "",
            "result": result,
            "preview": preview,
            "examples": examples,
        },
    )

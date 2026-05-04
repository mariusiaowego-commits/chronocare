"""News pages — HTMX server-rendered."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.schemas.news import NewsItemCreate, RssFeedCreate
from chronocare.services import news as news_svc

router = APIRouter(prefix="/news", tags=["news-pages"])


@router.get("")
async def news_index(
    request: Request,
    category: str | None = None,
    is_bookmarked: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    items = await news_svc.list_news_items(db, category=category, is_bookmarked=is_bookmarked)
    from chronocare.main import templates
    return templates.TemplateResponse(request, "news/list.html", {
        "request": request,
        "items": items,
        "current_category": category,
        "is_bookmarked": is_bookmarked,
    })


@router.get("/new")
async def news_new_form(request: Request):
    from chronocare.main import templates
    return templates.TemplateResponse(request, "news/form.html", {
        "request": request,
        "item": None,
    })


@router.post("/new")
async def news_create(data: NewsItemCreate, db: AsyncSession = Depends(get_db)):
    await news_svc.create_news_item(db, data)
    return RedirectResponse("/news", status_code=303)


@router.get("/{item_id}")
async def news_detail(request: Request, item_id: int, db: AsyncSession = Depends(get_db)):
    item = await news_svc.get_news_item(db, item_id)
    if not item:
        from fastapi import HTTPException
        raise HTTPException(404, "News item not found")
    from chronocare.main import templates
    return templates.TemplateResponse(request, "news/detail.html", {
        "request": request,
        "item": item,
    })


@router.get("/{item_id}/edit")
async def news_edit_form(request: Request, item_id: int, db: AsyncSession = Depends(get_db)):
    item = await news_svc.get_news_item(db, item_id)
    if not item:
        from fastapi import HTTPException
        raise HTTPException(404, "News item not found")
    from chronocare.main import templates
    return templates.TemplateResponse(request, "news/form.html", {
        "request": request,
        "item": item,
    })


@router.post("/{item_id}/edit")
async def news_update(item_id: int, data: NewsItemCreate, db: AsyncSession = Depends(get_db)):
    from chronocare.schemas.news import NewsItemUpdate
    update_data = NewsItemUpdate(**data.model_dump())
    await news_svc.update_news_item(db, item_id, update_data)
    return RedirectResponse(f"/news/{item_id}", status_code=303)


@router.post("/{item_id}/delete")
async def news_delete(item_id: int, db: AsyncSession = Depends(get_db)):
    await news_svc.delete_news_item(db, item_id)
    return RedirectResponse("/news", status_code=303)


@router.post("/{item_id}/bookmark")
async def news_toggle_bookmark(item_id: int, db: AsyncSession = Depends(get_db)):
    await news_svc.toggle_bookmark(db, item_id)
    return RedirectResponse("/news", status_code=303)


@router.post("/{item_id}/share")
async def news_toggle_share(item_id: int, db: AsyncSession = Depends(get_db)):
    await news_svc.toggle_share(db, item_id)
    return RedirectResponse("/news", status_code=303)


# ── RSS Feed pages ────────────────────────────────────────────

@router.get("/feeds/manage")
async def feeds_manage(request: Request, db: AsyncSession = Depends(get_db)):
    feeds = await news_svc.list_feeds(db)
    from chronocare.main import templates
    return templates.TemplateResponse(request, "news/feeds.html", {
        "request": request,
        "feeds": feeds,
    })


@router.get("/feeds/new")
async def feed_new_form(request: Request):
    from chronocare.main import templates
    return templates.TemplateResponse(request, "news/feed_form.html", {
        "request": request,
        "feed": None,
    })


@router.post("/feeds/new")
async def feed_create(data: RssFeedCreate, db: AsyncSession = Depends(get_db)):
    await news_svc.create_feed(db, data)
    return RedirectResponse("/news/feeds/manage", status_code=303)

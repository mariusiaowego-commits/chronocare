"""News API — REST endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.schemas.news import (
    NewsItemBrief,
    NewsItemCreate,
    NewsItemRead,
    NewsItemUpdate,
    RssFeedCreate,
    RssFeedRead,
    RssFeedUpdate,
)
from chronocare.services import news as news_svc

router = APIRouter(prefix="/api/news", tags=["news"])


# ── NewsItems ─────────────────────────────────────────────────

@router.post("/items", response_model=NewsItemRead, status_code=201)
async def api_create_news_item(data: NewsItemCreate, db: AsyncSession = Depends(get_db)):
    return await news_svc.create_news_item(db, data)


@router.get("/items", response_model=list[NewsItemBrief])
async def api_list_news_items(
    category: str | None = None,
    is_bookmarked: bool | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await news_svc.list_news_items(
        db, category=category, is_bookmarked=is_bookmarked, limit=limit, offset=offset
    )


@router.get("/items/{item_id}", response_model=NewsItemRead)
async def api_get_news_item(item_id: int, db: AsyncSession = Depends(get_db)):
    item = await news_svc.get_news_item(db, item_id)
    if not item:
        raise HTTPException(404, "News item not found")
    return item


@router.patch("/items/{item_id}", response_model=NewsItemRead)
async def api_update_news_item(item_id: int, data: NewsItemUpdate, db: AsyncSession = Depends(get_db)):
    item = await news_svc.update_news_item(db, item_id, data)
    if not item:
        raise HTTPException(404, "News item not found")
    return item


@router.delete("/items/{item_id}", status_code=204)
async def api_delete_news_item(item_id: int, db: AsyncSession = Depends(get_db)):
    if not await news_svc.delete_news_item(db, item_id):
        raise HTTPException(404, "News item not found")


@router.post("/items/{item_id}/bookmark", response_model=NewsItemRead)
async def api_toggle_bookmark(item_id: int, db: AsyncSession = Depends(get_db)):
    item = await news_svc.toggle_bookmark(db, item_id)
    if not item:
        raise HTTPException(404, "News item not found")
    return item


@router.post("/items/{item_id}/share", response_model=NewsItemRead)
async def api_toggle_share(item_id: int, db: AsyncSession = Depends(get_db)):
    item = await news_svc.toggle_share(db, item_id)
    if not item:
        raise HTTPException(404, "News item not found")
    return item


# ── RSS Feeds ─────────────────────────────────────────────────

@router.post("/feeds", response_model=RssFeedRead, status_code=201)
async def api_create_feed(data: RssFeedCreate, db: AsyncSession = Depends(get_db)):
    return await news_svc.create_feed(db, data)


@router.get("/feeds", response_model=list[RssFeedRead])
async def api_list_feeds(
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await news_svc.list_feeds(db, is_active=is_active)


@router.get("/feeds/{feed_id}", response_model=RssFeedRead)
async def api_get_feed(feed_id: int, db: AsyncSession = Depends(get_db)):
    feed = await news_svc.get_feed(db, feed_id)
    if not feed:
        raise HTTPException(404, "Feed not found")
    return feed


@router.patch("/feeds/{feed_id}", response_model=RssFeedRead)
async def api_update_feed(feed_id: int, data: RssFeedUpdate, db: AsyncSession = Depends(get_db)):
    feed = await news_svc.update_feed(db, feed_id, data)
    if not feed:
        raise HTTPException(404, "Feed not found")
    return feed


@router.delete("/feeds/{feed_id}", status_code=204)
async def api_delete_feed(feed_id: int, db: AsyncSession = Depends(get_db)):
    if not await news_svc.delete_feed(db, feed_id):
        raise HTTPException(404, "Feed not found")

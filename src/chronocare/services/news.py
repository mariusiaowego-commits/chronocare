"""News service — CRUD + bookmark/share."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.models.news import NewsItem, RssFeed
from chronocare.schemas.news import (
    NewsItemCreate,
    NewsItemUpdate,
    RssFeedCreate,
    RssFeedUpdate,
)


# ── NewsItem CRUD ─────────────────────────────────────────────

async def create_news_item(db: AsyncSession, data: NewsItemCreate) -> NewsItem:
    item = NewsItem(**data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def get_news_item(db: AsyncSession, item_id: int) -> NewsItem | None:
    return await db.get(NewsItem, item_id)


async def list_news_items(
    db: AsyncSession,
    category: str | None = None,
    is_bookmarked: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[NewsItem]:
    q = select(NewsItem)
    if category is not None:
        q = q.where(NewsItem.category == category)
    if is_bookmarked is not None:
        q = q.where(NewsItem.is_bookmarked == is_bookmarked)
    q = q.order_by(NewsItem.published_at.desc().nullslast(), NewsItem.created_at.desc())
    q = q.limit(limit).offset(offset)
    result = await db.execute(q)
    return list(result.scalars().all())


async def update_news_item(db: AsyncSession, item_id: int, data: NewsItemUpdate) -> NewsItem | None:
    item = await db.get(NewsItem, item_id)
    if not item:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    await db.commit()
    await db.refresh(item)
    return item


async def delete_news_item(db: AsyncSession, item_id: int) -> bool:
    item = await db.get(NewsItem, item_id)
    if not item:
        return False
    await db.delete(item)
    await db.commit()
    return True


async def toggle_bookmark(db: AsyncSession, item_id: int) -> NewsItem | None:
    item = await db.get(NewsItem, item_id)
    if not item:
        return None
    item.is_bookmarked = not item.is_bookmarked
    await db.commit()
    await db.refresh(item)
    return item


async def toggle_share(db: AsyncSession, item_id: int) -> NewsItem | None:
    item = await db.get(NewsItem, item_id)
    if not item:
        return None
    item.is_shared = not item.is_shared
    await db.commit()
    await db.refresh(item)
    return item


# ── RssFeed CRUD ──────────────────────────────────────────────

async def create_feed(db: AsyncSession, data: RssFeedCreate) -> RssFeed:
    feed = RssFeed(**data.model_dump())
    db.add(feed)
    await db.commit()
    await db.refresh(feed)
    return feed


async def get_feed(db: AsyncSession, feed_id: int) -> RssFeed | None:
    return await db.get(RssFeed, feed_id)


async def list_feeds(db: AsyncSession, is_active: bool | None = None) -> list[RssFeed]:
    q = select(RssFeed)
    if is_active is not None:
        q = q.where(RssFeed.is_active == is_active)
    q = q.order_by(RssFeed.created_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


async def update_feed(db: AsyncSession, feed_id: int, data: RssFeedUpdate) -> RssFeed | None:
    feed = await db.get(RssFeed, feed_id)
    if not feed:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(feed, k, v)
    await db.commit()
    await db.refresh(feed)
    return feed


async def delete_feed(db: AsyncSession, feed_id: int) -> bool:
    feed = await db.get(RssFeed, feed_id)
    if not feed:
        return False
    await db.delete(feed)
    await db.commit()
    return True

"""News / RSS schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

# ── NewsItem ──────────────────────────────────────────────────

class NewsItemCreate(BaseModel):
    title: str = Field(..., max_length=300)
    url: str | None = None
    source: str | None = None
    content: str | None = None
    summary: str | None = None
    published_at: datetime | None = None
    category: str | None = None
    tags: list[str] | None = None
    is_bookmarked: bool = False
    is_shared: bool = False


class NewsItemRead(BaseModel):
    id: int
    title: str
    url: str | None
    source: str | None
    content: str | None
    summary: str | None
    published_at: datetime | None
    category: str | None
    tags: list[str] | None
    is_bookmarked: bool
    is_shared: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NewsItemUpdate(BaseModel):
    title: str | None = Field(None, max_length=300)
    url: str | None = None
    source: str | None = None
    content: str | None = None
    summary: str | None = None
    published_at: datetime | None = None
    category: str | None = None
    tags: list[str] | None = None
    is_bookmarked: bool | None = None
    is_shared: bool | None = None


class NewsItemBrief(BaseModel):
    """List view — no full content."""
    id: int
    title: str
    url: str | None
    source: str | None
    summary: str | None
    published_at: datetime | None
    category: str | None
    is_bookmarked: bool
    is_shared: bool

    model_config = {"from_attributes": True}


# ── RssFeed ───────────────────────────────────────────────────

class RssFeedCreate(BaseModel):
    name: str = Field(..., max_length=100)
    url: str
    category: str | None = None
    is_active: bool = True
    fetch_interval_hours: int = Field(4, ge=1, le=168)


class RssFeedRead(BaseModel):
    id: int
    name: str
    url: str
    category: str | None
    is_active: bool
    last_fetched_at: datetime | None
    fetch_interval_hours: int
    created_at: datetime

    model_config = {"from_attributes": True}


class RssFeedUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    url: str | None = None
    category: str | None = None
    is_active: bool | None = None
    fetch_interval_hours: int | None = Field(None, ge=1, le=168)

"""Wiki (knowledge base) schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

# ── WikiCategory ──────────────────────────────────────────────

class WikiCategoryCreate(BaseModel):
    name: str = Field(..., max_length=100)
    slug: str | None = None  # auto from name
    parent_id: int | None = None
    description: str | None = None
    icon: str | None = None
    sort_order: int = 0


class WikiCategoryRead(BaseModel):
    id: int
    name: str
    slug: str
    parent_id: int | None
    description: str | None
    icon: str | None
    sort_order: int

    model_config = {"from_attributes": True}


class WikiCategoryUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    slug: str | None = None
    parent_id: int | None = None
    description: str | None = None
    icon: str | None = None
    sort_order: int | None = None


# ── WikiArticle ───────────────────────────────────────────────

class WikiArticleCreate(BaseModel):
    title: str = Field(..., max_length=200)
    slug: str | None = None  # auto from title
    content: str
    category_id: int | None = None
    tags: list[str] | None = None
    source: str | None = None
    source_url: str | None = None
    related_conditions: list[str] | None = None
    related_persons: list[int] | None = None
    is_recommended: bool = False


class WikiArticleRead(BaseModel):
    id: int
    title: str
    slug: str
    content: str
    category_id: int | None
    tags: list[str] | None
    source: str | None
    source_url: str | None
    related_conditions: list[str] | None
    related_persons: list[int] | None
    is_recommended: bool
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class WikiArticleUpdate(BaseModel):
    title: str | None = Field(None, max_length=200)
    slug: str | None = None
    content: str | None = None
    category_id: int | None = None
    tags: list[str] | None = None
    source: str | None = None
    source_url: str | None = None
    related_conditions: list[str] | None = None
    related_persons: list[int] | None = None
    is_recommended: bool | None = None


class WikiArticleBrief(BaseModel):
    """List view — no full content."""
    id: int
    title: str
    slug: str
    category_id: int | None
    tags: list[str] | None
    is_recommended: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class WikiSearchParams(BaseModel):
    q: str = Field(..., min_length=1)
    category_id: int | None = None
    limit: int = Field(20, ge=1, le=100)

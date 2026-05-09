"""Wiki service — CRUD + FTS5 full-text search."""

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.models.wiki import WikiArticle, WikiCategory
from chronocare.schemas.wiki import (
    WikiArticleCreate,
    WikiArticleUpdate,
    WikiCategoryCreate,
    WikiCategoryUpdate,
)

# ── Category CRUD ─────────────────────────────────────────────

async def create_category(db: AsyncSession, data: WikiCategoryCreate) -> WikiCategory:
    cat = WikiCategory(**data.model_dump())
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


async def get_category(db: AsyncSession, cat_id: int) -> WikiCategory | None:
    return await db.get(WikiCategory, cat_id)


async def list_categories(db: AsyncSession) -> list[WikiCategory]:
    result = await db.execute(select(WikiCategory).order_by(WikiCategory.sort_order))
    return list(result.scalars().all())


async def update_category(db: AsyncSession, cat_id: int, data: WikiCategoryUpdate) -> WikiCategory | None:
    cat = await db.get(WikiCategory, cat_id)
    if not cat:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(cat, k, v)
    await db.commit()
    await db.refresh(cat)
    return cat


async def delete_category(db: AsyncSession, cat_id: int) -> bool:
    cat = await db.get(WikiCategory, cat_id)
    if not cat:
        return False
    await db.delete(cat)
    await db.commit()
    return True


# ── Article CRUD ──────────────────────────────────────────────

async def create_article(db: AsyncSession, data: WikiArticleCreate) -> WikiArticle:
    article = WikiArticle(**data.model_dump())
    db.add(article)
    await db.commit()
    await db.refresh(article)
    # Sync to FTS index
    await _fts_upsert(db, article)
    return article


async def get_article(db: AsyncSession, article_id: int) -> WikiArticle | None:
    return await db.get(WikiArticle, article_id)


async def get_article_by_slug(db: AsyncSession, slug: str) -> WikiArticle | None:
    result = await db.execute(select(WikiArticle).where(WikiArticle.slug == slug))
    return result.scalar_one_or_none()


async def list_articles(
    db: AsyncSession,
    category_id: int | None = None,
    is_recommended: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[WikiArticle]:
    q = select(WikiArticle)
    if category_id is not None:
        q = q.where(WikiArticle.category_id == category_id)
    if is_recommended is not None:
        q = q.where(WikiArticle.is_recommended == is_recommended)
    q = q.order_by(WikiArticle.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    return list(result.scalars().all())


async def update_article(db: AsyncSession, article_id: int, data: WikiArticleUpdate) -> WikiArticle | None:
    article = await db.get(WikiArticle, article_id)
    if not article:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(article, k, v)
    await db.commit()
    await db.refresh(article)
    await _fts_upsert(db, article)
    return article


async def delete_article(db: AsyncSession, article_id: int) -> bool:
    article = await db.get(WikiArticle, article_id)
    if not article:
        return False
    await _fts_delete(db, article_id)
    await db.delete(article)
    await db.commit()
    return True


# ── FTS5 Search ───────────────────────────────────────────────

async def search_articles(
    db: AsyncSession,
    query: str,
    category_id: int | None = None,
    limit: int = 20,
) -> list[WikiArticle]:
    """Full-text search via FTS5. Returns articles ranked by relevance."""
    # FTS5 match syntax
    fts_query = query.replace('"', '""')
    sql = """
        SELECT wa.* FROM wiki_articles wa
        JOIN wiki_fts ON wa.id = wiki_fts.rowid
        WHERE wiki_fts MATCH :query
    """
    if category_id is not None:
        sql += " AND wa.category_id = :cat_id"
    sql += " ORDER BY rank LIMIT :limit"

    params = {"query": fts_query, "limit": limit}
    if category_id is not None:
        params["cat_id"] = category_id

    result = await db.execute(text(sql), params)
    rows = result.fetchall()
    return [WikiArticle(**dict(row._mapping)) for row in rows]


# ── FTS5 helpers ──────────────────────────────────────────────

async def _fts_upsert(db: AsyncSession, article: WikiArticle) -> None:
    """Insert or replace FTS index entry."""
    tags_str = " ".join(article.tags) if article.tags else ""
    await db.execute(text(
        "INSERT OR REPLACE INTO wiki_fts(rowid, title, content, tags) "
        "VALUES (:id, :title, :content, :tags)"
    ), {"id": article.id, "title": article.title, "content": article.content, "tags": tags_str})


async def _fts_delete(db: AsyncSession, article_id: int) -> None:
    """Remove FTS index entry."""
    await db.execute(text(
        "DELETE FROM wiki_fts WHERE rowid = :id"
    ), {"id": article_id})

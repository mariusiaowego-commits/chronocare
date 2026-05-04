"""Wiki API — REST endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.schemas.wiki import (
    WikiArticleBrief,
    WikiArticleCreate,
    WikiArticleRead,
    WikiArticleUpdate,
    WikiCategoryCreate,
    WikiCategoryRead,
    WikiCategoryUpdate,
)
from chronocare.services import wiki as wiki_svc

router = APIRouter(prefix="/api/wiki", tags=["wiki"])


# ── Categories ────────────────────────────────────────────────

@router.post("/categories", response_model=WikiCategoryRead, status_code=201)
async def api_create_category(data: WikiCategoryCreate, db: AsyncSession = Depends(get_db)):
    return await wiki_svc.create_category(db, data)


@router.get("/categories", response_model=list[WikiCategoryRead])
async def api_list_categories(db: AsyncSession = Depends(get_db)):
    return await wiki_svc.list_categories(db)


@router.get("/categories/{cat_id}", response_model=WikiCategoryRead)
async def api_get_category(cat_id: int, db: AsyncSession = Depends(get_db)):
    cat = await wiki_svc.get_category(db, cat_id)
    if not cat:
        raise HTTPException(404, "Category not found")
    return cat


@router.patch("/categories/{cat_id}", response_model=WikiCategoryRead)
async def api_update_category(cat_id: int, data: WikiCategoryUpdate, db: AsyncSession = Depends(get_db)):
    cat = await wiki_svc.update_category(db, cat_id, data)
    if not cat:
        raise HTTPException(404, "Category not found")
    return cat


@router.delete("/categories/{cat_id}", status_code=204)
async def api_delete_category(cat_id: int, db: AsyncSession = Depends(get_db)):
    if not await wiki_svc.delete_category(db, cat_id):
        raise HTTPException(404, "Category not found")


# ── Articles ──────────────────────────────────────────────────

@router.post("/articles", response_model=WikiArticleRead, status_code=201)
async def api_create_article(data: WikiArticleCreate, db: AsyncSession = Depends(get_db)):
    return await wiki_svc.create_article(db, data)


@router.get("/articles", response_model=list[WikiArticleBrief])
async def api_list_articles(
    category_id: int | None = None,
    is_recommended: bool | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await wiki_svc.list_articles(db, category_id=category_id, is_recommended=is_recommended, limit=limit, offset=offset)


@router.get("/articles/search", response_model=list[WikiArticleRead])
async def api_search_articles(
    q: str = Query(..., min_length=1),
    category_id: int | None = None,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await wiki_svc.search_articles(db, q, category_id=category_id, limit=limit)


@router.get("/articles/{article_id}", response_model=WikiArticleRead)
async def api_get_article(article_id: int, db: AsyncSession = Depends(get_db)):
    article = await wiki_svc.get_article(db, article_id)
    if not article:
        raise HTTPException(404, "Article not found")
    return article


@router.patch("/articles/{article_id}", response_model=WikiArticleRead)
async def api_update_article(article_id: int, data: WikiArticleUpdate, db: AsyncSession = Depends(get_db)):
    article = await wiki_svc.update_article(db, article_id, data)
    if not article:
        raise HTTPException(404, "Article not found")
    return article


@router.delete("/articles/{article_id}", status_code=204)
async def api_delete_article(article_id: int, db: AsyncSession = Depends(get_db)):
    if not await wiki_svc.delete_article(db, article_id):
        raise HTTPException(404, "Article not found")

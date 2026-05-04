"""Wiki pages — HTMX server-rendered."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from chronocare.database import get_db
from chronocare.schemas.wiki import WikiArticleCreate, WikiCategoryCreate
from chronocare.services import wiki as wiki_svc

router = APIRouter(prefix="/wiki", tags=["wiki-pages"])


@router.get("")
async def wiki_index(
    request: Request,
    category_id: int | None = None,
    q: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    categories = await wiki_svc.list_categories(db)
    if q:
        articles = await wiki_svc.search_articles(db, q, category_id=category_id)
    else:
        articles = await wiki_svc.list_articles(db, category_id=category_id)
    from chronocare.main import templates
    return templates.TemplateResponse(request, "wiki/list.html", {
        "request": request,
        "articles": articles,
        "categories": categories,
        "current_category": category_id,
        "query": q or "",
    })


@router.get("/new")
async def wiki_new_form(request: Request, db: AsyncSession = Depends(get_db)):
    categories = await wiki_svc.list_categories(db)
    from chronocare.main import templates
    return templates.TemplateResponse(request, "wiki/form.html", {
        "request": request,
        "categories": categories,
        "article": None,
    })


@router.post("/new")
async def wiki_create(data: WikiArticleCreate, db: AsyncSession = Depends(get_db)):
    await wiki_svc.create_article(db, data)
    return RedirectResponse("/wiki", status_code=303)


@router.get("/{article_id}")
async def wiki_detail(request: Request, article_id: int, db: AsyncSession = Depends(get_db)):
    article = await wiki_svc.get_article(db, article_id)
    if not article:
        from fastapi import HTTPException
        raise HTTPException(404, "Article not found")
    categories = await wiki_svc.list_categories(db)
    cat_name = ""
    for c in categories:
        if c.id == article.category_id:
            cat_name = c.name
            break
    from chronocare.main import templates
    return templates.TemplateResponse(request, "wiki/detail.html", {
        "request": request,
        "article": article,
        "cat_name": cat_name,
    })


@router.get("/{article_id}/edit")
async def wiki_edit_form(request: Request, article_id: int, db: AsyncSession = Depends(get_db)):
    article = await wiki_svc.get_article(db, article_id)
    if not article:
        from fastapi import HTTPException
        raise HTTPException(404, "Article not found")
    categories = await wiki_svc.list_categories(db)
    from chronocare.main import templates
    return templates.TemplateResponse(request, "wiki/form.html", {
        "request": request,
        "categories": categories,
        "article": article,
    })


@router.post("/{article_id}/edit")
async def wiki_update(article_id: int, data: WikiArticleCreate, db: AsyncSession = Depends(get_db)):
    from chronocare.schemas.wiki import WikiArticleUpdate
    update_data = WikiArticleUpdate(**data.model_dump())
    await wiki_svc.update_article(db, article_id, update_data)
    return RedirectResponse(f"/wiki/{article_id}", status_code=303)


@router.post("/{article_id}/delete")
async def wiki_delete(article_id: int, db: AsyncSession = Depends(get_db)):
    await wiki_svc.delete_article(db, article_id)
    return RedirectResponse("/wiki", status_code=303)


# ── Category pages ────────────────────────────────────────────

@router.get("/categories/new")
async def cat_new_form(request: Request):
    from chronocare.main import templates
    return templates.TemplateResponse(request, "wiki/cat_form.html", {
        "request": request,
        "category": None,
    })


@router.post("/categories/new")
async def cat_create(data: WikiCategoryCreate, db: AsyncSession = Depends(get_db)):
    await wiki_svc.create_category(db, data)
    return RedirectResponse("/wiki", status_code=303)

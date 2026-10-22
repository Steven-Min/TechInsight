from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.article import (
    ArticleCreate,
    ArticleResponse,
    ArticleUpdate,
    PaginatedArticles,
    SearchMode,
    SearchResponse,
)
from app.services.article import ArticleService

router = APIRouter(prefix="/articles", tags=["articles"])


def get_service(db: AsyncSession = Depends(get_db)) -> ArticleService:
    return ArticleService(db)


@router.get("", response_model=PaginatedArticles, summary="記事一覧（キーワード絞込可）")
async def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    q: str | None = Query(None, max_length=200, description="タイトル・本文の部分一致"),
    category: str | None = Query(None, max_length=128),
    service: ArticleService = Depends(get_service),
) -> PaginatedArticles:
    return await service.list_paginated(page, page_size, q, category)


@router.get("/search", response_model=SearchResponse, summary="セマンティック / キーワード / ハイブリッド検索")
async def search_articles(
    q: str = Query(..., min_length=1, max_length=500, description="自然言語クエリ"),
    mode: SearchMode = Query(SearchMode.semantic),
    limit: int = Query(12, ge=1, le=50),
    service: ArticleService = Depends(get_service),
) -> SearchResponse:
    return await service.search(q, mode, limit)


@router.get("/categories", response_model=list[str], summary="カテゴリ一覧")
async def list_categories(
    service: ArticleService = Depends(get_service),
) -> list[str]:
    return await service.list_categories()


@router.get("/{article_id}", response_model=ArticleResponse, summary="記事詳細")
async def get_article(
    article_id: int, service: ArticleService = Depends(get_service)
) -> ArticleResponse:
    article = await service.get(article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.post(
    "",
    response_model=ArticleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="記事作成",
)
async def create_article(
    payload: ArticleCreate, service: ArticleService = Depends(get_service)
) -> ArticleResponse:
    return await service.create(payload)


@router.patch("/{article_id}", response_model=ArticleResponse, summary="記事更新（部分更新）")
async def update_article(
    article_id: int,
    payload: ArticleUpdate,
    service: ArticleService = Depends(get_service),
) -> ArticleResponse:
    article = await service.update(article_id, payload)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.delete(
    "/{article_id}", status_code=status.HTTP_204_NO_CONTENT, summary="記事削除"
)
async def delete_article(
    article_id: int, service: ArticleService = Depends(get_service)
) -> None:
    deleted = await service.delete(article_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Article not found")

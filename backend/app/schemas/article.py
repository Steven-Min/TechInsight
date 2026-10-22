from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

CONTENT_EXCERPT_LENGTH = 200


class SearchMode(StrEnum):
    keyword = "keyword"
    semantic = "semantic"
    hybrid = "hybrid"


class ArticleBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=512)
    content: str = Field(..., min_length=1)
    category: str | None = Field(None, max_length=128)
    tags: list[str] = Field(default_factory=list, max_length=20)
    author: str | None = Field(None, max_length=128)
    published_at: datetime | None = None


class ArticleCreate(ArticleBase):
    pass


class ArticleUpdate(BaseModel):
    """部分更新。指定されたフィールドのみ更新する。"""

    title: str | None = Field(None, min_length=1, max_length=512)
    content: str | None = Field(None, min_length=1)
    category: str | None = Field(None, max_length=128)
    tags: list[str] | None = Field(None, max_length=20)
    author: str | None = Field(None, max_length=128)
    published_at: datetime | None = None


class ArticleResponse(ArticleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class ArticleListItem(BaseModel):
    """一覧用の軽量表現。本文は抜粋のみ返し転送量を抑える。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    excerpt: str
    category: str | None
    tags: list[str]
    author: str | None
    published_at: datetime | None
    updated_at: datetime

    @classmethod
    def from_article(cls, article) -> "ArticleListItem":
        excerpt = article.content[:CONTENT_EXCERPT_LENGTH]
        if len(article.content) > CONTENT_EXCERPT_LENGTH:
            excerpt += "…"
        return cls(
            id=article.id,
            title=article.title,
            excerpt=excerpt,
            category=article.category,
            tags=article.tags,
            author=article.author,
            published_at=article.published_at,
            updated_at=article.updated_at,
        )


class PaginatedArticles(BaseModel):
    items: list[ArticleListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class SearchResultItem(BaseModel):
    article: ArticleListItem
    score: float = Field(..., description="類似度スコア（モードにより意味が異なる）")


class SearchResponse(BaseModel):
    mode: SearchMode
    query: str
    results: list[SearchResultItem]

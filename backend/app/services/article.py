"""記事サービス。ビジネスロジック（Embedding 連携・検索モード分岐）を担う。"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.cursor import decode_cursor, encode_cursor
from app.models.article import Article
from app.repositories.article import ArticleRepository
from app.schemas.article import (
    ArticleCreate,
    ArticleListItem,
    ArticleUpdate,
    PaginatedArticles,
    SearchMode,
    SearchResponse,
    SearchResultItem,
    TotalRelation,
)
from app.services.embedding import EmbeddingService

logger = logging.getLogger(__name__)

# RRF（Reciprocal Rank Fusion）の定数。小さいほど上位の順位を重視する
RRF_K = 60


class ArticleService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ArticleRepository(db)

    # --- CRUD ---

    async def get(self, article_id: int) -> Article | None:
        return await self.repo.get(article_id)

    async def list_paginated(
        self, cursor: str | None, page_size: int, q: str | None, category: str | None
    ) -> PaginatedArticles:
        decoded = decode_cursor(cursor) if cursor else None
        rows = await self.repo.list_keyset(page_size, decoded, q, category)
        total, relation = await self._count_total(q, category)

        # page_size + 1 件取得しているため、超過分の有無が次ページ有無
        has_next = len(rows) > page_size
        articles = rows[:page_size]
        next_cursor = (
            encode_cursor(articles[-1].published_at, articles[-1].id)
            if has_next
            else None
        )

        return PaginatedArticles(
            items=[ArticleListItem.from_article(a) for a in articles],
            total=total,
            total_relation=relation,
            page_size=page_size,
            next_cursor=next_cursor,
        )

    async def _count_total(
        self, q: str | None, category: str | None
    ) -> tuple[int, TotalRelation]:
        """一覧の総件数を返す。正確な COUNT(*) は件数に比例して重くなるため、

        - フィルタなし: プランナ統計による概算（approx）。統計未収集時のみ
          上限付きカウントにフォールバック
        - フィルタあり: 上限（list_count_cap）まで数えて打ち切り。
          上限未満なら正確（eq）、到達したら下限値として返す（gte）
        """
        cap = get_settings().list_count_cap

        if not q and not category:
            estimate = await self.repo.estimate_total()
            if estimate is not None:
                return estimate, "approx"

        total, is_exact = await self.repo.count_capped(q, category, cap)
        return total, "eq" if is_exact else "gte"

    async def create(self, payload: ArticleCreate) -> Article:
        article = Article(**payload.model_dump())
        article.embedding = await self._embed(article.title, article.content)
        self.repo.add(article)
        await self.db.commit()
        await self.db.refresh(article)
        return article

    async def update(self, article_id: int, payload: ArticleUpdate) -> Article | None:
        article = await self.repo.get(article_id)
        if article is None:
            return None

        changes = payload.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(article, field, value)

        # 検索対象テキストが変わった場合のみ Embedding を再計算
        if "title" in changes or "content" in changes:
            article.embedding = await self._embed(article.title, article.content)

        await self.db.commit()
        await self.db.refresh(article)
        return article

    async def delete(self, article_id: int) -> bool:
        deleted = await self.repo.delete(article_id)
        if deleted:
            await self.db.commit()
        return deleted

    async def list_categories(self) -> list[str]:
        return await self.repo.list_categories()

    # --- 検索 ---

    async def search(self, q: str, mode: SearchMode, limit: int) -> SearchResponse:
        if mode == SearchMode.keyword:
            pairs = await self.repo.keyword_search(
                q, limit, get_settings().keyword_candidate_cap
            )
        elif mode == SearchMode.semantic:
            query_vector = await EmbeddingService.embed_query_async(q)
            pairs = await self.repo.semantic_search(query_vector, limit)
        else:
            pairs = await self._hybrid_search(q, limit)

        return SearchResponse(
            mode=mode,
            query=q,
            results=[
                SearchResultItem(
                    article=ArticleListItem.from_article(a), score=round(score, 4)
                )
                for a, score in pairs
            ],
        )

    async def _hybrid_search(self, q: str, limit: int) -> list[tuple[Article, float]]:
        """キーワード検索とセマンティック検索を RRF で統合する。

        スコアのスケールが異なる 2 つのランキングを、順位ベースで
        安定的に融合できるため RRF を採用。
        """
        query_vector = await EmbeddingService.embed_query_async(q)
        keyword_results = await self.repo.keyword_search(
            q, limit * 2, get_settings().keyword_candidate_cap
        )
        semantic_results = await self.repo.semantic_search(query_vector, limit * 2)

        scores: dict[int, float] = {}
        articles: dict[int, Article] = {}
        for results in (keyword_results, semantic_results):
            for rank, (article, _) in enumerate(results):
                articles[article.id] = article
                scores[article.id] = scores.get(article.id, 0.0) + 1.0 / (
                    RRF_K + rank + 1
                )

        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:limit]
        return [(articles[article_id], score) for article_id, score in ranked]

    # --- 内部 ---

    @staticmethod
    async def _embed(title: str, content: str) -> list[float]:
        text = EmbeddingService.build_passage_text(title, content)
        vectors = await EmbeddingService.embed_passages_async([text])
        return vectors[0]

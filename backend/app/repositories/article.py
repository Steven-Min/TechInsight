"""記事リポジトリ。DB アクセスをこの層に集約する。"""

from sqlalchemy import Select, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article


class ArticleRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # --- 取得 ---

    async def get(self, article_id: int) -> Article | None:
        return await self.db.get(Article, article_id)

    def _apply_filters(
        self, stmt: Select, q: str | None, category: str | None
    ) -> Select:
        if q:
            # pg_trgm の GIN インデックスが効く ILIKE 部分一致（日本語にも有効）
            pattern = f"%{q}%"
            stmt = stmt.where(
                or_(Article.title.ilike(pattern), Article.content.ilike(pattern))
            )
        if category:
            stmt = stmt.where(Article.category == category)
        return stmt

    async def list_paginated(
        self,
        page: int,
        page_size: int,
        q: str | None = None,
        category: str | None = None,
    ) -> tuple[list[Article], int]:
        base = select(Article)
        base = self._apply_filters(base, q, category)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = (
            base.order_by(
                Article.published_at.desc().nulls_last(), Article.id.desc()
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self.db.execute(stmt)).scalars().all()
        return list(rows), total

    async def keyword_search(self, q: str, limit: int) -> list[tuple[Article, float]]:
        """pg_trgm の類似度を併用したキーワード検索。"""
        pattern = f"%{q}%"
        sim = func.greatest(
            func.similarity(Article.title, q),
            func.similarity(func.left(Article.content, 1000), q),
        )
        stmt = (
            select(Article, sim.label("score"))
            .where(
                or_(Article.title.ilike(pattern), Article.content.ilike(pattern))
            )
            .order_by(sim.desc(), Article.published_at.desc().nulls_last())
            .limit(limit)
        )
        rows = (await self.db.execute(stmt)).all()
        return [(row.Article, float(row.score or 0.0)) for row in rows]

    async def semantic_search(
        self, query_vector: list[float], limit: int
    ) -> list[tuple[Article, float]]:
        """pgvector（HNSW）によるコサイン類似度検索。"""
        distance = Article.embedding.cosine_distance(query_vector)
        stmt = (
            select(Article, distance.label("distance"))
            .where(Article.embedding.is_not(None))
            .order_by(distance)
            .limit(limit)
        )
        rows = (await self.db.execute(stmt)).all()
        # コサイン距離 -> 類似度（1 - distance）に変換して返す
        return [(row.Article, 1.0 - float(row.distance)) for row in rows]

    async def list_categories(self) -> list[str]:
        stmt = (
            select(Article.category)
            .where(Article.category.is_not(None))
            .distinct()
            .order_by(Article.category)
        )
        return list((await self.db.execute(stmt)).scalars().all())

    # --- 変更 ---

    def add(self, article: Article) -> None:
        self.db.add(article)

    async def delete(self, article_id: int) -> bool:
        result = await self.db.execute(
            delete(Article).where(Article.id == article_id)
        )
        return result.rowcount > 0

"""記事リポジトリ。DB アクセスをこの層に集約する。"""

from datetime import datetime

from sqlalchemy import Select, and_, delete, func, or_, select, text, tuple_
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

    # ソートキー。NULLS LAST 相当を COALESCE('-infinity') で表現することで、
    # keyset 述語（行値比較）と ORDER BY の両方で複合式インデックスが効く
    _sort_key = func.coalesce(
        Article.published_at, text("'-infinity'::timestamptz")
    )

    async def list_keyset(
        self,
        page_size: int,
        cursor: tuple[datetime | None, int] | None = None,
        q: str | None = None,
        category: str | None = None,
    ) -> list[Article]:
        """keyset（カーソル）方式の一覧取得。

        OFFSET はスキップ行数に比例して劣化するため、「直前ページ最終行の
        ソートキーより後ろ」を行値比較で取得する。ページ深度によらず一定コスト。
        次ページ有無の判定用に page_size + 1 件返す（呼び出し側で切り詰める）。
        """
        stmt = select(Article)
        stmt = self._apply_filters(stmt, q, category)

        if cursor is not None:
            published_at, article_id = cursor
            if published_at is not None:
                stmt = stmt.where(
                    tuple_(self._sort_key, Article.id)
                    < tuple_(published_at, article_id)
                )
            else:
                # カーソル行が published_at NULL（ソート末尾グループ）の場合、
                # 残りは同グループ内で id が小さい行のみ
                stmt = stmt.where(
                    and_(Article.published_at.is_(None), Article.id < article_id)
                )

        stmt = stmt.order_by(self._sort_key.desc(), Article.id.desc()).limit(
            page_size + 1
        )
        rows = (await self.db.execute(stmt)).scalars().all()
        return list(rows)

    async def estimate_total(self) -> int | None:
        """プランナ統計（pg_class.reltuples）による全件数の概算値。

        正確な COUNT(*) は件数に比例してコストが増えるため、フィルタなしの
        一覧ではこの概算を用いる。ANALYZE 未実行（reltuples <= 0）の場合は
        None を返し、呼び出し側で上限付きカウントにフォールバックする。
        """
        result = await self.db.execute(
            text(
                "SELECT reltuples::bigint FROM pg_class "
                "WHERE oid = 'articles'::regclass"
            )
        )
        value = result.scalar_one_or_none()
        if value is None or value <= 0:
            return None
        return int(value)

    async def count_capped(
        self, q: str | None, category: str | None, cap: int
    ) -> tuple[int, bool]:
        """フィルタ適用後の件数を cap + 1 件まで数えて打ち切る。

        戻り値は (件数, 正確かどうか)。cap 超過時は (cap, False) を返し、
        ヒット数が莫大なクエリでも count のコストを一定に抑える。
        """
        base = select(Article.id)
        base = self._apply_filters(base, q, category)
        subq = base.limit(cap + 1).subquery()
        count_stmt = select(func.count()).select_from(subq)
        n = (await self.db.execute(count_stmt)).scalar_one()
        if n > cap:
            return cap, False
        return n, True

    async def keyword_search(
        self, q: str, limit: int, candidate_cap: int = 1_000
    ) -> list[tuple[Article, float]]:
        """pg_trgm の類似度を併用したキーワード検索（候補打ち切り方式）。

        マッチ全件を similarity() でスコアリングするとヒット数に比例して
        遅くなるため、2段構成にする:
          1. trigram インデックスで候補を candidate_cap 件まで取得して打ち切り
          2. 候補のみスコアリングして上位 limit 件を返す
        ヒット数がいくら多くても、ヒープ読取・スコア計算・ソートのコストが
        candidate_cap で頭打ちになる（再現率とのトレードオフは docs 参照）。
        """
        pattern = f"%{q}%"
        candidates = (
            select(Article.id)
            .where(
                or_(Article.title.ilike(pattern), Article.content.ilike(pattern))
            )
            .limit(candidate_cap)
            .subquery()
        )
        sim = func.greatest(
            func.similarity(Article.title, q),
            func.similarity(func.left(Article.content, 1000), q),
        )
        stmt = (
            select(Article, sim.label("score"))
            .join(candidates, Article.id == candidates.c.id)
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

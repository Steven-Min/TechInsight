"""一覧APIの件数カウント戦略（概算 / 上限打ち切り）のテスト。

DB を使わず、リポジトリをスタブに差し替えてサービス層の分岐を検証する。
"""

import asyncio

from app.services.article import ArticleService


class StubRepo:
    def __init__(
        self,
        estimate: int | None = None,
        capped: tuple[int, bool] = (0, True),
        rows: list | None = None,
    ):
        self._estimate = estimate
        self._capped = capped
        self._rows = rows or []
        self.estimate_calls = 0
        self.capped_calls: list[tuple] = []

    async def list_keyset(self, page_size, cursor=None, q=None, category=None):
        return self._rows

    async def estimate_total(self):
        self.estimate_calls += 1
        return self._estimate

    async def count_capped(self, q, category, cap):
        self.capped_calls.append((q, category, cap))
        return self._capped


def make_service(repo: StubRepo) -> ArticleService:
    service = ArticleService.__new__(ArticleService)
    service.db = None  # list_paginated は DB を直接触らない
    service.repo = repo
    return service


class TestCountStrategy:
    def test_unfiltered_uses_estimate(self):
        repo = StubRepo(estimate=5000)
        result = asyncio.run(make_service(repo).list_paginated(None, 12, None, None))
        assert result.total == 5000
        assert result.total_relation == "approx"
        assert repo.capped_calls == []  # 正確な count は実行しない

    def test_unfiltered_falls_back_when_no_statistics(self):
        repo = StubRepo(estimate=None, capped=(42, True))
        result = asyncio.run(make_service(repo).list_paginated(None, 12, None, None))
        assert result.total == 42
        assert result.total_relation == "eq"

    def test_filtered_exact_under_cap(self):
        repo = StubRepo(capped=(120, True))
        result = asyncio.run(
            make_service(repo).list_paginated(None, 12, "docker", None)
        )
        assert result.total == 120
        assert result.total_relation == "eq"
        assert repo.estimate_calls == 0  # フィルタ付きは統計概算を使わない

    def test_filtered_capped_returns_gte(self):
        repo = StubRepo(capped=(10_000, False))
        result = asyncio.run(
            make_service(repo).list_paginated(None, 12, None, "Backend")
        )
        assert result.total == 10_000
        assert result.total_relation == "gte"

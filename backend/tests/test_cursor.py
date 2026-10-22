"""keyset ページネーションのカーソルコーデックとページ送りロジックのテスト。"""

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.core.cursor import InvalidCursorError, decode_cursor, encode_cursor
from tests.test_count_strategy import StubRepo, make_service


class TestCursorCodec:
    def test_roundtrip(self):
        dt = datetime(2026, 1, 15, 12, 30, tzinfo=UTC)
        cursor = encode_cursor(dt, 42)
        assert decode_cursor(cursor) == (dt, 42)

    def test_roundtrip_null_published_at(self):
        cursor = encode_cursor(None, 7)
        assert decode_cursor(cursor) == (None, 7)

    def test_opaque_urlsafe(self):
        cursor = encode_cursor(datetime(2026, 1, 1, tzinfo=UTC), 1)
        assert "=" not in cursor
        assert "+" not in cursor and "/" not in cursor

    @pytest.mark.parametrize("raw", ["", "!!!", "bm90LWpzb24", "eyJwIjogMX0"])
    def test_invalid_cursor_raises(self, raw: str):
        with pytest.raises(InvalidCursorError):
            decode_cursor(raw)


def _article(article_id: int) -> SimpleNamespace:
    return SimpleNamespace(
        id=article_id,
        title=f"t{article_id}",
        content="c",
        category=None,
        tags=[],
        author=None,
        published_at=datetime(2026, 1, 1, tzinfo=UTC),
        updated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


class TestKeysetPaging:
    def test_next_cursor_emitted_when_more_rows(self):
        # page_size + 1 件返る → 次ページあり。カーソルはページ最終行を指す
        repo = StubRepo(estimate=100, rows=[_article(i) for i in range(13, 0, -1)])
        result = asyncio.run(make_service(repo).list_paginated(None, 12, None, None))
        assert len(result.items) == 12
        assert result.next_cursor is not None
        assert decode_cursor(result.next_cursor)[1] == result.items[-1].id

    def test_no_next_cursor_on_last_page(self):
        repo = StubRepo(estimate=100, rows=[_article(i) for i in range(5, 0, -1)])
        result = asyncio.run(make_service(repo).list_paginated(None, 12, None, None))
        assert len(result.items) == 5
        assert result.next_cursor is None

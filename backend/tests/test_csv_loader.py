from datetime import datetime, timezone
from pathlib import Path

import pytest

from scripts.csv_loader import (
    build_column_map,
    load_articles_csv,
    parse_datetime,
    parse_tags,
)


class TestBuildColumnMap:
    def test_english_headers(self):
        mapping = build_column_map(
            ["id", "title", "content", "category", "tags", "author", "published_at"]
        )
        assert mapping["title"] == "title"
        assert mapping["content"] == "content"
        assert mapping["published_at"] == "published_at"

    def test_japanese_headers(self):
        mapping = build_column_map(["タイトル", "本文", "カテゴリ", "タグ", "著者", "公開日"])
        assert mapping["title"] == "タイトル"
        assert mapping["content"] == "本文"
        assert mapping["category"] == "カテゴリ"
        assert mapping["published_at"] == "公開日"

    def test_alternative_names(self):
        mapping = build_column_map(["Headline", "Body", "Genre", "Keywords", "Writer", "Date"])
        assert mapping["title"] == "Headline"
        assert mapping["content"] == "Body"
        assert mapping["category"] == "Genre"

    def test_no_duplicate_column_assignment(self):
        # created_at は published_at のエイリアスだが、
        # description が content に割当済みなら二重割当しない
        mapping = build_column_map(["title", "description", "created_at"])
        assert mapping["content"] == "description"
        assert mapping["published_at"] == "created_at"
        assert len(set(mapping.values())) == len(mapping)


class TestParsers:
    def test_parse_tags_variants(self):
        assert parse_tags("python, fastapi,docker") == ["python", "fastapi", "docker"]
        assert parse_tags("a;b|c、d") == ["a", "b", "c", "d"]
        assert parse_tags("") == []
        assert parse_tags(None) == []

    def test_parse_datetime_iso(self):
        dt = parse_datetime("2024-05-01T12:00:00+09:00")
        assert dt is not None
        assert dt.tzinfo is not None

    def test_parse_datetime_formats(self):
        assert parse_datetime("2024/05/01") == datetime(2024, 5, 1, tzinfo=timezone.utc)
        assert parse_datetime("2024-05-01") == datetime(2024, 5, 1, tzinfo=timezone.utc)
        assert parse_datetime("invalid") is None
        assert parse_datetime(None) is None


class TestLoadCsv:
    def test_load_basic_csv(self, tmp_path: Path):
        csv_file = tmp_path / "articles.csv"
        csv_file.write_text(
            "title,content,category,tags,author,published_at\n"
            "記事1,本文です,AI,\"llm,rag\",田中,2024-01-15\n"
            ",空タイトルはスキップ,AI,,田中,2024-01-16\n",
            encoding="utf-8",
        )
        rows = load_articles_csv(csv_file)
        assert len(rows) == 1
        assert rows[0]["title"] == "記事1"
        assert rows[0]["tags"] == ["llm", "rag"]

    def test_unknown_schema_raises(self, tmp_path: Path):
        csv_file = tmp_path / "bad.csv"
        csv_file.write_text("foo,bar\n1,2\n", encoding="utf-8")
        with pytest.raises(ValueError, match="COLUMN_ALIASES"):
            load_articles_csv(csv_file)

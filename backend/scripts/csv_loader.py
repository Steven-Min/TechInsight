"""articles.csv の読み込みとカラムマッピング。

提供される CSV のカラム名の揺れ（日本語 / 英語、命名差）を吸収するため、
ヘッダーを正規化した上で既知のエイリアスへマッピングする。
未知のスキーマでも title / content 相当のカラムを推定して取り込める。
"""

import csv
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# フィールド -> 受理するカラム名（正規化後）のエイリアス
COLUMN_ALIASES: dict[str, list[str]] = {
    "title": ["title", "タイトル", "題名", "headline", "subject", "article_title", "name"],
    "content": [
        "content", "body", "text", "本文", "記事本文", "内容", "article",
        "article_body", "article_content", "description",
    ],
    "category": ["category", "カテゴリ", "カテゴリー", "genre", "topic", "ジャンル"],
    "tags": ["tags", "tag", "タグ", "keywords", "keyword", "キーワード"],
    "author": ["author", "著者", "writer", "投稿者", "created_by", "執筆者"],
    "published_at": [
        "published_at", "published", "publish_date", "published_date", "date",
        "公開日", "投稿日", "作成日", "created_at", "posted_at",
    ],
}

_DATE_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d",
    "%Y年%m月%d日",
]


def _normalize(header: str) -> str:
    return re.sub(r"[\s\-]+", "_", header.strip().lower().lstrip("﻿"))


def build_column_map(headers: list[str]) -> dict[str, str]:
    """CSV ヘッダーから {フィールド名: 実カラム名} のマップを構築する。"""
    normalized = {_normalize(h): h for h in headers}
    mapping: dict[str, str] = {}
    for field, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in normalized:
                # published_at に created_at を割り当てるのは最終手段のため、
                # 既にマップ済みのカラムは流用しない
                if normalized[alias] in mapping.values():
                    continue
                mapping[field] = normalized[alias]
                break
    return mapping


def parse_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    parts = re.split(r"[,;|、/]+", raw)
    return [p.strip() for p in parts if p.strip()][:20]


def parse_datetime(raw: str | None) -> datetime | None:
    if not raw or not raw.strip():
        return None
    value = raw.strip()
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        dt = None
        for fmt in _DATE_FORMATS:
            try:
                dt = datetime.strptime(value, fmt)
                break
            except ValueError:
                continue
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def load_articles_csv(path: Path) -> list[dict[str, Any]]:
    """CSV を読み込み、Article モデルに渡せる dict のリストを返す。"""
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        mapping = build_column_map(headers)

        if "title" not in mapping or "content" not in mapping:
            raise ValueError(
                f"CSV のカラムを解釈できません。headers={headers} mapping={mapping}. "
                "scripts/csv_loader.py の COLUMN_ALIASES にカラム名を追加してください。"
            )

        logger.info("CSV column mapping: %s", mapping)

        rows: list[dict[str, Any]] = []
        skipped = 0
        for line_no, row in enumerate(reader, start=2):
            title = (row.get(mapping["title"]) or "").strip()
            content = (row.get(mapping["content"]) or "").strip()
            if not title or not content:
                skipped += 1
                continue
            rows.append(
                {
                    "title": title[:512],
                    "content": content,
                    "category": (
                        (row.get(mapping["category"]) or "").strip()[:128] or None
                        if "category" in mapping
                        else None
                    ),
                    "tags": (
                        parse_tags(row.get(mapping["tags"]))
                        if "tags" in mapping
                        else []
                    ),
                    "author": (
                        (row.get(mapping["author"]) or "").strip()[:128] or None
                        if "author" in mapping
                        else None
                    ),
                    "published_at": (
                        parse_datetime(row.get(mapping["published_at"]))
                        if "published_at" in mapping
                        else None
                    ),
                }
            )

        if skipped:
            logger.warning("Skipped %d rows with empty title/content", skipped)
        return rows

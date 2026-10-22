# 簡易API設計書

## 1. 概要

- **ベースURL**: `http://localhost:8000/api/v1`
- **形式**: REST / JSON
- **バージョニング**: URL パスに `/v1` を付与（破壊的変更時は `/v2` を追加し並行稼働できる）
- **自動ドキュメント**: 起動後 http://localhost:8000/docs（Swagger UI）で全エンドポイントを実行可能

## 2. エンドポイント一覧

| メソッド | パス | 概要 |
|---|---|---|
| GET | `/articles` | 記事一覧（ページネーション・キーワード絞込・カテゴリ絞込） |
| GET | `/articles/search` | セマンティック / キーワード / ハイブリッド検索 |
| GET | `/articles/categories` | カテゴリ一覧（絞り込みUI用） |
| GET | `/articles/{id}` | 記事詳細 |
| POST | `/articles` | 記事作成（Embedding を同期生成） |
| PATCH | `/articles/{id}` | 記事の部分更新（title/content 変更時のみ Embedding 再生成） |
| DELETE | `/articles/{id}` | 記事削除 |
| GET | `/health`（v1外） | ヘルスチェック（compose の起動順制御にも使用） |

## 3. 詳細

### GET /articles — 記事一覧（keyset ページネーション）

| パラメータ | 型 | デフォルト | 説明 |
|---|---|---|---|
| `cursor` | string | - | 前ページのレスポンスの `next_cursor`。先頭ページは省略。不正値は 422 |
| `page_size` | int (1..100) | 12 | 1ページ件数 |
| `q` | string | - | タイトル・本文の部分一致（pg_trgm） |
| `category` | string | - | カテゴリ完全一致 |

**レスポンス 200**

```json
{
  "items": [
    {
      "id": 1,
      "title": "Implementing PostgreSQL: ...",
      "excerpt": "In this article, we will focus on...",
      "category": "Backend",
      "tags": [],
      "author": "Ito",
      "published_at": "2025-09-19T22:00:00Z",
      "updated_at": "2026-10-22T05:00:00Z"
    }
  ],
  "total": 1000,
  "total_relation": "approx",
  "page_size": 12,
  "next_cursor": "eyJwIjoiMjAyNS0wOS0xOVQyMjowMDowMCswMDowMCIsImkiOjF9"
}
```

**keyset（カーソル）方式について**

OFFSET ページネーションはスキップ行数に比例して劣化する（10万件・OFFSET 50,000 で 101ms を実測）ため、
「直前ページ最終行のソートキーより後ろ」を行値比較で取得する keyset 方式を採用。
ソートキー `(COALESCE(published_at, '-infinity') DESC, id DESC)` の複合式インデックスにより、
ページ深度によらず一定コストで取得できる。

- `next_cursor` は最終行の位置を base64url エンコードしたオペーク値。クライアントは解釈せずそのまま渡す
- `next_cursor` が `null` なら最終ページ
- 任意ページへのランダムジャンプは不可（UI は前へ/次へのみのため影響なし。「前へ」はクライアント側のカーソル履歴で実現）

> 一覧では本文全文ではなく `excerpt`（先頭200文字）を返し、転送量を抑える。

**`total_relation` — 件数の性質**（Elasticsearch の `hits.total.relation` に倣った設計）

正確な `COUNT(*)` は全件スキャンとなり件数に比例して重くなるため（10万件で約55ms を実測）、
件数の算出方法を状況で切り替え、その性質をフィールドで明示する:

| 値 | 意味 | 使われる状況 |
|---|---|---|
| `approx` | DB 統計（`pg_class.reltuples`）による概算 | フィルタなしの全件一覧 |
| `eq` | 正確な件数 | フィルタあり かつ 上限（10,000件）未満 |
| `gte` | 下限値（実際は `total` 件以上） | フィルタありのカウントが上限に到達 |

フロントエンドはそれぞれ「約 N 件 / 全 N 件 / N+ 件」と表示する。

### GET /articles/search — 意味検索

| パラメータ | 型 | デフォルト | 説明 |
|---|---|---|---|
| `q` | string (1..500) | 必須 | 自然言語クエリ |
| `mode` | `semantic` \| `keyword` \| `hybrid` | `semantic` | 検索モード |
| `limit` | int (1..50) | 12 | 取得件数 |

**レスポンス 200**

```json
{
  "mode": "semantic",
  "query": "データベースを高速化したい",
  "results": [
    { "article": { "...": "一覧と同じ形式" }, "score": 0.8732 }
  ]
}
```

- `semantic`: クエリを Embedding 化し、pgvector の HNSW インデックスでコサイン類似度上位を返す。`score` = 類似度（0〜1）
- `keyword`: pg_trgm の `similarity` を併用した部分一致。`score` = trigram 類似度
  - **候補打ち切り**: trigram インデックスで候補を上限（既定 1,000 件・`KEYWORD_CANDIDATE_CAP`）まで
    取得してからスコアリングする。ヒット数の多い語でも応答時間が頭打ちになる代わりに、
    上限超過時は候補外の文書がランキングから漏れうる（再現率とのトレードオフ）
- `hybrid`: 両者の順位を RRF（k=60）で融合。`score` = RRF スコア（キーワード側は上記の打ち切りが適用される）

### POST /articles — 作成

**リクエスト**

```json
{
  "title": "必須（1〜512文字）",
  "content": "必須",
  "category": "任意（128文字まで）",
  "tags": ["任意", "最大20個"],
  "author": "任意（128文字まで）",
  "published_at": "2026-01-01T00:00:00Z（任意）"
}
```

**レスポンス**: `201 Created` + 記事全体（`id`, `created_at`, `updated_at` 含む）

> 作成・更新時に Embedding を同期生成するため、新規記事も即座にセマンティック検索の対象になる。

### PATCH /articles/{id} — 部分更新

- 指定したフィールドのみ更新（`exclude_unset`）
- `title` / `content` が変わった場合のみ Embedding を再生成

**レスポンス**: `200 OK` + 更新後の記事 / `404` 記事なし

### DELETE /articles/{id}

**レスポンス**: `204 No Content` / `404` 記事なし

## 4. エラーレスポンス

FastAPI 標準形式に統一:

```json
{ "detail": "Article not found" }
```

| ステータス | 条件 |
|---|---|
| 400 / 422 | バリデーションエラー（型・文字数・必須欠落） |
| 404 | 記事が存在しない |
| 500 | サーバー内部エラー |

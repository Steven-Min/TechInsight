"""articles.csv が見つからない場合のフォールバック用サンプルデータ生成。

デモ・開発環境でもセマンティック検索を体験できるよう、
技術トピックに沿った記事を決定論的に生成する。
"""

import random
from datetime import UTC, datetime, timedelta
from typing import Any

TOPICS = [
    ("Python", "バックエンド", ["python", "fastapi", "asyncio"]),
    ("TypeScript", "フロントエンド", ["typescript", "react", "nextjs"]),
    ("PostgreSQL", "データベース", ["postgresql", "sql", "index"]),
    ("Docker", "インフラ", ["docker", "container", "devops"]),
    ("Kubernetes", "インフラ", ["kubernetes", "k8s", "orchestration"]),
    ("機械学習", "AI", ["machine-learning", "python", "scikit-learn"]),
    ("深層学習", "AI", ["deep-learning", "pytorch", "transformer"]),
    ("LLM", "AI", ["llm", "rag", "embedding"]),
    ("React", "フロントエンド", ["react", "hooks", "state-management"]),
    ("Go", "バックエンド", ["go", "golang", "concurrency"]),
    ("Rust", "システム", ["rust", "memory-safety", "performance"]),
    ("GraphQL", "API設計", ["graphql", "api", "schema"]),
    ("マイクロサービス", "アーキテクチャ", ["microservices", "distributed", "grpc"]),
    ("セキュリティ", "セキュリティ", ["security", "oauth", "encryption"]),
    ("CI/CD", "DevOps", ["cicd", "github-actions", "automation"]),
    ("AWS", "クラウド", ["aws", "lambda", "s3"]),
    ("監視", "SRE", ["observability", "prometheus", "grafana"]),
    ("テスト", "品質", ["testing", "pytest", "tdd"]),
    ("キャッシュ", "パフォーマンス", ["cache", "redis", "performance"]),
    ("検索", "データベース", ["search", "elasticsearch", "vector-search"]),
]

PATTERNS = [
    "{topic}入門：基礎から学ぶ実践ガイド",
    "{topic}のベストプラクティス{n}選",
    "本番環境で学んだ{topic}の落とし穴",
    "{topic}のパフォーマンスチューニング実践",
    "チーム開発における{topic}の運用ノウハウ",
    "{topic}を使ったスケーラブルな設計パターン",
    "{topic}のトラブルシューティング事例",
    "ゼロから理解する{topic}の仕組み",
]

BODY_TEMPLATE = """## はじめに

{topic}は現代のソフトウェア開発において重要な技術のひとつです。本記事では、{context}の観点から{topic}を深掘りし、実務で役立つ知見を共有します。

## 背景と課題

多くの開発チームが{topic}の導入時に直面する課題として、学習コストの高さ、既存システムとの整合性、運用負荷の増大が挙げられます。特に{category}領域では、{challenge}が大きなテーマとなります。

## 実践アプローチ

1. 小さく始めて段階的に適用範囲を広げる
2. 計測に基づいて意思決定を行う（推測しない）
3. ドキュメントとレビュー文化を整備し、知識の属人化を防ぐ

{detail}

## まとめ

{topic}を効果的に活用するには、技術的な理解だけでなく、チームの開発プロセスへの統合が不可欠です。本記事で紹介したアプローチが、皆さんのプロジェクトの参考になれば幸いです。
"""

CHALLENGES = [
    "スループットとレイテンシのトレードオフ",
    "可用性とデータ整合性の両立",
    "開発速度と品質のバランス",
    "コストとスケーラビリティの最適化",
]

DETAILS = [
    "実際のプロジェクトでは、負荷テストの結果を踏まえてボトルネックを特定し、インデックス設計やクエリの見直しを行いました。その結果、レスポンスタイムを約60%改善できました。",
    "導入初期はチーム内の知見が不足していたため、週次の勉強会とペアプログラミングを実施しました。3ヶ月後には全メンバーが自走できる状態になりました。",
    "障害対応の経験から、アラートの閾値設計とランブックの整備が重要であることを学びました。オンコール負荷は半減し、MTTRも大幅に短縮されました。",
    "段階的なマイグレーション戦略を採用し、カナリアリリースでリスクを最小化しました。ロールバック手順を事前に整備したことが功を奏しました。",
]

AUTHORS = ["田中太郎", "佐藤花子", "鈴木一郎", "高橋美咲", "伊藤健太", "渡辺由美"]


def generate_sample_articles(count: int = 1000) -> list[dict[str, Any]]:
    rng = random.Random(42)  # 再現性のため固定シード
    base_date = datetime(2024, 1, 1, tzinfo=UTC)
    articles: list[dict[str, Any]] = []

    for i in range(count):
        topic, category, tags = TOPICS[i % len(TOPICS)]
        pattern = PATTERNS[(i // len(TOPICS)) % len(PATTERNS)]
        title = pattern.format(topic=topic, n=rng.randint(3, 10))
        body = BODY_TEMPLATE.format(
            topic=topic,
            category=category,
            context=rng.choice(["設計", "運用", "パフォーマンス", "チーム開発"]),
            challenge=rng.choice(CHALLENGES),
            detail=rng.choice(DETAILS),
        )
        articles.append(
            {
                "title": f"{title} (#{i + 1})",
                "content": body,
                "category": category,
                "tags": tags,
                "author": rng.choice(AUTHORS),
                "published_at": base_date + timedelta(hours=rng.randint(0, 24 * 700)),
            }
        )
    return articles

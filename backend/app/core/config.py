from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリケーション設定。環境変数から読み込む。"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "TechInsight API"
    debug: bool = False

    database_url: str = (
        "postgresql+asyncpg://techinsight:techinsight@localhost:54320/techinsight"
    )

    # Embedding
    embedding_model: str = "intfloat/multilingual-e5-small"
    embedding_dim: int = 384
    # e5 系モデルは passage / query プレフィックスを付与する学習がされている
    passage_prefix: str = "passage: "
    query_prefix: str = "query: "
    # 本文が長い場合に Embedding 対象として使う先頭文字数（e5-small は 512 トークン上限）
    embedding_text_limit: int = 1600

    # Seed
    seed_csv_path: str = "data/articles.csv"
    seed_fallback_count: int = 1000

    # 一覧APIの件数カウント上限。フィルタ付き一覧はこの件数まで数えて打ち切り、
    # 超過時は total_relation = "gte" として返す（全件スキャンの肥大化を防ぐ）
    list_count_cap: int = 10_000

    # キーワード検索で similarity スコアリングの対象とする候補数の上限。
    # ヒット数の多い語でも、スコア計算・ソートのコストをこの件数で頭打ちにする
    keyword_candidate_cap: int = 1_000

    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

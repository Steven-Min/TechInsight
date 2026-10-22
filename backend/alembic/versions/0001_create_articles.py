"""create articles table

Revision ID: 0001
Revises:
Create Date: 2026-10-22

1万件超のデータ量を想定したインデックス設計:
- embedding: HNSW（pgvector）。IVFFlat と異なりデータ投入後の再構築が不要で、
  件数が増えても再現率と速度のバランスが良い
- title / content: pg_trgm GIN。日本語を含む部分一致（ILIKE）を高速化
- published_at / category / tags: 一覧・絞り込みクエリ用
"""
from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "articles",
        sa.Column(
            "id", sa.BigInteger(), sa.Identity(always=True), primary_key=True
        ),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=128), nullable=True),
        sa.Column(
            "tags",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::text[]"),
        ),
        sa.Column("author", sa.String(length=128), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("embedding", Vector(384), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # セマンティック検索用 ANN インデックス
    op.execute(
        """
        CREATE INDEX ix_articles_embedding_hnsw
        ON articles USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )

    # キーワード検索（ILIKE / similarity）用 trigram インデックス
    op.execute(
        "CREATE INDEX ix_articles_title_trgm ON articles USING gin (title gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX ix_articles_content_trgm ON articles USING gin (content gin_trgm_ops)"
    )

    # 一覧表示・絞り込み用
    op.create_index(
        "ix_articles_published_at",
        "articles",
        [sa.text("published_at DESC NULLS LAST")],
    )
    op.create_index("ix_articles_category", "articles", ["category"])
    op.execute("CREATE INDEX ix_articles_tags ON articles USING gin (tags)")


def downgrade() -> None:
    op.drop_table("articles")

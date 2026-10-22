"""keyset pagination index

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-22

keyset（カーソル）ページネーション用の複合式インデックスを追加する。

ソート順 "published_at DESC NULLS LAST, id DESC" を
"COALESCE(published_at, '-infinity') DESC, id DESC" として表現することで、
行値比較（keyset 述語）と ORDER BY の両方でインデックスを使えるようにする。
単独の published_at インデックスは本インデックスで代替されるため削除。
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX ix_articles_published_at_id
        ON articles ((COALESCE(published_at, '-infinity'::timestamptz)) DESC, id DESC)
        """
    )
    op.execute("DROP INDEX IF EXISTS ix_articles_published_at")


def downgrade() -> None:
    op.create_index(
        "ix_articles_published_at",
        "articles",
        [sa.text("published_at DESC NULLS LAST")],
    )
    op.execute("DROP INDEX IF EXISTS ix_articles_published_at_id")

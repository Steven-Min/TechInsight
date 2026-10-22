"""初期データ投入スクリプト（冪等）。

docker compose up 時に entrypoint から実行される。
1. articles テーブルが空の場合のみ実行（再起動時はスキップ）
2. SEED_CSV_PATH の CSV を取り込む。無ければサンプルデータを生成
3. 記事をバッチ INSERT した後、Embedding をバッチ生成して UPDATE

1万件規模を想定し、INSERT / Embedding 生成ともにバッチ処理で行う。
"""

import asyncio
import logging
import sys
from pathlib import Path

from sqlalchemy import func, select, update

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal, engine
from app.models.article import Article
from app.services.embedding import EmbeddingService
from scripts.csv_loader import load_articles_csv
from scripts.sample_data import generate_sample_articles

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s"
)
logger = logging.getLogger("seed")

settings = get_settings()

INSERT_BATCH_SIZE = 500
EMBEDDING_BATCH_SIZE = 64


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        count = (
            await session.execute(select(func.count()).select_from(Article))
        ).scalar_one()
        if count > 0:
            logger.info("articles table already has %d rows. Skipping seed.", count)
            return

    rows = load_rows()
    logger.info("Inserting %d articles...", len(rows))

    async with AsyncSessionLocal() as session:
        for i in range(0, len(rows), INSERT_BATCH_SIZE):
            batch = rows[i : i + INSERT_BATCH_SIZE]
            session.add_all([Article(**row) for row in batch])
            await session.commit()
            logger.info("Inserted %d / %d", min(i + INSERT_BATCH_SIZE, len(rows)), len(rows))

    await generate_embeddings()
    logger.info("Seed completed.")


def load_rows() -> list[dict]:
    csv_path = Path(settings.seed_csv_path)
    if csv_path.exists():
        logger.info("Loading articles from %s", csv_path)
        rows = load_articles_csv(csv_path)
        logger.info("Loaded %d articles from CSV", len(rows))
        return rows

    logger.warning(
        "CSV not found at %s. Generating %d sample articles instead. "
        "(data/articles.csv を配置して db ボリュームを削除後に再起動すると実データを取り込めます)",
        csv_path,
        settings.seed_fallback_count,
    )
    return generate_sample_articles(settings.seed_fallback_count)


async def generate_embeddings() -> None:
    """embedding が NULL の記事に対してベクトルをバッチ生成する。"""
    EmbeddingService.load()

    async with AsyncSessionLocal() as session:
        total = (
            await session.execute(
                select(func.count())
                .select_from(Article)
                .where(Article.embedding.is_(None))
            )
        ).scalar_one()

        done = 0
        while True:
            result = await session.execute(
                select(Article.id, Article.title, Article.content)
                .where(Article.embedding.is_(None))
                .order_by(Article.id)
                .limit(EMBEDDING_BATCH_SIZE)
            )
            batch = result.all()
            if not batch:
                break

            texts = [
                EmbeddingService.build_passage_text(title, content)
                for _, title, content in batch
            ]
            vectors = await EmbeddingService.embed_passages_async(texts)

            for (article_id, _, _), vector in zip(batch, vectors, strict=True):
                await session.execute(
                    update(Article)
                    .where(Article.id == article_id)
                    .values(embedding=vector)
                )
            await session.commit()

            done += len(batch)
            logger.info("Embeddings generated: %d / %d", done, total)


async def main() -> None:
    try:
        await seed()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        logger.exception("Seed failed")
        sys.exit(1)

"""Embedding 生成サービス。

intfloat/multilingual-e5-small（384次元・多言語対応）を使用する。
e5 系モデルの仕様に従い、文書には "passage: "、検索クエリには
"query: " のプレフィックスを付与し、正規化済みベクトルを返す。
正規化済みのためコサイン類似度 = 内積として扱える。
"""

import asyncio
import logging
import threading

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmbeddingService:
    """SentenceTransformer モデルのシングルトンラッパー。"""

    _model = None
    _lock = threading.Lock()

    @classmethod
    def load(cls):
        """モデルをロードする（初回のみ）。スレッドセーフ。"""
        if cls._model is None:
            with cls._lock:
                if cls._model is None:
                    from sentence_transformers import SentenceTransformer

                    logger.info("Loading embedding model: %s", settings.embedding_model)
                    cls._model = SentenceTransformer(settings.embedding_model)
                    logger.info("Embedding model loaded")
        return cls._model

    @classmethod
    def build_passage_text(cls, title: str, content: str) -> str:
        """記事から Embedding 対象テキストを組み立てる。

        タイトルは意味情報が凝縮されているため必ず含め、
        本文はモデルのトークン上限を考慮して先頭のみ使用する。
        """
        return f"{title}\n{content[: settings.embedding_text_limit]}"

    @classmethod
    def embed_passages(cls, texts: list[str]) -> list[list[float]]:
        model = cls.load()
        prefixed = [settings.passage_prefix + t for t in texts]
        vectors = model.encode(
            prefixed, normalize_embeddings=True, show_progress_bar=False
        )
        return [v.tolist() for v in vectors]

    @classmethod
    def embed_query(cls, query: str) -> list[float]:
        model = cls.load()
        vector = model.encode(
            settings.query_prefix + query,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vector.tolist()

    # --- 非同期ラッパー（推論はCPUバウンドなのでスレッドプールへ逃がす） ---

    @classmethod
    async def embed_passages_async(cls, texts: list[str]) -> list[list[float]]:
        return await asyncio.to_thread(cls.embed_passages, texts)

    @classmethod
    async def embed_query_async(cls, query: str) -> list[float]:
        return await asyncio.to_thread(cls.embed_query, query)

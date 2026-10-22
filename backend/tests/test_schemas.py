import pytest
from pydantic import ValidationError

from app.schemas.article import ArticleCreate, ArticleUpdate


class TestArticleCreate:
    def test_valid(self):
        article = ArticleCreate(title="テスト記事", content="本文")
        assert article.tags == []
        assert article.category is None

    def test_empty_title_rejected(self):
        with pytest.raises(ValidationError):
            ArticleCreate(title="", content="本文")

    def test_title_too_long_rejected(self):
        with pytest.raises(ValidationError):
            ArticleCreate(title="a" * 513, content="本文")


class TestArticleUpdate:
    def test_partial_update_only_sets_given_fields(self):
        update = ArticleUpdate(title="新タイトル")
        assert update.model_dump(exclude_unset=True) == {"title": "新タイトル"}

    def test_empty_content_rejected(self):
        with pytest.raises(ValidationError):
            ArticleUpdate(content="")

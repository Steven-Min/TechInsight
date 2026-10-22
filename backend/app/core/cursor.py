"""keyset ページネーションのカーソルコーデック。

カーソルは「直前ページ最終行のソートキー (published_at, id)」を
base64url でエンコードしたオペーク文字列。クライアントは中身を解釈せず、
そのまま次のリクエストに渡す。
"""

import base64
import binascii
import json
from datetime import datetime


class InvalidCursorError(ValueError):
    pass


def encode_cursor(published_at: datetime | None, article_id: int) -> str:
    payload = {
        "p": published_at.isoformat() if published_at is not None else None,
        "i": article_id,
    }
    raw = json.dumps(payload, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(cursor: str) -> tuple[datetime | None, int]:
    """カーソル文字列を (published_at, id) に復元する。

    不正な値は InvalidCursorError（API 層で 422 に変換）。
    """
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode()))
        published_at = (
            datetime.fromisoformat(payload["p"]) if payload["p"] is not None else None
        )
        article_id = payload["i"]
        if not isinstance(article_id, int):
            raise TypeError("id must be int")
        return published_at, article_id
    except (KeyError, TypeError, ValueError, binascii.Error) as exc:
        raise InvalidCursorError(f"Invalid cursor: {cursor!r}") from exc

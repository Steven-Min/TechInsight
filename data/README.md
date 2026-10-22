# data/

提供された `articles.csv`（1,000件）をこのディレクトリに配置してください。

```
data/articles.csv
```

- `docker compose up` 時の初回シードで自動的に取り込まれ、Embedding が生成されます
- CSV が存在しない場合は、デモ用のサンプル記事1,000件が自動生成されます
- カラム名は日本語 / 英語の揺れを自動マッピングします（`backend/scripts/csv_loader.py` 参照）
- 既にシード済みの DB を作り直して再取込する場合:

```bash
docker compose down -v   # DB ボリュームごと削除
docker compose up --build
```

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/opt/hf-cache

WORKDIR /app

# 依存関係のインストール（torch は CPU 版を優先的に解決）
COPY requirements.txt .
RUN pip install -r requirements.txt \
    --extra-index-url https://download.pytorch.org/whl/cpu

# Embedding モデルをイメージに焼き込み、起動時のダウンロードを不要にする
RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('intfloat/multilingual-e5-small')"

COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]

# syntax=docker/dockerfile:1
FROM python:3.12-slim AS app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app
COPY pyproject.toml README.md ./
COPY touchline ./touchline
RUN pip install ".[foundry]"
COPY web ./web
COPY docs ./docs

RUN useradd --create-home --uid 10001 touchline
USER touchline
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request,os;urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/api/health')"
CMD ["sh", "-c", "uvicorn touchline.server.app:app --host 0.0.0.0 --port ${PORT} --proxy-headers --ws-ping-interval 20"]

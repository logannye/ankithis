FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim

WORKDIR /app

RUN adduser --system --no-create-home appuser

COPY --from=builder /install /usr/local
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh && mkdir -p /app/data/uploads && chown appuser /app/data/uploads

USER appuser

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]

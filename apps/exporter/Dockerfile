FROM python:3.12-alpine3.21 AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml ./

RUN uv sync --no-dev --frozen 2>/dev/null || uv sync --no-dev

COPY src/ ./src/

RUN mkdir -p /var/lib/exporter && \
    adduser -D -u 1000 exporter && \
    chown -R exporter:exporter /app /var/lib/exporter

USER exporter

ENV SIEM_STATE_FILE_PATH=/var/lib/exporter/state.json
ENV SIEM_LOG_LEVEL=INFO

CMD ["uv", "run", "python", "-m", "src.main"]
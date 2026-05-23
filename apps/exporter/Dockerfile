FROM python:3.12-alpine3.21 AS base

COPY --from=ghcr.io/astral-sh/uv:0.11.14 /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

COPY apps/exporter ./apps/exporter

RUN uv sync --project ./apps/exporter --no-dev --frozen

RUN mkdir -p /var/lib/exporter && \
    adduser -D -u 1000 exporter && \
    chown -R exporter:exporter /app /var/lib/exporter

USER exporter

WORKDIR /app/apps/exporter

ENV SIEM_STATE_FILE_PATH=/var/lib/exporter/state.json
ENV SIEM_LOG_LEVEL=INFO

CMD ["uv", "run", "python", "-m", "src.main"]
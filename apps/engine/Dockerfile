FROM python:3.12-alpine3.21

COPY --from=ghcr.io/astral-sh/uv:0.11.14 /uv /usr/local/bin/uv

WORKDIR /app

COPY uv.lock ./

COPY pyproject.toml ./

COPY apps/engine ./apps/engine

RUN uv sync --project ./apps/engine --no-dev --frozen

RUN adduser -D -u 1000 engine && chown -R engine:engine /app

USER engine

WORKDIR /app/apps/engine

EXPOSE 8000

CMD ["uv", "run", "python", "-m", "src.main"]
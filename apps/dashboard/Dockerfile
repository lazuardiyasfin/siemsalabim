# Build frontend
FROM node:24-alpine AS frontend-builder

WORKDIR /build/frontend

COPY apps/dashboard/frontend/package*.json ./

RUN npm ci

COPY apps/dashboard/frontend .

ARG VITE_API_BASE_URL

ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# Final image
FROM python:3.12-alpine3.21

COPY --from=ghcr.io/astral-sh/uv:0.11.14 /uv /usr/local/bin/uv

WORKDIR /app

COPY uv.lock ./

COPY pyproject.toml ./

COPY apps/dashboard/backend/pyproject.toml ./apps/dashboard/backend/

RUN uv sync --project ./apps/dashboard/backend --no-dev --frozen

COPY apps/dashboard/backend ./apps/dashboard/backend

COPY --from=frontend-builder /build/frontend/dist ./apps/dashboard/frontend/dist

RUN adduser -D -u 1000 dashboard && chown -R dashboard:dashboard /app

USER dashboard

EXPOSE 8001

ENV PYTHONPATH=/app/apps/dashboard/backend/src

CMD ["uv", "run", "--project", "./apps/dashboard/backend", "python", "-m", "dashboard-backend.main"]
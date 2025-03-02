FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS uv

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-install-project --no-dev --no-editable

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-dev --no-editable

FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  PATH="/app/.venv/bin:$PATH"

RUN groupadd -r app && \
  useradd -r -g app -d /app -s /bin/bash app && \
  mkdir -p /app && \
  chown app:app /app

WORKDIR /app

COPY --from=uv --chown=app:app /app/.venv /app/.venv

USER app

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD ["time-mcp-server", "--help"] || exit 1

ENTRYPOINT ["time-mcp-server"]

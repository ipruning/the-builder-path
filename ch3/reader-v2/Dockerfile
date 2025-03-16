FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

RUN apt-get update && apt-get install -y \
  build-essential \
  curl \
  swig \
  && rm -rf /var/lib/apt/lists/*

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

COPY --from=builder --chown=app:app /app/.venv /app/.venv

COPY ./src ./src
COPY ./main.py ./main.py
COPY ./config/deploy.yml ./config/deploy.yml
COPY ./static ./static

USER app

EXPOSE 5001

HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5001/up').getcode() == 200 or exit(1)"

CMD ["python", "main.py"]

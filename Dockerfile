FROM ghcr.io/astral-sh/uv:0.9.2-python3.11-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-install-project --no-dev --extra pdf

COPY app ./app
COPY README.md ./README.md

RUN uv sync --frozen --no-dev --extra pdf

FROM python:3.11-slim-bookworm AS runtime

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN useradd --create-home --uid 10001 queryn

COPY --from=builder --chown=queryn:queryn /app/.venv /app/.venv
COPY --from=builder --chown=queryn:queryn /app/app /app/app

USER queryn

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

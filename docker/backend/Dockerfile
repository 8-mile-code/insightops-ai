FROM ghcr.io/astral-sh/uv:0.10.7 AS uv

FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=uv /uv /uvx /bin/

COPY pyproject.toml uv.lock ./

RUN uv sync \
    --frozen \
    --no-dev \
    --no-install-project

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY scripts ./scripts
COPY sample_data ./sample_data

RUN mkdir -p uploads/datasets

EXPOSE 8000

CMD [ "uvicorn", "app.main:app",  "--host", "0.0.0.0",  "--port", "8000"]

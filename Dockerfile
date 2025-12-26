FROM python:3.13-slim

WORKDIR /app

# Install uv and dependencies
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml ./
RUN uv sync --no-dev --no-install-project

COPY src ./src
COPY scripts ./scripts
COPY alembic ./alembic
COPY alembic.ini ./

EXPOSE 8000

CMD ["uv", "run", "fastapi", "run", "src/api/main.py", "--host", "0.0.0.0", "--port", "8000"]

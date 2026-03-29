FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock README.md ./

# Install dependencies only (not the project itself) for better layer caching
RUN uv sync --frozen --no-dev --no-install-project && \
    uv pip install unified-planning[tamer] up-lpg

# Copy application code then install the project
COPY src/ src/
RUN uv sync --frozen --no-dev

CMD ["uv", "run", "python", "-m", "temporal_strips.worker"]

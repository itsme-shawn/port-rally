FROM python:3.12-slim

ENV UV_LINK_MODE=copy
WORKDIR /app

# Install uv and sync dependencies from pyproject
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
COPY pyproject.toml /app/pyproject.toml
RUN uv sync --no-dev

# Copy source
COPY src /app/src
ENV PYTHONPATH=/app/src
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:${PATH}"

CMD ["uv", "run", "-m", "quote_pipeline.main"]

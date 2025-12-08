FROM python:3.12-slim

ENV UV_LINK_MODE=copy
WORKDIR /app

# Install uv via pip and sync dependencies
RUN pip install --no-cache-dir uv
COPY pyproject.toml README.md /app/
RUN uv sync --no-dev

# Copy source
COPY src /app/src
ENV PYTHONPATH=/app/src
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:${PATH}"

CMD ["uv", "run", "-m", "quote_pipeline.main"]

FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN uv pip install --system -r pyproject.toml

# Copy source code
COPY src/ ./src/

# Expose port
EXPOSE 4000

# Run application
CMD ["python", "-m", "advisor.main"]

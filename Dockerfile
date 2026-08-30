# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml requirements.txt ./

RUN pip install --no-cache-dir --prefix=/install "setuptools>=68" && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Production image
FROM python:3.11-slim AS production

# Add metadata
LABEL maintainer="AEGIS Team"
LABEL description="AEGIS Agentic Clinical Intelligence"
LABEL version="0.3.0"

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY src/ /app/src/
COPY data/ /app/data/
COPY benchmark.jsonl /app/

# Create non-root user
RUN useradd --create-home --shell /bin/bash --uid 1000 aegis && \
    chown -R aegis:aegis /app

USER aegis

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    AEGIS_AUTH_DISABLED=true \
    AEGIS_SECRET_KEY=change-me-in-production

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "aegis.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

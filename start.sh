#!/bin/bash
set -e

echo "Starting AEGIS Backend..."
echo "Environment: ${AEGIS_ENV:-development}"
echo "LLM Provider: ${LLM_PROVIDER:-mock}"
echo "Database: ${DATABASE_URL:-sqlite:///./aegis.db}"

# Run database migrations if needed
# python -m aegis.cli db migrate

# Start the server
exec uvicorn aegis.api:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WORKERS:-2}

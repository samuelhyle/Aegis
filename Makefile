.PHONY: install run test lint format typecheck ingest docker docker-dev benchmark clean help

# Default target
help:
	@echo "AEGIS - Agentic Clinical Intelligence"
	@echo ""
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make run           - Run development server"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linter"
	@echo "  make lint-fix      - Run linter with auto-fix"
	@echo "  make format        - Format code"
	@echo "  make typecheck     - Run type checking"
	@echo "  make ingest        - Ingest Synthea data"
	@echo "  make benchmark     - Validate benchmark"
	@echo "  make docker        - Build Docker image"
	@echo "  make docker-run    - Run Docker container"
	@echo "  make docker-dev    - Run in development mode"
	@echo "  make docker-frontend - Run with frontend"
	@echo "  make docker-production - Run in production mode"
	@echo "  make clean         - Clean build artifacts"

# Installation
install:
	python -m pip install -e ".[dev]"

install-all:
	python -m pip install -e ".[all]"

# Development
run:
	uvicorn aegis.api:app --reload --host 0.0.0.0 --port 8000

run-prod:
	uvicorn aegis.api:app --host 0.0.0.0 --port 8000 --workers 4

# Testing
test:
	pytest tests/ -q

test-verbose:
	pytest tests/ -v

test-coverage:
	pytest tests/ --cov=aegis --cov-report=html

test-auth:
	pytest tests/test_auth.py -v

test-rate-limit:
	pytest tests/test_rate_limit.py -v

test-api:
	pytest tests/test_api.py -v

# Linting and Formatting
lint:
	ruff check src tests

lint-fix:
	ruff check --fix src tests

format:
	ruff format src tests

typecheck:
	mypy src/aegis --ignore-missing-imports

# Data Management
ingest:
	aegis-ingest data/synthea

benchmark:
	@echo "Validating benchmark..."
	@python -c "import json; records = [json.loads(l) for l in open('benchmark.jsonl') if l.strip()]; print(f'{len(records)} questions'); assert len(records) >= 50"

# Docker
docker:
	docker build -t aegis:latest .

docker-run:
	docker run -p 8000:8000 aegis:latest

docker-dev:
	docker compose up aegis-dev

docker-frontend:
	docker compose --profile frontend up

docker-production:
	docker compose --profile production up -d

docker-stop:
	docker compose down

# Cleanup
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov

clean-all: clean
	rm -rf .venv node_modules web/node_modules web/.next

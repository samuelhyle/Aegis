from __future__ import annotations

import os
from functools import lru_cache


@lru_cache
def get_settings() -> dict[str, str]:
    """Get application settings from environment variables."""
    return {
        "env": os.getenv("AEGIS_ENV", "development"),
        "data_dir": os.getenv("AEGIS_DATA_DIR", "data/synthea"),
        "auth_disabled": os.getenv("AEGIS_AUTH_DISABLED", "false").lower() == "true",
        "secret_key": os.getenv("AEGIS_SECRET_KEY", "change-me-in-production"),
        "llm_provider": os.getenv("LLM_PROVIDER", "mock"),
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
        "model_name": os.getenv("MODEL_NAME", "gpt-4o-mini"),
        "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
        "database_url": os.getenv("DATABASE_URL", "sqlite:///./aegis.db"),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "otel_endpoint": os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", ""),
        "otel_service_name": os.getenv("OTEL_SERVICE_NAME", "aegis"),
        "rate_limit_enabled": os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",
        "rate_limit_rpm": int(os.getenv("RATE_LIMIT_RPM", "60")),
        "cors_origins": os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    }


def is_production() -> bool:
    return get_settings()["env"] == "production"


def is_development() -> bool:
    return get_settings()["env"] == "development"

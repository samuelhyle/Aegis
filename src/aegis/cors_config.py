"""CORS configuration for production deployment."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CORSConfig:
    """CORS configuration."""

    # Allowed origins
    allowed_origins: list[str] = field(default_factory=lambda: [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ])

    # Allow credentials (cookies, authorization headers)
    allow_credentials: bool = True

    # Allowed HTTP methods
    allowed_methods: list[str] = field(default_factory=lambda: [
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "PATCH",
        "OPTIONS",
    ])

    # Allowed headers
    allowed_headers: list[str] = field(default_factory=lambda: [
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
        "X-API-Key",
        "X-Request-ID",
    ])

    # Expose headers to the browser
    expose_headers: list[str] = field(default_factory=lambda: [
        "X-Request-ID",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
    ])

    # Max age for preflight requests (seconds)
    max_age: int = 86400  # 24 hours

    # Whether to allow all origins (development only)
    allow_all_origins: bool = False

    def get_origins(self) -> list[str] | str:
        """Get allowed origins for CORS middleware."""
        if self.allow_all_origins:
            return "*"
        return self.allowed_origins

    def to_middleware_config(self) -> dict[str, Any]:
        """Convert to FastAPI CORS middleware config."""
        return {
            "allow_origins": self.get_origins(),
            "allow_credentials": self.allow_credentials,
            "allow_methods": self.allowed_methods,
            "allow_headers": self.allowed_headers,
            "expose_headers": self.expose_headers,
            "max_age": self.max_age,
        }


def get_cors_config() -> CORSConfig:
    """Get CORS configuration based on environment."""
    env = os.getenv("AEGIS_ENV", "development")

    config = CORSConfig()

    if env == "production":
        # Production: restrict origins
        production_origins = os.getenv("AEGIS_CORS_ORIGINS", "")
        if production_origins:
            config.allowed_origins = [
                origin.strip()
                for origin in production_origins.split(",")
                if origin.strip()
            ]
        else:
            # Default production origins (empty - must be configured)
            config.allowed_origins = []

        config.allow_all_origins = False
        config.allow_credentials = True

    elif env == "staging":
        # Staging: allow specific staging domains
        staging_origins = os.getenv("AEGIS_CORS_ORIGINS", "")
        if staging_origins:
            config.allowed_origins = [
                origin.strip()
                for origin in staging_origins.split(",")
                if origin.strip()
            ]
        else:
            # Include localhost for staging testing
            config.allowed_origins = [
                "http://localhost:3000",
                "http://localhost:8000",
            ]

        config.allow_all_origins = False
        config.allow_credentials = True

    else:
        # Development: allow localhost
        config.allowed_origins = [
            "http://localhost:3000",
            "http://localhost:8000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000",
        ]
        config.allow_all_origins = False
        config.allow_credentials = True

    return config


def setup_cors(app: Any) -> None:
    """Setup CORS middleware on a FastAPI app."""
    from fastapi.middleware.cors import CORSMiddleware

    config = get_cors_config()
    middleware_config = config.to_middleware_config()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=middleware_config["allow_origins"],
        allow_credentials=middleware_config["allow_credentials"],
        allow_methods=middleware_config["allow_methods"],
        allow_headers=middleware_config["allow_headers"],
        expose_headers=middleware_config["expose_headers"],
        max_age=middleware_config["max_age"],
    )

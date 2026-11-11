"""Application settings.

Settings are read once from the environment (and ``.env``) and validated eagerly
so that an unsafe production configuration fails at start-up, not at runtime.
"""
from __future__ import annotations

import logging
import os
import secrets
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

logger = logging.getLogger("padav.config")

_TRUE = {"1", "true", "yes", "on"}
MIN_SECRET_LENGTH = 32
# Values that have shipped in templates / source and must never be used for signing.
_KNOWN_WEAK_SECRETS = {
    "dev-only-change-me-before-deploying",
    "replace-this-with-a-long-random-secret",
    "changeme",
    "secret",
}


class ConfigurationError(RuntimeError):
    """Raised when the environment describes an unsafe or invalid configuration."""


class _Env:
    """Typed accessors over ``os.environ`` (removes repeated parsing code)."""

    @staticmethod
    def text(name: str, default: str = "") -> str:
        return os.getenv(name, default).strip()

    @staticmethod
    def flag(name: str, default: bool = False) -> bool:
        raw = os.getenv(name)
        return default if raw is None else raw.strip().lower() in _TRUE

    @staticmethod
    def integer(name: str, default: int, *, minimum: int = 1) -> int:
        raw = os.getenv(name)
        try:
            value = default if raw is None else int(raw)
        except ValueError as exc:
            raise ConfigurationError(f"{name} must be an integer") from exc
        if value < minimum:
            raise ConfigurationError(f"{name} must be >= {minimum}")
        return value

    @staticmethod
    def csv(name: str, default: str = "") -> list[str]:
        return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


class Settings:
    def __init__(self) -> None:
        env = _Env
        # App
        self.app_name = env.text("APP_NAME", "Padav")
        self.environment = env.text("ENVIRONMENT", "development").lower()
        self.is_production = self.environment == "production"
        # Debug is opt-in: tracebacks must never be exposed by default.
        self.debug = env.flag("DEBUG", False)

        # API
        self.api_v1_str = "/api/v1"
        self.algorithm = "HS256"
        self.jwt_issuer = env.text("JWT_ISSUER", "padav-api")
        self.jwt_audience = env.text("JWT_AUDIENCE", "padav-web")
        self.access_token_expire_minutes = env.integer("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
        self.refresh_token_expire_days = env.integer("REFRESH_TOKEN_EXPIRE_DAYS", 7)
        self.secret_key = self._resolve_secret(env.text("SECRET_KEY"))
        self.bcrypt_rounds = env.integer("BCRYPT_ROUNDS", 12, minimum=10)

        # Database
        self.database_url = env.text("DATABASE_URL", "sqlite:///./padav.db")

        # HTTP surface
        self.backend_cors_origins = env.csv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
        self.allowed_hosts = env.csv("ALLOWED_HOSTS")  # empty = do not enforce
        self.docs_enabled = env.flag("ENABLE_DOCS", not self.is_production)
        self.seed_on_startup = env.flag("SEED_ON_STARTUP", not self.is_production)

        # Abuse protection
        self.rate_limit_enabled = env.flag("RATE_LIMIT_ENABLED", True)
        self.auth_rate_limit_per_minute = env.integer("AUTH_RATE_LIMIT_PER_MINUTE", 20)
        self.login_max_failures = env.integer("LOGIN_MAX_FAILURES", 5)
        self.login_lockout_seconds = env.integer("LOGIN_LOCKOUT_SECONDS", 900)

        # Dev launcher
        self.dev_host = env.text("DEV_HOST", "127.0.0.1")

        self._validate()

    def _resolve_secret(self, configured: str) -> str:
        if configured:
            return configured
        if self.is_production:
            raise ConfigurationError("SECRET_KEY must be set in production")
        # Never fall back to a constant that is visible in the source tree: anyone could
        # then forge tokens. An ephemeral key only invalidates sessions on restart.
        logger.warning("SECRET_KEY not set; using an ephemeral key (sessions reset on restart)")
        return secrets.token_urlsafe(48)

    def _validate(self) -> None:
        if self.is_production:
            if self.debug:
                raise ConfigurationError("DEBUG must be off in production")
            if len(self.secret_key) < MIN_SECRET_LENGTH or self.secret_key in _KNOWN_WEAK_SECRETS:
                raise ConfigurationError(
                    f"SECRET_KEY must be a random value of at least {MIN_SECRET_LENGTH} characters"
                )
            if "*" in self.backend_cors_origins:
                raise ConfigurationError("CORS_ORIGINS must list explicit origins in production")
            if not self.allowed_hosts:
                raise ConfigurationError("ALLOWED_HOSTS must be set in production")
        if "*" in self.backend_cors_origins:
            # Credentials are enabled, so a wildcard origin is never acceptable.
            raise ConfigurationError("CORS_ORIGINS must not contain '*'")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

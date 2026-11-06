import os
from functools import lru_cache
from pathlib import Path
from typing import List

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


class Settings:
    def __init__(self):
        # App
        self.app_name = "Padav"
        self.debug = os.getenv("DEBUG", "true").lower() == "true"
        self.environment = os.getenv("ENVIRONMENT", "development")

        # API
        self.api_v1_str = "/api/v1"
        self.secret_key = os.getenv("SECRET_KEY", "dev-only-change-me-before-deploying")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.refresh_token_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

        # Database
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./padav.db")

        # CORS
        configured_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
        self.backend_cors_origins: List[str] = [origin.strip() for origin in configured_origins.split(",") if origin.strip()]

        if self.environment == "production" and self.secret_key == "dev-only-change-me-before-deploying":
            raise ValueError("Set SECRET_KEY before running Padav in production")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


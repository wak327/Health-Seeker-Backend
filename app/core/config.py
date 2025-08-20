from functools import lru_cache
from typing import List

from pydantic import AnyUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    project_name: str = "Health Seeker Backend"
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"

    database_url: str = (
        "postgresql+psycopg2://postgres:postgres@postgres:5432/health_seeker"
    )

    celery_broker_url: AnyUrl = "redis://redis:6379/0"  # type: ignore[assignment]
    celery_result_backend: AnyUrl = "redis://redis:6379/1"  # type: ignore[assignment]

    enable_background_workers: bool = True
    enable_event_subscribers: bool = True

    cors_allow_origins: List[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]

    log_level: str = "INFO"

    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    superadmin_email: str | None = None
    superadmin_password: str | None = None
    superadmin_full_name: str = "Super Admin"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings instance."""

    return Settings()

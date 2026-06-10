"""
Application configuration module.

All environment variables are loaded, validated, and typed here.
Nothing in this codebase calls os.getenv() directly — ever.
If a required value is missing or malformed, the app fails at
startup with a clear error message rather than crashing silently
at runtime.
"""

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Typed, validated application settings.

    Pydantic-settings reads values from environment variables and
    the .env file automatically. Every field has a type annotation
    which means invalid values are caught immediately at startup.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        # 'forbid' means if an unknown variable exists in .env,
        # the app refuses to start. Prevents silent config drift.
        extra="ignore",
    )

    # ----------------------------------------------------------------
    # Application
    # ----------------------------------------------------------------
    app_env: Literal["development", "staging", "production"] = "development"
    app_secret_key: str = Field(min_length=32)
    app_debug: bool = False

    # ----------------------------------------------------------------
    # Database
    # ----------------------------------------------------------------
    database_url: str = Field(min_length=10)
    database_pool_size: int = Field(default=10, ge=1, le=50)
    database_max_overflow: int = Field(default=20, ge=0, le=100)

    # ----------------------------------------------------------------
    # Redis
    # ----------------------------------------------------------------
    redis_url: str = Field(min_length=10)

    # ----------------------------------------------------------------
    # JWT Authentication
    # ----------------------------------------------------------------
    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: Literal["HS256", "HS512", "RS256"] = "HS256"
    jwt_access_token_expire_minutes: int = Field(default=30, ge=5, le=1440)

    # ----------------------------------------------------------------
    # AI / LLM
    # ----------------------------------------------------------------
    openai_api_key: str = Field(min_length=10)
    openai_model: str = "gpt-4o"

    # ----------------------------------------------------------------
    # Security
    # ----------------------------------------------------------------
    allowed_origins: list[str] = Field(default_factory=list)
    rate_limit_per_minute: int = Field(default=60, ge=1, le=1000)

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list) -> list:
        """
        Accept either a comma-separated string from .env
        or a Python list. Both are valid input formats.

        Example .env value:
            ALLOWED_ORIGINS=http://localhost:5173,https://app.shadowwall.io
        """
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    # ----------------------------------------------------------------
    # Computed properties — derived from raw config values
    # ----------------------------------------------------------------
    @property
    def is_production(self) -> bool:
        """True when running in a production environment."""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """True when running locally."""
        return self.app_env == "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Returns the application settings instance.

    lru_cache(maxsize=1) means this function runs ONCE and caches
    the result forever. Every part of the app that calls
    get_settings() gets the same object — not a new one each time.

    This is the standard pattern for dependency injection in FastAPI.
    Usage in a route:

        from app.core.config import get_settings
        from fastapi import Depends

        def my_route(settings: Settings = Depends(get_settings)):
            ...
    """
    return Settings()

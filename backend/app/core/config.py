import json
from typing import Any
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings configuration using Pydantic Settings v2.

    Loads environment variables from .env file or environment overrides.
    """

    PROJECT_NAME: str = "ThirdEye - Threat Intel Core"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/thirdeye"
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        """Normalize DATABASE_URL for asyncpg driver (convert sslmode= to ssl=)."""
        if "asyncpg" in v and "sslmode=" in v:
            return v.replace("sslmode=", "ssl=")
        return v

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: Any) -> list[str]:
        """Parse ALLOWED_ORIGINS flexibly from string, comma-separated list, JSON list, or list object."""
        if isinstance(v, str):
            v_trimmed = v.strip()
            if not v_trimmed:
                return []
            if v_trimmed.startswith("[") and v_trimmed.endswith("]"):
                try:
                    parsed = json.loads(v_trimmed)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if item]
                except json.JSONDecodeError:
                    pass
            return [item.strip() for item in v_trimmed.split(",") if item.strip()]
        elif isinstance(v, list):
            return [str(item).strip() for item in v if item]
        return []


settings = Settings()

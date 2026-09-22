"""Configuration settings for the Dark Web Threat Actor Deanonymization system."""
from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Neo4j Graph Database
    NEO4J_URI: str = Field(default="bolt://localhost:7687", description="Neo4j Bolt connection URI")
    NEO4J_USER: str = Field(default="neo4j", description="Neo4j username")
    NEO4J_PASSWORD: str = Field(default="ThreatIntelSecurePass2026", description="Neo4j password")
    NEO4J_AUTH: Optional[str] = Field(default=None, description="Optional Neo4j auth string (user/password)")
    NEO4J_DATABASE: str = Field(default="neo4j", description="Target database name")
    MOCK_NEO4J: bool = Field(default=False, description="Use in-memory mock repository when Neo4j is offline")

    # Ollama Local AI Service
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", description="Ollama API base endpoint")
    OLLAMA_HOST: str = Field(default="http://localhost:11434", description="Ollama host URI")
    OLLAMA_EMBED_MODEL: str = Field(default="nomic-embed-text", description="Vector embedding model name")
    OLLAMA_LLM_MODEL: str = Field(default="qwen2.5:7b", description="LLM model name for stylometric reasoning")
    MOCK_OLLAMA: bool = Field(default=False, description="Use deterministic offline vector mock when Ollama is unavailable")

    # Stylometry & Identity Resolution Thresholds
    SIMILARITY_THRESHOLD: float = Field(
        default=0.82,
        ge=0.0,
        le=1.0,
        description="Cosine similarity cutoff for stylistic linkage between handles",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached singleton instance of application settings."""
    return Settings()


# Default instance for direct import
settings = get_settings()

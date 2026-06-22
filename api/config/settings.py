"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DB_", extra="ignore")

    database_url: str = Field(
        default="postgresql+psycopg://rag_user:rag_password@localhost:5432/rag_platform",
        validation_alias="DATABASE_URL",
    )
    pool_size: int = Field(default=5, validation_alias="DB_POOL_SIZE")


class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AUTH_", extra="ignore")

    required: bool = Field(default=False, validation_alias="AUTH_REQUIRED")
    header_name: str = "X-Tenant-Key"


class RetrievalSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RETRIEVAL_", extra="ignore")

    backend: Literal["memory", "faiss", "chroma", "hybrid", "hnsw", "pgvector"] = Field(
        default="memory",
        validation_alias="RETRIEVAL_BACKEND",
    )
    top_k: int = Field(default=5, validation_alias="RETRIEVAL_TOP_K")
    similarity_threshold: float = Field(
        default=0.0,
        validation_alias="RETRIEVAL_SIMILARITY_THRESHOLD",
    )


class EmbeddingSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EMBEDDING_", extra="ignore")

    provider: str = Field(default="dummy", validation_alias="EMBEDDING_PROVIDER")
    model_name: str = Field(default="all-MiniLM-L6-v2", validation_alias="EMBEDDING_MODEL")
    embedding_dimension: int = Field(default=1536, validation_alias="EMBEDDING_DIMENSION")


class CacheSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CACHE_", extra="ignore")

    redis_url: Optional[str] = Field(default=None, validation_alias="REDIS_URL")
    ttl: int = Field(default=300, validation_alias="CACHE_TTL")


class LLMSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    provider: str = Field(default="local", validation_alias="LLM_PROVIDER")
    openai_api_key: Optional[str] = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        validation_alias="OPENAI_BASE_URL",
    )
    openai_model: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL")


class EvaluationSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EVAL_", extra="ignore")

    enable_evaluation: bool = Field(default=True, validation_alias="ENABLE_EVALUATION")
    faithfulness_threshold: float = Field(
        default=0.7,
        validation_alias="FAITHFULNESS_THRESHOLD",
    )


class ApplicationSettings(BaseSettings):
    """Top-level application configuration."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    retrieval: RetrievalSettings = Field(default_factory=RetrievalSettings)
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    evaluation: EvaluationSettings = Field(default_factory=EvaluationSettings)
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    mlflow_tracking_uri: Optional[str] = Field(default=None, validation_alias="MLFLOW_TRACKING_URI")

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        return value.upper()

    def validate(self) -> None:
        """Validate required configuration for the active deployment profile."""
        if self.llm.provider in {"openai", "openai-compatible"} and not (
            self.llm.openai_api_key or ""
        ).strip():
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")
        if self.llm.provider not in {"local", "openai", "openai-compatible"}:
            raise ValueError(f"Unsupported LLM_PROVIDER: {self.llm.provider}")
        if self.retrieval.backend not in {"memory", "faiss", "chroma", "hybrid", "hnsw", "pgvector"}:
            raise ValueError(f"Unsupported RETRIEVAL_BACKEND: {self.retrieval.backend}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "database": self.database.model_dump(),
            "auth": {"required": self.auth.required, "header_name": self.auth.header_name},
            "retrieval": self.retrieval.model_dump(),
            "embedding": {
                "provider": self.embedding.provider,
                "model_name": self.embedding.model_name,
                "embedding_dimension": self.embedding.embedding_dimension,
            },
            "cache": self.cache.model_dump(),
            "llm": {"provider": self.llm.provider, "openai_model": self.llm.openai_model},
            "evaluation": self.evaluation.model_dump(),
            "log_level": self.log_level,
        }


@lru_cache(maxsize=1)
def get_settings() -> ApplicationSettings:
    settings = ApplicationSettings()
    settings.validate()
    return settings


def get_default_settings() -> ApplicationSettings:
    """Backward-compatible alias used by existing routes."""
    return get_settings()

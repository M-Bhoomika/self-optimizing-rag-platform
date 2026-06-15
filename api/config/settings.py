"""Application configuration models.

Defines typed, nested Pydantic settings for the platform along with helpers to
build a default configuration and export it as a dictionary.

NOTE: Environment-variable / .env loading is intentionally NOT wired in here.
When ready, this is the place to add it — for example by switching the models
to ``pydantic_settings.BaseSettings`` (so each field reads from an env var like
``DATABASE_URL``), or by reading ``os.environ`` inside ``get_default_settings``.
The field names below are chosen to map cleanly onto such environment variables.
"""

from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, Field


class DatabaseSettings(BaseModel):
    """Database connection configuration."""

    # TODO(env): load from DATABASE_URL
    database_url: str = "postgresql://rag_user:rag_password@localhost:5432/rag_platform"
    # TODO(env): load from DB_POOL_SIZE
    pool_size: int = 5


class RetrievalSettings(BaseModel):
    """Retrieval behavior configuration."""

    # TODO(env): load from RETRIEVAL_TOP_K
    top_k: int = 5
    # TODO(env): load from RETRIEVAL_SIMILARITY_THRESHOLD
    similarity_threshold: float = 0.0


class EmbeddingSettings(BaseModel):
    """Embedding provider configuration."""

    # TODO(env): load from EMBEDDING_MODEL_NAME
    model_name: str = "dummy"
    # TODO(env): load from EMBEDDING_DIMENSION
    embedding_dimension: int = 1536


class EvaluationSettings(BaseModel):
    """Evaluation configuration."""

    # TODO(env): load from ENABLE_EVALUATION
    enable_evaluation: bool = True
    # TODO(env): load from FAITHFULNESS_THRESHOLD
    faithfulness_threshold: float = 0.7


class ApplicationSettings(BaseModel):
    """Top-level application configuration aggregating all sections."""

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    retrieval: RetrievalSettings = Field(default_factory=RetrievalSettings)
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    evaluation: EvaluationSettings = Field(default_factory=EvaluationSettings)

    def to_dict(self) -> Dict[str, Any]:
        """Export the full configuration as a plain nested dictionary."""
        return self.model_dump()


def get_default_settings() -> ApplicationSettings:
    """Return a fully populated :class:`ApplicationSettings` with defaults.

    TODO(env): Once environment loading is added, override the section defaults
    here based on the process environment before returning.
    """
    return ApplicationSettings()

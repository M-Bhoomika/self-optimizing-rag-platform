"""Embedding-domain Pydantic models.

Request/response contracts for the embedding layer. Transport-agnostic and
free of any provider-specific logic.
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class EmbeddingRequest(BaseModel):
    """Input for an embedding call."""

    texts: List[str]


class EmbeddingResponse(BaseModel):
    """Embedding vectors produced for a batch of texts."""

    vectors: List[List[float]] = Field(default_factory=list)
    dimension: int

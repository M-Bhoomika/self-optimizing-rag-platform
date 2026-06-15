"""Retrieval-domain Pydantic models.

Request/response contracts for the retrieval layer. These are transport- and
storage-agnostic and carry no business logic.
"""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class RetrievalRequest(BaseModel):
    """Input for a retrieval call."""

    tenant_id: str
    query: str
    top_k: int = 5


class RetrievalResult(BaseModel):
    """A single retrieved chunk with its similarity score."""

    chunk_id: str
    document_id: str
    score: float
    chunk_text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RetrievalResponse(BaseModel):
    """The ordered set of results for a retrieval request."""

    results: List[RetrievalResult] = Field(default_factory=list)

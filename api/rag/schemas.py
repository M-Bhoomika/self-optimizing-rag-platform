"""RAG-domain Pydantic models.

Request/response contracts for the orchestration layer that combines retrieval
with (eventual) answer generation.
"""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class RAGRequest(BaseModel):
    """Input for a RAG orchestration call."""

    tenant_id: str
    query: str
    top_k: int = 5


class RAGContext(BaseModel):
    """A single retrieved context passed to the generation layer."""

    chunk_id: str
    document_id: str
    chunk_text: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RAGResponse(BaseModel):
    """The orchestrated result: retrieved contexts plus a generated answer."""

    query: str
    contexts: List[RAGContext] = Field(default_factory=list)
    generated_answer: str
    retrieved_count: int

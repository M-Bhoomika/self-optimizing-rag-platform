"""RAG-domain Pydantic models."""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class RAGRequest(BaseModel):
    tenant_id: str
    query: str
    top_k: int = 5


class RAGContext(BaseModel):
    chunk_id: str
    document_id: str
    chunk_text: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RAGResponse(BaseModel):
    query: str
    contexts: List[RAGContext] = Field(default_factory=list)
    generated_answer: str
    retrieved_count: int
    confidence_score: float = 0.0
    low_confidence: bool = False
    model: str = ""
    citations: List[Dict[str, Any]] = Field(default_factory=list)

"""State definitions for the iterative retrieval pipeline."""

from __future__ import annotations

from typing import Any, Dict, List, TypedDict


class RAGState(TypedDict, total=False):
    """Graph state passed between iterative retrieval nodes."""

    tenant_id: str
    query: str
    rewritten_queries: List[str]
    retrieved_chunks: List[Dict[str, Any]]
    reranked_chunks: List[Dict[str, Any]]
    relevance_score: float
    confidence_score: float
    answer: str
    citations: List[Dict[str, Any]]
    iteration_count: int
    top_k: int
    max_iterations: int
    relevance_threshold: float
    low_confidence: bool
    model: str

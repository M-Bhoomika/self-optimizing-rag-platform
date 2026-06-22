"""RAG orchestration service."""

from __future__ import annotations

from typing import List

from api.generation.factory import get_llm_provider
from api.generation.service import GenerationService
from api.retrieval.pipeline import IterativeRetrievalPipeline

from .schemas import RAGContext, RAGRequest, RAGResponse


class RAGService:
    """Orchestrates end-to-end iterative retrieval and answer generation."""

    def __init__(
        self,
        retrieval_service: object,
        relevance_threshold: float = 0.35,
        max_iterations: int = 3,
    ) -> None:
        self.pipeline = IterativeRetrievalPipeline(
            retrieval_service=retrieval_service,
            generation_service=GenerationService(llm_provider=get_llm_provider()),
            relevance_threshold=relevance_threshold,
            max_iterations=max_iterations,
        )

    def retrieve_context(self, request: RAGRequest) -> RAGResponse:
        state = self.pipeline.run(
            tenant_id=request.tenant_id,
            query=request.query,
            top_k=request.top_k,
        )
        chunks = state.get("reranked_chunks") or state.get("retrieved_chunks", [])
        contexts: List[RAGContext] = [
            RAGContext(
                chunk_id=str(c.get("chunk_id", "")),
                document_id=str(c.get("document_id", "")),
                chunk_text=str(c.get("chunk_text", "")),
                score=float(c.get("score", 0.0)),
                metadata=dict(c.get("metadata", {})),
            )
            for c in chunks
        ]
        return RAGResponse(
            query=request.query,
            contexts=contexts,
            generated_answer=str(state.get("answer", "")),
            retrieved_count=len(contexts),
            confidence_score=float(state.get("confidence_score", 0.0)),
            low_confidence=bool(state.get("low_confidence", False)),
            model=str(state.get("model", "")),
            citations=list(state.get("citations", [])),
        )

    @staticmethod
    def build_context_string(contexts: List[RAGContext]) -> str:
        lines: List[str] = []
        for rank, context in enumerate(contexts, start=1):
            lines.append(f"[{rank}] {context.chunk_text}")
        return "\n\n".join(lines)

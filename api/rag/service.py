"""RAG orchestration service.

Coordinates retrieval and (eventually) answer generation. For now the
generation step is a placeholder; only retrieval and context assembly are
implemented.
"""

from __future__ import annotations

from typing import List

from api.retrieval.schemas import RetrievalRequest

from .schemas import RAGContext, RAGRequest, RAGResponse

GENERATION_PLACEHOLDER = "Generation layer not implemented yet."


class RAGService:
    """Orchestrates retrieval and answer generation for a query."""

    def __init__(self, retrieval_service: object) -> None:
        self.retrieval_service = retrieval_service

    def retrieve_context(self, request: RAGRequest) -> RAGResponse:
        """Retrieve relevant chunks and assemble a RAG response.

        The generated answer is a fixed placeholder until the generation layer
        is implemented.
        """
        retrieval_request = RetrievalRequest(
            tenant_id=request.tenant_id,
            query=request.query,
            top_k=request.top_k,
        )
        retrieval_response = self.retrieval_service.retrieve(retrieval_request)

        contexts: List[RAGContext] = [
            RAGContext(
                chunk_id=result.chunk_id,
                document_id=result.document_id,
                chunk_text=result.chunk_text,
                score=result.score,
                metadata=result.metadata,
            )
            for result in retrieval_response.results
        ]

        return RAGResponse(
            query=request.query,
            contexts=contexts,
            generated_answer=GENERATION_PLACEHOLDER,
            retrieved_count=len(contexts),
        )

    @staticmethod
    def build_context_string(contexts: List[RAGContext]) -> str:
        """Concatenate context chunk texts into a readable, ranked text block."""
        lines: List[str] = []
        for rank, context in enumerate(contexts, start=1):
            lines.append(f"[{rank}] {context.chunk_text}")
        return "\n\n".join(lines)

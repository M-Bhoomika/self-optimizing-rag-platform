"""Iterative retrieval pipeline with LangGraph or lightweight fallback runner."""

from __future__ import annotations

import hashlib
from typing import Any, Callable, Dict, List, Optional

from api.generation.factory import get_llm_provider
from api.generation.service import GenerationService, compute_confidence_score
from api.observability.tracing import trace_span
from api.retrieval.schemas import RetrievalRequest
from api.retrieval.service import RetrievalService
from api.retrieval.state import RAGState


def _rewrite_query(query: str, iteration: int) -> str:
    """Expand query with iteration-specific terms for improved recall."""
    base = query.strip()
    if iteration <= 1:
        return base
    suffix = hashlib.sha256(f"{base}:{iteration}".encode()).hexdigest()[:6]
    return f"{base} ({suffix})"


class IterativeRetrievalPipeline:
    """End-to-end RAG pipeline: rewrite → retrieve → assess → rerank → generate."""

    def __init__(
        self,
        retrieval_service: Optional[RetrievalService] = None,
        generation_service: Optional[GenerationService] = None,
        relevance_threshold: float = 0.35,
        max_iterations: int = 3,
    ) -> None:
        self.retrieval_service = retrieval_service or RetrievalService()
        self.generation_service = generation_service or GenerationService(
            llm_provider=get_llm_provider(),
            confidence_threshold=relevance_threshold,
        )
        self.relevance_threshold = relevance_threshold
        self.max_iterations = max_iterations
        self._graph_runner = self._build_runner()

    def _build_runner(self) -> Callable[[RAGState], RAGState]:
        try:
            from langgraph.graph import END, StateGraph  # type: ignore

            graph = StateGraph(RAGState)
            graph.add_node("rewrite_query", self.rewrite_query)
            graph.add_node("retrieve", self.retrieve)
            graph.add_node("assess_relevance", self.assess_relevance)
            graph.add_node("rerank", self.rerank)
            graph.add_node("generate", self.generate)

            graph.set_entry_point("rewrite_query")
            graph.add_edge("rewrite_query", "retrieve")
            graph.add_edge("retrieve", "assess_relevance")
            graph.add_conditional_edges(
                "assess_relevance",
                self.route_after_assessment,
                {
                    "rewrite": "rewrite_query",
                    "rerank": "rerank",
                    "generate_low_confidence": "generate",
                },
            )
            graph.add_edge("rerank", "generate")
            graph.add_edge("generate", END)
            return graph.compile().invoke
        except ImportError:
            return self._fallback_run

    def rewrite_query(self, state: RAGState) -> RAGState:
        iteration = int(state.get("iteration_count", 0)) + 1
        rewritten = _rewrite_query(state["query"], iteration)
        history = list(state.get("rewritten_queries", []))
        history.append(rewritten)
        updated = dict(state)
        updated["rewritten_queries"] = history
        updated["iteration_count"] = iteration
        return updated  # type: ignore[return-value]

    def retrieve(self, state: RAGState) -> RAGState:
        query = state["rewritten_queries"][-1]
        with trace_span(
            "retrieval.search",
            {"tenant_id": state["tenant_id"], "top_k": int(state.get("top_k", 5))},
        ):
            response = self.retrieval_service.retrieve(
                RetrievalRequest(
                    tenant_id=state["tenant_id"],
                    query=query,
                    top_k=int(state.get("top_k", 5)),
                )
            )
        chunks = [
            {
                "chunk_id": item.chunk_id,
                "document_id": item.document_id,
                "chunk_text": item.chunk_text,
                "score": item.score,
                "metadata": item.metadata,
            }
            for item in response.results
        ]
        updated = dict(state)
        updated["retrieved_chunks"] = chunks
        return updated  # type: ignore[return-value]

    def assess_relevance(self, state: RAGState) -> RAGState:
        chunks = state.get("retrieved_chunks", [])
        score = max((float(c.get("score", 0.0)) for c in chunks), default=0.0)
        updated = dict(state)
        updated["relevance_score"] = score
        return updated  # type: ignore[return-value]

    def rerank(self, state: RAGState) -> RAGState:
        chunks = list(state.get("retrieved_chunks", []))
        chunks.sort(key=lambda item: float(item.get("score", 0.0)), reverse=True)
        updated = dict(state)
        updated["reranked_chunks"] = chunks
        return updated  # type: ignore[return-value]

    def generate(self, state: RAGState) -> RAGState:
        chunks = state.get("reranked_chunks") or state.get("retrieved_chunks", [])
        context = "\n\n".join(c["chunk_text"] for c in chunks)
        relevance = float(state.get("relevance_score", 0.0))
        threshold = float(state.get("relevance_threshold", self.relevance_threshold))
        force_low = bool(state.get("low_confidence", False)) or relevance < threshold

        with trace_span(
            "generation.answer",
            {"tenant_id": state["tenant_id"], "low_confidence": force_low},
        ):
            result = self.generation_service.generate_answer(
                question=state["query"],
                context=context if context.strip() else "No retrieval context available.",
                chunks=chunks,
                retrieval_score=relevance,
                force_low_confidence=force_low and not context.strip(),
            )

        if force_low and context.strip() and not result.low_confidence:
            result_confidence = compute_confidence_score(result.answer, context, relevance)
            if result_confidence < threshold:
                result = result.model_copy(
                    update={
                        "answer": f"Low-confidence answer: {result.answer}",
                        "confidence_score": result_confidence,
                        "low_confidence": True,
                    }
                )

        citations = [
            {
                "chunk_id": c.chunk_id,
                "document_id": c.document_id,
                "chunk_text": c.chunk_text,
                "score": c.score,
            }
            for c in result.citations
        ]
        updated = dict(state)
        updated["answer"] = result.answer
        updated["citations"] = citations
        updated["confidence_score"] = result.confidence_score
        updated["low_confidence"] = result.low_confidence
        updated["model"] = result.model
        return updated  # type: ignore[return-value]

    def route_after_assessment(self, state: RAGState) -> str:
        score = float(state.get("relevance_score", 0.0))
        iteration = int(state.get("iteration_count", 0))
        max_iterations = int(state.get("max_iterations", self.max_iterations))
        threshold = float(state.get("relevance_threshold", self.relevance_threshold))

        if score >= threshold:
            return "rerank"
        if iteration >= max_iterations:
            return "generate_low_confidence"
        return "rewrite"

    def _fallback_run(self, state: RAGState) -> RAGState:
        current = dict(state)
        current.setdefault("rewritten_queries", [])
        current.setdefault("iteration_count", 0)
        current.setdefault("max_iterations", self.max_iterations)
        current.setdefault("relevance_threshold", self.relevance_threshold)
        current.setdefault("low_confidence", False)

        while True:
            current = self.rewrite_query(current)  # type: ignore[assignment]
            current = self.retrieve(current)  # type: ignore[assignment]
            current = self.assess_relevance(current)  # type: ignore[assignment]
            route = self.route_after_assessment(current)
            if route == "rewrite":
                continue
            if route == "rerank":
                current = self.rerank(current)  # type: ignore[assignment]
            else:
                current["low_confidence"] = True  # type: ignore[index]
            current = self.generate(current)  # type: ignore[assignment]
            return current  # type: ignore[return-value]

    def run_until_generation(self, tenant_id: str, query: str, top_k: int = 5) -> RAGState:
        """Run rewrite/retrieve/assess/rerank without final generation."""
        state: RAGState = {
            "tenant_id": tenant_id,
            "query": query,
            "rewritten_queries": [],
            "retrieved_chunks": [],
            "reranked_chunks": [],
            "relevance_score": 0.0,
            "confidence_score": 0.0,
            "answer": "",
            "citations": [],
            "iteration_count": 0,
            "top_k": top_k,
            "max_iterations": self.max_iterations,
            "relevance_threshold": self.relevance_threshold,
            "low_confidence": False,
            "model": "",
        }
        current = dict(state)
        current.setdefault("rewritten_queries", [])
        current.setdefault("iteration_count", 0)
        while True:
            current = self.rewrite_query(current)  # type: ignore[assignment]
            current = self.retrieve(current)  # type: ignore[assignment]
            current = self.assess_relevance(current)  # type: ignore[assignment]
            route = self.route_after_assessment(current)
            if route == "rewrite":
                continue
            if route == "rerank":
                current = self.rerank(current)  # type: ignore[assignment]
            else:
                current["low_confidence"] = True  # type: ignore[index]
            return current  # type: ignore[return-value]

    def finalize_generation(self, state: RAGState) -> RAGState:
        return self.generate(state)

    def run(self, tenant_id: str, query: str, top_k: int = 5) -> RAGState:
        return self.finalize_generation(
            self.run_until_generation(tenant_id=tenant_id, query=query, top_k=top_k)
        )

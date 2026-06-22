"""LangChain retrieval fallback tests."""

from __future__ import annotations

from api.retrieval.langchain_retrievers import (
    ContextualCompressionRetrieverFallback,
    EnsembleRetrieverFallback,
    LangChainRetrievalOrchestrator,
    MultiQueryRetrieverFallback,
)
from api.retrieval.schemas import RetrievalResult


def _result(chunk_id: str, score: float) -> RetrievalResult:
    return RetrievalResult(
        chunk_id=chunk_id,
        document_id="doc-1",
        score=score,
        chunk_text=f"text about retrieval {chunk_id}",
        metadata={},
    )


def test_multi_query_expands_and_dedupes() -> None:
    retriever = MultiQueryRetrieverFallback()

    def _search(query: str, top_k: int):
        return [_result(f"{query}-a", 0.9), _result("shared", 0.8)]

    results = retriever.retrieve("vector search", _search, top_k=3, variant_count=2)
    assert results
    assert len({item.chunk_id for item in results}) == len(results)


def test_compression_prefers_overlap() -> None:
    retriever = ContextualCompressionRetrieverFallback()
    results = retriever.compress(
        "vector search",
        [_result("a", 0.5), _result("b", 0.9)],
        top_k=1,
    )
    assert len(results) == 1


def test_ensemble_merges_retrievers() -> None:
    retriever = EnsembleRetrieverFallback()

    def _first(_query: str, _top_k: int):
        return [_result("a", 1.0)]

    def _second(_query: str, _top_k: int):
        return [_result("b", 1.0)]

    merged = retriever.retrieve("q", [_first, _second], top_k=2)
    assert len(merged) == 2


def test_orchestrator_import_safe_without_langchain() -> None:
    orchestrator = LangChainRetrievalOrchestrator(use_langchain=False)
    assert orchestrator.backend == "fallback"
    results = orchestrator.retrieve(
        "tenant isolation",
        retrieve_fn=lambda q, k: [_result("c1", 0.7)],
        top_k=1,
    )
    assert results

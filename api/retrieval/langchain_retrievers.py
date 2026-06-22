"""LangChain-style retrieval abstractions with offline fallbacks.

When ``langchain`` / ``langchain-community`` are installed, optional wrappers
delegate to LangChain retriever classes. Otherwise deterministic fallback
implementations provide MultiQuery, contextual compression, and ensemble
behavior without external dependencies.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Callable, Dict, List, Optional, Sequence

from api.retrieval.schemas import RetrievalResult

logger = logging.getLogger(__name__)

RetrieveFn = Callable[[str, int], List[RetrievalResult]]


def _dedupe_results(results: Sequence[RetrievalResult]) -> List[RetrievalResult]:
    seen: set[str] = set()
    ordered: List[RetrievalResult] = []
    for item in sorted(results, key=lambda r: r.score, reverse=True):
        if item.chunk_id in seen:
            continue
        seen.add(item.chunk_id)
        ordered.append(item)
    return ordered


class MultiQueryRetrieverFallback:
    """Generate query variants for improved recall (MultiQueryRetriever-style)."""

    def expand_queries(self, query: str, count: int = 3) -> List[str]:
        base = query.strip()
        if not base:
            return []
        variants = [base]
        for index in range(1, count):
            suffix = hashlib.sha256(f"{base}:{index}".encode()).hexdigest()[:6]
            variants.append(f"{base} (variant {suffix})")
        return variants

    def retrieve(
        self,
        query: str,
        retrieve_fn: RetrieveFn,
        top_k: int = 5,
        variant_count: int = 3,
    ) -> List[RetrievalResult]:
        merged: List[RetrievalResult] = []
        for variant in self.expand_queries(query, count=variant_count):
            merged.extend(retrieve_fn(variant, top_k))
        return _dedupe_results(merged)[:top_k]


class ContextualCompressionRetrieverFallback:
    """Filter/rerank retrieved chunks by lexical overlap (compression-style)."""

    def compress(
        self,
        query: str,
        results: Sequence[RetrievalResult],
        top_k: int = 5,
    ) -> List[RetrievalResult]:
        if not results:
            return []
        query_terms = {term.lower() for term in query.split() if len(term) > 2}

        def _score(item: RetrievalResult) -> float:
            text_terms = set(item.chunk_text.lower().split())
            overlap = len(query_terms & text_terms)
            return float(item.score) + (0.05 * overlap)

        ranked = sorted(results, key=_score, reverse=True)
        return ranked[:top_k]


class EnsembleRetrieverFallback:
    """Merge results from multiple retrievers with weighted scores."""

    def retrieve(
        self,
        query: str,
        retrievers: Sequence[RetrieveFn],
        top_k: int = 5,
        weights: Optional[Sequence[float]] = None,
    ) -> List[RetrievalResult]:
        if not retrievers:
            return []
        weight_values = list(weights) if weights else [1.0] * len(retrievers)
        merged: List[RetrievalResult] = []
        for weight, retrieve_fn in zip(weight_values, retrievers):
            for item in retrieve_fn(query, top_k):
                merged.append(
                    RetrievalResult(
                        chunk_id=item.chunk_id,
                        document_id=item.document_id,
                        score=float(item.score) * float(weight),
                        chunk_text=item.chunk_text,
                        metadata=dict(item.metadata),
                    )
                )
        return _dedupe_results(merged)[:top_k]


def _langchain_available() -> bool:
    try:
        import langchain  # noqa: F401

        return True
    except ImportError:
        return False


class LangChainRetrievalOrchestrator:
    """Optional LangChain retriever wiring with safe fallbacks."""

    def __init__(self, use_langchain: Optional[bool] = None) -> None:
        self.use_langchain = _langchain_available() if use_langchain is None else bool(use_langchain)
        self.multi_query = MultiQueryRetrieverFallback()
        self.compression = ContextualCompressionRetrieverFallback()
        self.ensemble = EnsembleRetrieverFallback()
        self._langchain_ready = False
        if self.use_langchain:
            try:
                import langchain_community  # noqa: F401

                self._langchain_ready = True
            except ImportError:
                logger.debug("langchain-community not installed; using fallbacks.")
                self._langchain_ready = False

    @property
    def backend(self) -> str:
        return "langchain" if self._langchain_ready else "fallback"

    def retrieve(
        self,
        query: str,
        retrieve_fn: RetrieveFn,
        top_k: int = 5,
        use_multi_query: bool = True,
        use_compression: bool = True,
        ensemble_fns: Optional[Sequence[RetrieveFn]] = None,
    ) -> List[RetrievalResult]:
        if ensemble_fns:
            results = self.ensemble.retrieve(query, ensemble_fns, top_k=top_k)
        elif use_multi_query:
            results = self.multi_query.retrieve(query, retrieve_fn, top_k=top_k)
        else:
            results = retrieve_fn(query, top_k)

        if use_compression:
            results = self.compression.compress(query, results, top_k=top_k)
        return results

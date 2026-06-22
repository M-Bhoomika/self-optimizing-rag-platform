"""Cross-encoder reranker for refining retrieval results.

Re-scores candidate chunks with a cross-encoder model that jointly encodes the
query and each chunk, producing more accurate relevance ordering than bi-encoder
similarity alone.
"""

from __future__ import annotations

from typing import Any, List

from .schemas import RetrievalResult

DEFAULT_RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class CrossEncoderReranker:
    """Rerank retrieval candidates using a sentence-transformers CrossEncoder."""

    def __init__(self, model_name: str = DEFAULT_RERANKER_MODEL) -> None:
        try:
            from sentence_transformers import CrossEncoder  # type: ignore
        except ImportError as exc:  # pragma: no cover - exercised via ImportError tests
            raise ImportError(
                "sentence-transformers is required for CrossEncoderReranker. "
                "Install it with: pip install sentence-transformers"
            ) from exc

        self.model_name = model_name
        self._model: Any = CrossEncoder(model_name)

    def rerank(
        self,
        query: str,
        results: List[RetrievalResult],
        top_k: int,
    ) -> List[RetrievalResult]:
        """Return results sorted by cross-encoder score, limited to ``top_k``."""
        if not results:
            return []

        pairs = [(query, result.chunk_text) for result in results]
        scores = self._model.predict(pairs)

        reranked: List[RetrievalResult] = []
        for result, score in zip(results, scores):
            metadata = dict(result.metadata)
            metadata["reranker_score"] = float(score)
            reranked.append(result.model_copy(update={"metadata": metadata, "score": float(score)}))

        reranked.sort(key=lambda item: item.score, reverse=True)
        if top_k >= 0:
            return reranked[:top_k]
        return reranked

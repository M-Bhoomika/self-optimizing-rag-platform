"""Tests for retrieval reranking."""

from __future__ import annotations

import pytest

from api.retrieval.reranker import CrossEncoderReranker
from api.retrieval.schemas import RetrievalResult


class FakeReranker:
    """Deterministic reranker used in service tests."""

    def rerank(
        self,
        query: str,
        results: list[RetrievalResult],
        top_k: int,
    ) -> list[RetrievalResult]:
        if not results:
            return []
        reranked = sorted(results, key=lambda item: item.chunk_id, reverse=True)
        output: list[RetrievalResult] = []
        for index, result in enumerate(reranked[:top_k]):
            metadata = dict(result.metadata)
            metadata["reranker_score"] = float(index + 1)
            output.append(
                result.model_copy(
                    update={"score": float(index + 1), "metadata": metadata}
                )
            )
        return output


def _sample_results() -> list[RetrievalResult]:
    return [
        RetrievalResult(
            chunk_id="c1",
            document_id="d1",
            score=0.2,
            chunk_text="alpha",
            metadata={},
        ),
        RetrievalResult(
            chunk_id="c2",
            document_id="d1",
            score=0.9,
            chunk_text="beta",
            metadata={},
        ),
    ]


def test_fake_reranker_sorts_results() -> None:
    reranker = FakeReranker()
    results = reranker.rerank("query", _sample_results(), top_k=2)

    assert [result.chunk_id for result in results] == ["c2", "c1"]
    assert results[0].metadata["reranker_score"] == 1.0
    assert results[1].metadata["reranker_score"] == 2.0


def test_reranker_returns_empty_for_no_results() -> None:
    reranker = FakeReranker()
    assert reranker.rerank("query", [], top_k=5) == []


def test_cross_encoder_import_error_when_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins

    original_import = builtins.__import__

    def _fake_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "sentence_transformers":
            raise ImportError("sentence-transformers missing")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fake_import)

    with pytest.raises(ImportError, match="sentence-transformers"):
        CrossEncoderReranker()

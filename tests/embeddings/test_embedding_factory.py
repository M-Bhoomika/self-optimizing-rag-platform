"""Embedding provider factory tests."""

from __future__ import annotations

import pytest

from api.embeddings.factory import get_embedding_provider
from api.embeddings.providers import DummyEmbeddingProvider


def test_default_dummy_provider() -> None:
    provider = get_embedding_provider(provider_name="dummy")
    assert isinstance(provider, DummyEmbeddingProvider)
    assert provider.dimension == 1536


def test_dummy_batch_embeddings() -> None:
    provider = get_embedding_provider(provider_name="dummy")
    vectors = provider.embed_documents(["a", "b"])
    assert len(vectors) == 2
    assert len(vectors[0]) == provider.dimension


def test_sentence_transformers_import_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import api.embeddings.providers as providers_module

    def _raise(*args, **kwargs):
        raise ImportError("missing")

    monkeypatch.setattr(providers_module, "SentenceTransformer", None, raising=False)
    with pytest.raises(ImportError):
        providers_module.SentenceTransformersProvider()

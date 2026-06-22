"""End-to-end query flow tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.app.main import create_app
from api.embeddings.providers import DummyEmbeddingProvider
from api.retrieval.service import RetrievalService
from api.retrieval.vector_store import InMemoryVectorStore


def _seed_index() -> None:
    service = RetrievalService(
        embedding_provider=DummyEmbeddingProvider(),
        vector_store=InMemoryVectorStore(),
    )
    service.index_chunks(
        [
            {
                "chunk_id": "c1",
                "document_id": "d1",
                "tenant_id": "e2e-tenant",
                "chunk_text": "Vector databases store embeddings for similarity search.",
                "metadata": {},
            }
        ]
    )


def test_e2e_generate_with_indexed_context() -> None:
    client = TestClient(create_app())
    files = {"file": ("doc.txt", "Vector databases store embeddings for similarity search.", "text/plain")}
    data = {"tenant_id": "e2e-tenant", "title": "Vector DB", "document_type": "txt", "source": "test"}
    upload = client.post("/api/v1/documents/upload", data=data, files=files)
    assert upload.status_code == 200

    response = client.post(
        "/api/v1/query/generate",
        json={"tenant_id": "e2e-tenant", "query": "vector databases", "use_cache": False},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["answer"]
    assert "citations" in body


def test_readiness_endpoint() -> None:
    client = TestClient(create_app())
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert "checks" in response.json()


def test_experiments_run_endpoint() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/experiments/run",
        json={"experiment_name": "api-test", "tenant_id": "eval-tenant"},
    )
    assert response.status_code == 200
    assert "metrics" in response.json()

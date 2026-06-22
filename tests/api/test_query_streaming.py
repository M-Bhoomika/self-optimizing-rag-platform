"""Tests for streaming query API and cache behavior."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.app.main import create_app
from api.cache.redis_cache import RedisCache


def test_cache_key_format() -> None:
    key = RedisCache.make_key("tenant-a", "hello")
    assert key == f"tenant-a:{key.split(':')[1]}"
    assert not key.startswith("rag:query:")


def test_cache_memory_fallback() -> None:
    cache = RedisCache(redis_url=None)
    cache.set("tenant-a", "hello", {"answer": "world"})
    assert cache.get("tenant-a", "hello") == {"answer": "world"}


def test_stream_query_endpoint_sse() -> None:
    client = TestClient(create_app())
    with client.stream(
        "POST",
        "/api/v1/query/stream",
        json={"tenant_id": "tenant-1", "query": "vector search", "top_k": 3, "use_cache": False},
    ) as response:
        assert response.status_code == 200
        body = "".join(response.iter_text())
        assert "data:" in body
        assert '"done": true' in body.lower() or '"done": True' in body


def test_generate_endpoint_structured() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/query/generate",
        json={"tenant_id": "tenant-1", "query": "What is RAG?", "top_k": 3, "use_cache": False},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "answer" in payload
    assert "citations" in payload
    assert "confidence_score" in payload


def test_cache_stats_endpoint() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/query/cache/stats")
    assert response.status_code == 200
    assert "hits" in response.json()


def test_rag_query_no_placeholder() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/rag/query",
        json={"tenant_id": "tenant-1", "query": "hello", "top_k": 3},
    )
    assert response.status_code == 200
    body = response.json()
    assert "Generation layer not implemented yet." not in body["generated_answer"]

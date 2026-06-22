"""API health and route tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.app.main import create_app


def test_health_endpoint() -> None:
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_rag_query_endpoint_still_works() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/rag/query",
        json={"tenant_id": "tenant-1", "query": "hello", "top_k": 3},
    )
    assert response.status_code == 200
    body = response.json()
    assert "generated_answer" in body
    assert "confidence_score" in body

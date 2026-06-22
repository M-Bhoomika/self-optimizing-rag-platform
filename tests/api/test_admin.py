"""Admin API route tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.app.main import create_app


def test_admin_status_endpoint() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/admin/status")
    assert response.status_code == 200
    body = response.json()
    assert "retrieval_backend" in body
    assert "worker_queue_backend" in body


def test_admin_config_endpoint() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/admin/config")
    assert response.status_code == 200
    assert "retrieval" in response.json()


def test_admin_tenants_endpoint() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/admin/tenants")
    assert response.status_code == 200
    assert "tenants" in response.json()

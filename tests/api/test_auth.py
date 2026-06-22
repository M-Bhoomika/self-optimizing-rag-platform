"""Authentication and tenant isolation tests."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from api.app.auth import clear_test_tenants, hash_api_key, register_test_tenant, verify_api_key
from api.app.main import create_app


def test_hash_and_verify_api_key() -> None:
    raw = "test-secret-key"
    hashed = hash_api_key(raw)
    assert verify_api_key(raw, hashed)
    assert not verify_api_key("wrong", hashed)


def test_register_test_tenant_resolves() -> None:
    clear_test_tenants()
    tenant = register_test_tenant("secret", tenant_id="tenant-auth-1")
    assert tenant.id == "tenant-auth-1"


def test_auth_required_rejects_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    from api.app import dependencies
    from api.config import settings as settings_module

    dependencies.get_settings_cached.cache_clear()
    settings_module.get_settings.cache_clear()
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/query/generate",
        json={"tenant_id": "tenant-auth-1", "query": "hello", "use_cache": False},
    )
    assert response.status_code == 401


def test_auth_required_accepts_valid_key(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_test_tenants()
    register_test_tenant("valid-key", tenant_id="tenant-auth-1")
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    from api.app import dependencies
    from api.config import settings as settings_module

    dependencies.get_settings_cached.cache_clear()
    settings_module.get_settings.cache_clear()
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/query/generate",
        headers={"X-Tenant-Key": "valid-key"},
        json={"tenant_id": "tenant-auth-1", "query": "hello", "use_cache": False},
    )
    assert response.status_code == 200


def test_tenant_isolation_rejects_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_test_tenants()
    register_test_tenant("valid-key", tenant_id="tenant-a")
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    from api.app import dependencies
    from api.config import settings as settings_module

    dependencies.get_settings_cached.cache_clear()
    settings_module.get_settings.cache_clear()
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/query/generate",
        headers={"X-Tenant-Key": "valid-key"},
        json={"tenant_id": "tenant-b", "query": "hello", "use_cache": False},
    )
    assert response.status_code == 403


def test_quota_enforcement_blocks_excess_usage(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_test_tenants()
    register_test_tenant("quota-key", tenant_id="quota-tenant", query_quota_per_day=1)
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    from api.app import dependencies
    from api.config import settings as settings_module

    dependencies.get_settings_cached.cache_clear()
    settings_module.get_settings.cache_clear()
    client = TestClient(create_app())
    headers = {"X-Tenant-Key": "quota-key"}
    body = {"tenant_id": "quota-tenant", "query": "hello", "use_cache": False}
    first = client.post("/api/v1/query/generate", headers=headers, json=body)
    assert first.status_code == 200
    second = client.post("/api/v1/query/generate", headers=headers, json=body)
    assert second.status_code == 429


def test_document_quota_blocks_upload(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_test_tenants()
    register_test_tenant("doc-quota-key", tenant_id="doc-quota-tenant", document_quota=1)
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    from api.app import dependencies
    from api.config import settings as settings_module

    dependencies.get_settings_cached.cache_clear()
    settings_module.get_settings.cache_clear()
    client = TestClient(create_app())
    headers = {"X-Tenant-Key": "doc-quota-key"}
    files = {"file": ("doc.txt", "hello world", "text/plain")}
    data = {
        "tenant_id": "doc-quota-tenant",
        "title": "Doc 1",
        "document_type": "txt",
        "source": "upload",
    }
    first = client.post("/api/v1/documents/upload", headers=headers, data=data, files=files)
    assert first.status_code == 200
    second = client.post("/api/v1/documents/upload", headers=headers, data=data, files=files)
    assert second.status_code == 429

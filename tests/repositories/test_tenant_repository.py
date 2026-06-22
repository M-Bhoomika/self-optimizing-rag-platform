"""TenantRepository CRUD tests."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from api.models.tenant import Tenant
from api.repositories.tenants import TenantRepository


@pytest.fixture
def session() -> MagicMock:
    return MagicMock()


@pytest.fixture
def repo(session: MagicMock) -> TenantRepository:
    return TenantRepository(session)


def test_create_tenant(repo: TenantRepository, session: MagicMock) -> None:
    tenant = repo.create_tenant("Acme", "hash-1")
    session.add.assert_called_once()
    session.flush.assert_called_once()
    assert tenant.name == "Acme"
    assert tenant.api_key_hash == "hash-1"


def test_update_tenant_updates_fields(repo: TenantRepository, session: MagicMock) -> None:
    tenant_id = str(uuid.uuid4())
    tenant = Tenant(id=tenant_id, name="Old", api_key_hash="hash")
    session.get.return_value = tenant

    updated = repo.update_tenant(
        tenant_id,
        name="New",
        document_quota=50,
        query_quota_per_day=200,
    )

    assert updated is tenant
    assert tenant.name == "New"
    assert tenant.document_quota == 50
    assert tenant.query_quota_per_day == 200
    session.flush.assert_called_once()


def test_update_tenant_returns_none_when_missing(repo: TenantRepository, session: MagicMock) -> None:
    session.get.return_value = None
    assert repo.update_tenant(str(uuid.uuid4()), name="New") is None


def test_delete_tenant(repo: TenantRepository, session: MagicMock) -> None:
    tenant_id = str(uuid.uuid4())
    tenant = Tenant(id=tenant_id, name="Acme", api_key_hash="hash")
    session.get.return_value = tenant

    assert repo.delete_tenant(tenant_id) is True
    session.delete.assert_called_once_with(tenant)
    session.flush.assert_called_once()


def test_delete_tenant_returns_false_when_missing(repo: TenantRepository, session: MagicMock) -> None:
    session.get.return_value = None
    assert repo.delete_tenant(str(uuid.uuid4())) is False

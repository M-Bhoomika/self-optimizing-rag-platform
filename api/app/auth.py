"""API key authentication and tenant resolution."""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import uuid
from dataclasses import dataclass
from typing import Dict, Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from api.config.settings import get_settings
from api.repositories.queries import QueryRepository
from api.repositories.tenants import TenantRepository

logger = logging.getLogger(__name__)

_MEMORY_TENANTS: Dict[str, "TenantContext"] = {}
_MEMORY_QUERY_COUNTS: Dict[str, int] = {}
_MEMORY_DOC_COUNTS: Dict[str, int] = {}


@dataclass
class TenantContext:
    id: str
    name: str
    document_quota: Optional[int] = None
    query_quota_per_day: Optional[int] = None


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def verify_api_key(raw_key: str, stored_hash: str) -> bool:
    return hmac.compare_digest(hash_api_key(raw_key), stored_hash)


def register_test_tenant(
    raw_key: str,
    tenant_id: Optional[str] = None,
    name: str = "test-tenant",
    document_quota: int = 1000,
    query_quota_per_day: int = 1000,
) -> TenantContext:
    tid = tenant_id or str(uuid.uuid4())
    tenant = TenantContext(
        id=tid,
        name=name,
        document_quota=document_quota,
        query_quota_per_day=query_quota_per_day,
    )
    _MEMORY_TENANTS[hash_api_key(raw_key)] = tenant
    return tenant


def clear_test_tenants() -> None:
    _MEMORY_TENANTS.clear()
    _MEMORY_QUERY_COUNTS.clear()
    _MEMORY_DOC_COUNTS.clear()


def _tenant_from_orm(orm_tenant) -> TenantContext:
    return TenantContext(
        id=str(orm_tenant.id),
        name=orm_tenant.name,
        document_quota=orm_tenant.document_quota,
        query_quota_per_day=orm_tenant.query_quota_per_day,
    )


def _lookup_tenant_from_db(key_hash: str) -> Optional[TenantContext]:
    if os.getenv("SKIP_DB", "").lower() in {"1", "true", "yes"}:
        return None
    try:
        from api.db.session import get_db_session
        from api.repositories.tenants import TenantRepository

        with get_db_session() as session:
            orm_tenant = TenantRepository(session).get_by_api_key_hash(key_hash)
            if orm_tenant is not None:
                return _tenant_from_orm(orm_tenant)
    except Exception as exc:
        logger.debug("Database tenant lookup unavailable: %s", exc)
    return None


class TenantAuthService:
    def __init__(self, session: Optional[Session] = None) -> None:
        self._tenant_repo = TenantRepository(session) if session is not None else None
        self._query_repo = QueryRepository(session) if session is not None else None

    def resolve_tenant(self, raw_key: str) -> Optional[TenantContext]:
        if not raw_key or not raw_key.strip():
            return None
        key_hash = hash_api_key(raw_key.strip())
        if key_hash in _MEMORY_TENANTS:
            return _MEMORY_TENANTS[key_hash]
        if self._tenant_repo is not None:
            orm_tenant = self._tenant_repo.get_by_api_key_hash(key_hash)
            if orm_tenant is not None:
                return _tenant_from_orm(orm_tenant)
        return _lookup_tenant_from_db(key_hash)

    def enforce_query_quota(self, tenant: TenantContext) -> None:
        quota = tenant.query_quota_per_day
        if quota is None or quota <= 0:
            return
        if self._query_repo is not None:
            used = self._query_repo.count_queries_today(tenant.id)
        else:
            used = _MEMORY_QUERY_COUNTS.get(tenant.id, 0)
        if used >= quota:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily query quota exceeded ({quota}).",
            )

    def record_query_usage(self, tenant_id: str) -> None:
        if self._query_repo is None:
            _MEMORY_QUERY_COUNTS[tenant_id] = _MEMORY_QUERY_COUNTS.get(tenant_id, 0) + 1

    def enforce_document_quota(self, tenant: TenantContext) -> None:
        quota = tenant.document_quota
        if quota is None or quota <= 0:
            return
        used: Optional[int] = None
        if self._tenant_repo is not None:
            try:
                from api.repositories.documents import DocumentRepository

                session = self._tenant_repo.session
                used = DocumentRepository(session).count_documents_for_tenant(tenant.id)
            except Exception:
                used = None
        if used is None:
            from api.services.document_persistence import DocumentPersistenceService

            used = DocumentPersistenceService().count_documents(tenant.id)
        if used is None:
            used = _MEMORY_DOC_COUNTS.get(tenant.id, 0)
        if used >= quota:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Document quota exceeded ({quota}).",
            )

    def record_document_upload(self, tenant_id: str) -> None:
        _MEMORY_DOC_COUNTS[tenant_id] = _MEMORY_DOC_COUNTS.get(tenant_id, 0) + 1

    @staticmethod
    def validate_tenant_isolation(authenticated_id: str, requested_id: str) -> None:
        if str(authenticated_id) != str(requested_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="tenant_id does not match authenticated tenant.",
            )


def resolve_tenant_context(
    tenant_id: str,
    x_tenant_key: Optional[str] = Header(None, alias="X-Tenant-Key"),
) -> TenantContext:
    from api.app.dependencies import get_tenant_auth_service

    auth_service = get_tenant_auth_service()
    settings = get_settings()
    if settings.auth.required:
        if not x_tenant_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Missing {settings.auth.header_name} header.",
            )
        tenant = auth_service.resolve_tenant(x_tenant_key)
        if tenant is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key.",
            )
        auth_service.enforce_query_quota(tenant)
        auth_service.validate_tenant_isolation(tenant.id, tenant_id)
        return tenant

    if x_tenant_key:
        tenant = auth_service.resolve_tenant(x_tenant_key)
        if tenant is not None:
            auth_service.validate_tenant_isolation(tenant.id, tenant_id)
            return tenant

    return TenantContext(id=tenant_id, name=f"anonymous:{tenant_id}")

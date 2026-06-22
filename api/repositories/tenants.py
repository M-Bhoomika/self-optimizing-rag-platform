"""Tenant persistence repository."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.models.tenant import Tenant


class TenantRepository:
    """Data-access methods for :class:`Tenant` rows."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_tenant(
        self,
        name: str,
        api_key_hash: str,
        document_quota: int = 1000,
        query_quota_per_day: int = 1000,
    ) -> Tenant:
        """Create and persist a new tenant.

        Raises:
            ValueError: if ``name`` or ``api_key_hash`` is empty.
        """
        if not name or not name.strip():
            raise ValueError("name must not be empty.")
        if not api_key_hash or not api_key_hash.strip():
            raise ValueError("api_key_hash must not be empty.")

        tenant = Tenant(
            name=name.strip(),
            api_key_hash=api_key_hash,
            document_quota=document_quota,
            query_quota_per_day=query_quota_per_day,
        )
        self.session.add(tenant)
        self.session.flush()
        return tenant

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Return a tenant by id, or ``None`` if not found."""
        if not tenant_id:
            raise ValueError("tenant_id must not be empty.")
        return self.session.get(Tenant, tenant_id)

    def get_by_api_key_hash(self, api_key_hash: str) -> Optional[Tenant]:
        """Return a tenant by its API key hash, or ``None`` if not found."""
        if not api_key_hash:
            raise ValueError("api_key_hash must not be empty.")
        stmt = select(Tenant).where(Tenant.api_key_hash == api_key_hash)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_tenants(self, limit: int = 100) -> List[Tenant]:
        """Return tenants ordered by creation time, newest first."""
        if limit <= 0:
            raise ValueError("limit must be greater than 0.")
        stmt = select(Tenant).order_by(Tenant.created_at.desc()).limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def update_tenant(
        self,
        tenant_id: str,
        *,
        name: Optional[str] = None,
        api_key_hash: Optional[str] = None,
        document_quota: Optional[int] = None,
        query_quota_per_day: Optional[int] = None,
    ) -> Optional[Tenant]:
        """Update tenant fields and return the row, or ``None`` if not found."""
        tenant = self.get_tenant(tenant_id)
        if tenant is None:
            return None
        if name is not None:
            if not name.strip():
                raise ValueError("name must not be empty.")
            tenant.name = name.strip()
        if api_key_hash is not None:
            if not api_key_hash.strip():
                raise ValueError("api_key_hash must not be empty.")
            tenant.api_key_hash = api_key_hash.strip()
        if document_quota is not None:
            tenant.document_quota = document_quota
        if query_quota_per_day is not None:
            tenant.query_quota_per_day = query_quota_per_day
        self.session.flush()
        return tenant

    def delete_tenant(self, tenant_id: str) -> bool:
        """Delete a tenant by id. Returns ``True`` when a row was removed."""
        tenant = self.get_tenant(tenant_id)
        if tenant is None:
            return False
        self.session.delete(tenant)
        self.session.flush()
        return True

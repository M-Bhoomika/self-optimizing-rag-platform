"""Document persistence repository."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.models.document import Document


class DocumentRepository:
    """Data-access methods for :class:`Document` rows."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_document(
        self,
        tenant_id: str,
        title: str,
        content: str,
        document_type: str,
        s3_key: Optional[str] = None,
        embedding_model: Optional[str] = None,
    ) -> Document:
        """Create and persist a new document.

        Raises:
            ValueError: if ``tenant_id`` or ``document_type`` is empty.
        """
        if not tenant_id:
            raise ValueError("tenant_id must not be empty.")
        if not document_type or not document_type.strip():
            raise ValueError("document_type must not be empty.")

        document = Document(
            tenant_id=tenant_id,
            title=title,
            content=content,
            document_type=document_type,
            s3_key=s3_key,
            embedding_model=embedding_model,
        )
        self.session.add(document)
        self.session.flush()
        return document

    def get_document(self, document_id: str) -> Optional[Document]:
        """Return a document by id, or ``None`` if not found."""
        if not document_id:
            raise ValueError("document_id must not be empty.")
        return self.session.get(Document, document_id)

    def list_documents_for_tenant(self, tenant_id: str) -> List[Document]:
        """Return all documents for a tenant, newest first."""
        if not tenant_id:
            raise ValueError("tenant_id must not be empty.")
        stmt = (
            select(Document)
            .where(Document.tenant_id == tenant_id)
            .order_by(Document.created_at.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

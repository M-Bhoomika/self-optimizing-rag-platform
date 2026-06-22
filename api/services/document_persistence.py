"""PostgreSQL persistence for ingested documents and chunks."""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

from api.repositories.chunks import ChunkRepository
from api.repositories.documents import DocumentRepository

logger = logging.getLogger(__name__)


class DocumentPersistenceService:
    """Persist uploaded documents and chunk embeddings to PostgreSQL."""

    def persist_ingestion(
        self,
        tenant_id: str,
        title: str,
        content: str,
        document_type: str,
        source: str,
        chunk_records: Sequence[Dict[str, Any]],
        embedding_model: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        if os.getenv("SKIP_DB", "").lower() in {"1", "true", "yes"}:
            return None
        try:
            from api.db.session import get_db_session

            with get_db_session() as session:
                doc_repo = DocumentRepository(session)
                chunk_repo = ChunkRepository(session)
                document = doc_repo.create_document(
                    tenant_id=tenant_id,
                    title=title,
                    content=content,
                    document_type=document_type,
                    s3_key=source,
                    embedding_model=embedding_model,
                )
                document.ingested_at = datetime.now(timezone.utc)
                document.chunk_count = len(chunk_records)
                batch: List[tuple[int, str, Sequence[float]]] = []
                for record in chunk_records:
                    batch.append(
                        (
                            int(record["chunk_index"]),
                            str(record["chunk_text"]),
                            record["embedding"],
                        )
                    )
                chunks = chunk_repo.create_chunks_batch(
                    tenant_id=tenant_id,
                    document_id=str(document.id),
                    chunks=batch,
                )
                return {
                    "document_id": str(document.id),
                    "tenant_id": tenant_id,
                    "chunk_count": len(chunks),
                    "persisted": True,
                }
        except Exception as exc:
            logger.warning("Document persistence skipped: %s", exc)
            return None

    def count_documents(self, tenant_id: str) -> Optional[int]:
        if os.getenv("SKIP_DB", "").lower() in {"1", "true", "yes"}:
            return None
        try:
            from api.db.session import get_db_session

            with get_db_session() as session:
                return DocumentRepository(session).count_documents_for_tenant(tenant_id)
        except Exception as exc:
            logger.debug("Document count unavailable: %s", exc)
            return None

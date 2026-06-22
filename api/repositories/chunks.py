"""Chunk persistence repository."""

from __future__ import annotations

from typing import List, Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.models.chunk import Chunk


class ChunkRepository:
    """Data-access methods for :class:`Chunk` rows."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_chunk(
        self,
        tenant_id: str,
        document_id: str,
        chunk_text: str,
        chunk_index: int,
        embedding: Optional[Sequence[float]] = None,
    ) -> Chunk:
        if not tenant_id:
            raise ValueError("tenant_id must not be empty.")
        if not document_id:
            raise ValueError("document_id must not be empty.")
        if not chunk_text or not chunk_text.strip():
            raise ValueError("chunk_text must not be empty.")

        chunk = Chunk(
            tenant_id=tenant_id,
            document_id=document_id,
            chunk_text=chunk_text,
            chunk_index=chunk_index,
            embedding_vector=list(embedding) if embedding is not None else None,
        )
        self.session.add(chunk)
        self.session.flush()
        return chunk

    def create_chunks_batch(
        self,
        tenant_id: str,
        document_id: str,
        chunks: Sequence[tuple[int, str, Sequence[float]]],
    ) -> List[Chunk]:
        created: List[Chunk] = []
        for chunk_index, chunk_text, embedding in chunks:
            created.append(
                self.create_chunk(
                    tenant_id=tenant_id,
                    document_id=document_id,
                    chunk_text=chunk_text,
                    chunk_index=chunk_index,
                    embedding=embedding,
                )
            )
        return created

    def list_chunks_for_document(self, document_id: str) -> List[Chunk]:
        if not document_id:
            raise ValueError("document_id must not be empty.")
        stmt = (
            select(Chunk)
            .where(Chunk.document_id == document_id)
            .order_by(Chunk.chunk_index.asc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def count_chunks_for_tenant(self, tenant_id: str) -> int:
        if not tenant_id:
            raise ValueError("tenant_id must not be empty.")
        stmt = select(func.count()).select_from(Chunk).where(Chunk.tenant_id == tenant_id)
        return int(self.session.execute(stmt).scalar_one())

"""Chunk ORM model.

Maps the ``chunks`` table defined in ``api/db/schema.sql``.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .document import Document
    from .tenant import Tenant


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # TODO(embedding): The `embedding_vector` column is defined in schema.sql as
    # VECTOR(1536) (pgvector). pgvector ORM integration is intentionally not
    # implemented yet. When ready, map this with the pgvector SQLAlchemy type,
    # e.g. `from pgvector.sqlalchemy import Vector` and
    # `embedding_vector: Mapped[list[float] | None] = mapped_column(Vector(1536))`.
    # Embedding dimension: 1536.

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    document: Mapped["Document"] = relationship(back_populates="chunks")
    tenant: Mapped["Tenant"] = relationship(back_populates="chunks")

    def __repr__(self) -> str:
        return f"<Chunk id={self.id!r} document_id={self.document_id!r} index={self.chunk_index!r}>"

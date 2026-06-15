"""Ingestion-domain data structures.

Lightweight dataclasses used throughout the ingestion pipeline. These are
plain in-memory representations and are intentionally decoupled from the ORM
models and the database layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class DocumentMetadata:
    """Metadata describing a source document being ingested."""

    title: str
    source: str
    document_type: str
    tenant_id: str


@dataclass
class DocumentChunk:
    """A single chunk produced from a document."""

    chunk_index: int
    chunk_text: str
    metadata: Dict[str, Any] = field(default_factory=dict)

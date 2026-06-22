"""Shared vector-store item type used by production store implementations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Sequence


@dataclass
class VectorStoreItem:
    """A single chunk record to upsert into a vector store."""

    tenant_id: str
    chunk_id: str
    document_id: str
    embedding: Sequence[float]
    chunk_text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


def normalize_items(
    items: Sequence[VectorStoreItem | Dict[str, Any]] | None = None,
    **kwargs: Any,
) -> list[VectorStoreItem]:
    """Build :class:`VectorStoreItem` instances from a batch or single upsert call."""
    if items is not None:
        normalized: list[VectorStoreItem] = []
        for item in items:
            if isinstance(item, VectorStoreItem):
                normalized.append(item)
            elif isinstance(item, dict):
                normalized.append(
                    VectorStoreItem(
                        tenant_id=str(item["tenant_id"]),
                        chunk_id=str(item["chunk_id"]),
                        document_id=str(item["document_id"]),
                        embedding=item["embedding"],
                        chunk_text=str(item["chunk_text"]),
                        metadata=dict(item.get("metadata") or {}),
                    )
                )
            else:
                raise TypeError(f"Unsupported item type: {type(item)!r}")
        return normalized

    required = ("tenant_id", "chunk_id", "document_id", "embedding", "chunk_text")
    missing = [name for name in required if name not in kwargs]
    if missing:
        raise TypeError(
            "upsert() requires either `items` or keyword arguments: "
            + ", ".join(required)
        )

    return [
        VectorStoreItem(
            tenant_id=str(kwargs["tenant_id"]),
            chunk_id=str(kwargs["chunk_id"]),
            document_id=str(kwargs["document_id"]),
            embedding=kwargs["embedding"],
            chunk_text=str(kwargs["chunk_text"]),
            metadata=dict(kwargs.get("metadata") or {}),
        )
    ]

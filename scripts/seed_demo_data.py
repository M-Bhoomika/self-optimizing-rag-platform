#!/usr/bin/env python3
"""Generate in-memory demo data for local development and smoke tests.

Creates sample tenants, documents, chunks, and retrieval examples without
requiring a running database. Optionally indexes chunks into the in-memory
vector store and runs a sample retrieval query.

Usage:
    python scripts/seed_demo_data.py
    python scripts/seed_demo_data.py --dry-run
    python scripts/seed_demo_data.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List

# Ensure project root is on sys.path when run as a script.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.embeddings.providers import DummyEmbeddingProvider
from api.ingestion.chunker import chunk_text
from api.retrieval.schemas import RetrievalRequest
from api.retrieval.service import RetrievalService
from api.retrieval.vector_store import InMemoryVectorStore


@dataclass
class DemoTenant:
    id: str
    name: str
    document_quota: int = 1000
    query_quota_per_day: int = 1000


@dataclass
class DemoDocument:
    id: str
    tenant_id: str
    title: str
    content: str
    document_type: str = "txt"


@dataclass
class DemoChunk:
    chunk_id: str
    document_id: str
    tenant_id: str
    chunk_text: str
    chunk_index: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DemoDataset:
    tenants: List[DemoTenant]
    documents: List[DemoDocument]
    chunks: List[DemoChunk]
    retrieval_examples: List[Dict[str, Any]]


DEMO_DOCUMENTS: List[Dict[str, str]] = [
    {
        "title": "Introduction to RAG",
        "content": (
            "Retrieval-Augmented Generation combines document retrieval with "
            "language model generation. The system retrieves relevant chunks "
            "and uses them as context for answer generation."
        ),
    },
    {
        "title": "Vector Search Basics",
        "content": (
            "Vector search finds similar items by comparing embedding vectors. "
            "Cosine similarity and approximate nearest-neighbor indexes such as "
            "FAISS enable fast retrieval at scale."
        ),
    },
    {
        "title": "Multi-Tenant Architecture",
        "content": (
            "Multi-tenant platforms isolate customer data using tenant identifiers. "
            "Documents, chunks, and queries are scoped to a tenant to prevent "
            "cross-tenant data leakage."
        ),
    },
]

RETRIEVAL_QUERIES: List[str] = [
    "How does RAG work?",
    "What is vector search?",
    "How is tenant isolation enforced?",
]


def build_demo_dataset() -> DemoDataset:
    """Construct deterministic demo tenants, documents, chunks, and queries."""
    tenant = DemoTenant(
        id=str(uuid.uuid5(uuid.NAMESPACE_DNS, "demo-tenant")),
        name="Demo Tenant",
    )

    documents: List[DemoDocument] = []
    chunks: List[DemoChunk] = []

    for index, spec in enumerate(DEMO_DOCUMENTS):
        document_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"demo-doc-{index}"))
        document = DemoDocument(
            id=document_id,
            tenant_id=tenant.id,
            title=spec["title"],
            content=spec["content"],
        )
        documents.append(document)

        for chunk in chunk_text(document.content, chunk_size=120, overlap=20):
            chunks.append(
                DemoChunk(
                    chunk_id=f"{document_id}:{chunk.chunk_index}",
                    document_id=document_id,
                    tenant_id=tenant.id,
                    chunk_text=chunk.chunk_text,
                    chunk_index=chunk.chunk_index,
                    metadata={"title": document.title, **chunk.metadata},
                )
            )

    retrieval_examples = [
        {"tenant_id": tenant.id, "query": query, "top_k": 3}
        for query in RETRIEVAL_QUERIES
    ]

    return DemoDataset(
        tenants=[tenant],
        documents=documents,
        chunks=chunks,
        retrieval_examples=retrieval_examples,
    )


def run_retrieval_demo(dataset: DemoDataset) -> List[Dict[str, Any]]:
    """Index demo chunks and execute sample retrieval queries."""
    service = RetrievalService(
        embedding_provider=DummyEmbeddingProvider(),
        vector_store=InMemoryVectorStore(),
    )
    indexed = service.index_chunks(
        [
            {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "tenant_id": chunk.tenant_id,
                "chunk_text": chunk.chunk_text,
                "metadata": chunk.metadata,
            }
            for chunk in dataset.chunks
        ]
    )

    results: List[Dict[str, Any]] = []
    for example in dataset.retrieval_examples:
        response = service.retrieve(
            RetrievalRequest(
                tenant_id=example["tenant_id"],
                query=example["query"],
                top_k=example["top_k"],
            )
        )
        results.append(
            {
                "query": example["query"],
                "indexed_chunks": indexed,
                "retrieved_count": len(response.results),
                "top_result": response.results[0].chunk_text if response.results else None,
            }
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate in-memory demo data.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build demo data without running retrieval examples.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print output as JSON.",
    )
    args = parser.parse_args()

    dataset = build_demo_dataset()
    output: Dict[str, Any] = {
        "tenants": [asdict(t) for t in dataset.tenants],
        "documents": [asdict(d) for d in dataset.documents],
        "chunks": [asdict(c) for c in dataset.chunks],
        "retrieval_examples": dataset.retrieval_examples,
    }

    if not args.dry_run:
        output["retrieval_results"] = run_retrieval_demo(dataset)

    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print(f"Tenants:   {len(dataset.tenants)}")
        print(f"Documents: {len(dataset.documents)}")
        print(f"Chunks:    {len(dataset.chunks)}")
        print(f"Queries:   {len(dataset.retrieval_examples)}")
        if not args.dry_run:
            print(f"Retrieval runs: {len(output.get('retrieval_results', []))}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

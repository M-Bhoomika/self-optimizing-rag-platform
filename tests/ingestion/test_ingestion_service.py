"""Tests for the document ingestion workflow."""

from __future__ import annotations

import pytest

from api.embeddings.providers import DummyEmbeddingProvider
from api.ingestion.service import IngestionService
from api.retrieval.vector_store import InMemoryVectorStore

TENANT_ID = "tenant-1"


@pytest.fixture
def store() -> InMemoryVectorStore:
    return InMemoryVectorStore()


@pytest.fixture
def service(store: InMemoryVectorStore) -> IngestionService:
    return IngestionService(
        embedding_provider=DummyEmbeddingProvider(),
        vector_store=store,
    )


def test_txt_ingestion(service: IngestionService) -> None:
    summary = service.ingest_document(
        tenant_id=TENANT_ID,
        document_id="doc-txt",
        title="Plain text",
        content="Hello world. This is a plain text document.",
        document_type="txt",
        source="upload",
    )
    assert summary["document_id"] == "doc-txt"
    assert summary["tenant_id"] == TENANT_ID
    assert summary["chunk_count"] >= 1
    assert summary["indexed_count"] == summary["chunk_count"]
    assert len(summary.get("chunk_records", [])) == summary["chunk_count"]


def test_markdown_ingestion(service: IngestionService) -> None:
    summary = service.ingest_document(
        tenant_id=TENANT_ID,
        document_id="doc-md",
        title="Markdown",
        content="# Heading\n\nSome **bold** markdown content here.",
        document_type="markdown",
        source="upload",
    )
    assert summary["chunk_count"] >= 1
    assert summary["indexed_count"] == summary["chunk_count"]
    assert len(summary.get("chunk_records", [])) == summary["chunk_count"]


def test_html_ingestion(service: IngestionService) -> None:
    summary = service.ingest_document(
        tenant_id=TENANT_ID,
        document_id="doc-html",
        title="HTML",
        content="<html><body><p>Hello <b>world</b></p></body></html>",
        document_type="html",
        source="upload",
    )
    assert summary["chunk_count"] >= 1
    assert summary["indexed_count"] == summary["chunk_count"]
    assert len(summary.get("chunk_records", [])) == summary["chunk_count"]


def test_unsupported_document_type_raises(service: IngestionService) -> None:
    with pytest.raises(ValueError):
        service.ingest_document(
            tenant_id=TENANT_ID,
            document_id="doc-bad",
            title="Bad",
            content="some content",
            document_type="docx",
            source="upload",
        )


def test_empty_content_raises(service: IngestionService) -> None:
    with pytest.raises(ValueError):
        service.ingest_document(
            tenant_id=TENANT_ID,
            document_id="doc-empty",
            title="Empty",
            content="   ",
            document_type="txt",
            source="upload",
        )


def test_ingestion_indexes_chunks(service: IngestionService, store: InMemoryVectorStore) -> None:
    service.ingest_document(
        tenant_id=TENANT_ID,
        document_id="doc-idx",
        title="Indexed",
        content="Vector databases enable fast similarity search across many chunks.",
        document_type="txt",
        source="upload",
    )

    results = store.similarity_search(
        tenant_id=TENANT_ID,
        query_embedding=DummyEmbeddingProvider().embed_query("similarity search"),
        top_k=10,
    )
    assert len(results) >= 1
    assert all(r.document_id == "doc-idx" for r in results)

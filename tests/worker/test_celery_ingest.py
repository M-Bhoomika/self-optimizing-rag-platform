"""Celery ingestion task tests (mocked, Celery not required)."""

from __future__ import annotations

from unittest.mock import patch

from worker import ingest as worker_ingest


def test_is_celery_enabled_false_by_default() -> None:
    assert worker_ingest.is_celery_enabled() is False


def test_ingest_document_task_sync_fallback() -> None:
    payload = {
        "tenant_id": "worker-tenant",
        "title": "Worker Doc",
        "content": "Vector databases enable fast similarity search across chunks.",
        "document_type": "txt",
        "source": "test",
    }
    with patch("api.worker.ingest_pipeline.run_full_ingestion") as mock_run:
        mock_run.return_value = {"status": "completed", "ingestion": {"chunk_count": 2}}
        result = worker_ingest.ingest_document_task(payload)
    assert result["status"] == "completed"
    mock_run.assert_called_once_with(payload)

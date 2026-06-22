"""Worker queue tests."""

from __future__ import annotations

from api.worker.executor import execute_task
from api.worker.queue import TaskQueue


def test_memory_queue_enqueue_dequeue() -> None:
    queue = TaskQueue(redis_url="")
    task = queue.enqueue(
        "ingest",
        {
            "tenant_id": "worker-tenant",
            "title": "Worker Doc",
            "content": "Background ingestion content for testing.",
            "document_type": "txt",
        },
    )
    assert task.task_id
    raw = queue.dequeue(timeout_seconds=1.0)
    assert raw is not None
    assert raw["type"] == "ingest"
    assert raw["payload"]["tenant_id"] == "worker-tenant"


def test_execute_ingest_task() -> None:
    result = execute_task(
        {
            "task_id": "task-1",
            "type": "ingest",
            "payload": {
                "tenant_id": "worker-tenant",
                "title": "Worker Doc",
                "content": "Vector databases enable fast similarity search.",
                "document_type": "txt",
            },
        }
    )
    assert result["status"] == "completed"
    assert result["ingestion"]["chunk_count"] >= 1

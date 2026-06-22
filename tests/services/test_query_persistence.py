"""Query persistence service tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from api.services.query_persistence import QueryPersistenceService


def test_persist_query_graceful_when_db_unavailable() -> None:
    service = QueryPersistenceService()
    with patch("api.db.session.get_db_session", side_effect=RuntimeError("db down")):
        result = service.persist_query(
            tenant_id="tenant-1",
            query_text="hello",
            answer_text="world",
            retrieved_chunk_ids=["c1"],
            latency_ms=10,
            model_version="local-fallback",
            cached=False,
        )
    assert result is None


def test_persist_query_success_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKIP_DB", "false")
    service = QueryPersistenceService()
    mock_session = MagicMock()
    mock_repo = MagicMock()
    mock_repo.create_query_record.return_value = {"id": "q1", "tenant_id": "tenant-1"}
    with patch("api.db.session.get_db_session") as mock_ctx:
        mock_ctx.return_value.__enter__.return_value = mock_session
        with patch("api.services.query_persistence.QueryRepository", return_value=mock_repo):
            result = service.persist_query(
                tenant_id="tenant-1",
                query_text="hello",
                answer_text="world",
                retrieved_chunk_ids=["c1"],
                latency_ms=10,
                model_version="local-fallback",
                cached=False,
            )
    assert result == {"id": "q1", "tenant_id": "tenant-1"}

"""Tracing helper tests."""

from __future__ import annotations

from api.observability.tracing import setup_tracing, trace_span


def test_setup_tracing_noop_without_otel() -> None:
    assert setup_tracing(app=None) is False


def test_trace_span_noop_without_otel() -> None:
    with trace_span("test.span", {"key": "value"}):
        assert True

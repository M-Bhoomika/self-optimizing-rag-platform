"""Prometheus metrics definitions with optional prometheus_client dependency."""

from __future__ import annotations

from typing import Any, Optional


class MetricsRegistry:
    """Wraps Prometheus metrics when prometheus_client is installed."""

    def __init__(self) -> None:
        self.enabled = False
        self.request_count: Any = None
        self.request_latency_seconds: Any = None
        self.retrieval_latency_seconds: Any = None
        self.generation_latency_seconds: Any = None
        self.cache_hit_rate: Any = None
        self.context_recall_score: Any = None
        self.unanswered_query_rate: Any = None

        try:
            from prometheus_client import Counter, Gauge, Histogram  # type: ignore

            self.request_count = Counter(
                "request_count", "Total HTTP requests", ["method", "path", "status"]
            )
            self.request_latency_seconds = Histogram(
                "request_latency_seconds", "HTTP request latency in seconds", ["method", "path"]
            )
            self.retrieval_latency_seconds = Histogram(
                "retrieval_latency_seconds", "Retrieval latency in seconds"
            )
            self.generation_latency_seconds = Histogram(
                "generation_latency_seconds", "Generation latency in seconds"
            )
            self.cache_hit_rate = Gauge("cache_hit_rate", "Cache hit rate for query cache")
            self.context_recall_score = Gauge(
                "context_recall_score", "Latest observed context recall score"
            )
            self.unanswered_query_rate = Gauge(
                "unanswered_query_rate", "Rate of unanswered/low-confidence queries"
            )
            self.enabled = True
        except ImportError:
            self.enabled = False

    def observe_cache_hit(self, hit: bool) -> None:
        if self.enabled and self.cache_hit_rate is not None:
            self.cache_hit_rate.set(1.0 if hit else 0.0)


_metrics: Optional[MetricsRegistry] = None


def get_metrics() -> MetricsRegistry:
    global _metrics
    if _metrics is None:
        _metrics = MetricsRegistry()
    return _metrics

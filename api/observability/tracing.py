"""Optional OpenTelemetry tracing for FastAPI and RAG pipeline stages."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Iterator, Optional

logger = logging.getLogger(__name__)

_tracer: Any = None
_enabled = False


def setup_tracing(app: Any = None, service_name: str = "rag-platform") -> bool:
    """Configure OTLP export and FastAPI instrumentation when explicitly enabled."""
    global _tracer, _enabled
    if _enabled:
        return True

    import os

    enabled_flag = os.getenv("OTEL_TRACING_ENABLED", "").lower() in {"1", "true", "yes"}
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not enabled_flag and not endpoint:
        return False

    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        from opentelemetry import trace

        otlp_endpoint = endpoint or "http://localhost:4317"
        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True))
        )
        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer(service_name)

        if app is not None:
            FastAPIInstrumentor.instrument_app(app)

        _enabled = True
        logger.info("OpenTelemetry tracing enabled (endpoint=%s)", otlp_endpoint)
        return True
    except ImportError:
        logger.debug("OpenTelemetry packages not installed; tracing disabled.")
        return False
    except Exception as exc:
        logger.warning("Tracing setup failed: %s", exc)
        return False


def get_tracer(name: str = "rag-platform"):
    if _tracer is not None:
        return _tracer
    import os

    if os.getenv("OTEL_TRACING_ENABLED", "").lower() not in {"1", "true", "yes"} and not os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT"
    ):
        return None
    try:
        from opentelemetry import trace

        return trace.get_tracer(name)
    except ImportError:
        return None


@contextmanager
def trace_span(name: str, attributes: Optional[dict[str, Any]] = None) -> Iterator[None]:
    tracer = get_tracer()
    if tracer is None:
        yield
        return
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        yield

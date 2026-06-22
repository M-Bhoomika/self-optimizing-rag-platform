"""Streaming query API routes with Redis caching and SSE."""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, AsyncIterator, Dict, List, Optional

from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.app.auth import TenantContext, resolve_tenant_context
from api.app.dependencies import (
    get_cache,
    get_pipeline,
    get_query_persistence,
    get_tenant_auth_service,
)
from api.cache.redis_cache import RedisCache
from api.observability.metrics import get_metrics
from api.retrieval.pipeline import IterativeRetrievalPipeline
from api.services.query_persistence import QueryPersistenceService

router = APIRouter(prefix="/api/v1/query", tags=["query"])


class StreamQueryRequest(BaseModel):
    tenant_id: str
    query: str
    top_k: int = 5
    use_cache: bool = True
    ttl: int = 300


def get_authenticated_tenant(
    request: StreamQueryRequest,
    x_tenant_key: Optional[str] = Header(None, alias="X-Tenant-Key"),
) -> TenantContext:
    return resolve_tenant_context(request.tenant_id, x_tenant_key)


def _pipeline_payload(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "answer": state.get("answer", ""),
        "citations": state.get("citations", []),
        "relevance_score": state.get("relevance_score", 0.0),
        "confidence_score": state.get("confidence_score", 0.0),
        "low_confidence": state.get("low_confidence", False),
        "model": state.get("model", ""),
    }


def _chunk_ids(citations: List[Dict[str, Any]]) -> List[str]:
    return [str(c.get("chunk_id", "")) for c in citations if c.get("chunk_id")]


def _persist_query(
    persistence: QueryPersistenceService,
    tenant_id: str,
    query: str,
    payload: Dict[str, Any],
    latency_ms: int,
    cached: bool,
) -> None:
    get_tenant_auth_service().record_query_usage(tenant_id)
    context_text = " ".join(
        str(c.get("chunk_text", "")) for c in payload.get("citations", [])
    )
    persistence.persist_query(
        tenant_id=tenant_id,
        query_text=query,
        answer_text=str(payload.get("answer", "")),
        retrieved_chunk_ids=_chunk_ids(payload.get("citations", [])),
        latency_ms=latency_ms,
        model_version=str(payload.get("model", "")),
        cached=cached,
        context_text=context_text or None,
    )


async def _sse_stream(
    pipeline: IterativeRetrievalPipeline,
    request: StreamQueryRequest,
    tenant: TenantContext,
    cached: Dict[str, Any] | None,
    cache: RedisCache,
    persistence: QueryPersistenceService,
) -> AsyncIterator[str]:
    metrics = get_metrics()
    started = time.perf_counter()

    if cached is not None:
        for token in str(cached.get("answer", "")).split():
            if token:
                yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"
                await asyncio.sleep(0)
        latency_ms = int((time.perf_counter() - started) * 1000)
        _persist_query(persistence, tenant.id, request.query, cached, latency_ms, cached=True)
        yield f"data: {json.dumps({'token': '', 'done': True, 'citations': cached.get('citations', []), 'confidence_score': cached.get('confidence_score', 0.0), 'low_confidence': cached.get('low_confidence', False), 'cached': True})}\n\n"
        return

    pre_state = pipeline.run_until_generation(
        tenant_id=tenant.id,
        query=request.query,
        top_k=request.top_k,
    )
    if metrics.enabled and metrics.retrieval_latency_seconds is not None:
        metrics.retrieval_latency_seconds.observe(time.perf_counter() - started)

    chunks: List[Dict[str, Any]] = pre_state.get("reranked_chunks") or pre_state.get("retrieved_chunks", [])
    context = "\n\n".join(c["chunk_text"] for c in chunks)
    gen_service = pipeline.generation_service

    gen_start = time.perf_counter()
    for token in gen_service.stream_answer(
        question=request.query,
        context=context if context.strip() else "No retrieval context available.",
        chunks=chunks,
        retrieval_score=float(pre_state.get("relevance_score", 0.0)),
        force_low_confidence=bool(pre_state.get("low_confidence", False)) and not context.strip(),
    ):
        cleaned = token.strip()
        if cleaned:
            yield f"data: {json.dumps({'token': cleaned, 'done': False})}\n\n"
            await asyncio.sleep(0)

    if metrics.enabled and metrics.generation_latency_seconds is not None:
        metrics.generation_latency_seconds.observe(time.perf_counter() - gen_start)

    final_state = pipeline.finalize_generation(pre_state)
    payload = _pipeline_payload(final_state)
    if request.use_cache:
        cache.set(tenant.id, request.query, payload, ttl=request.ttl)

    latency_ms = int((time.perf_counter() - started) * 1000)
    _persist_query(persistence, tenant.id, request.query, payload, latency_ms, cached=False)

    if metrics.enabled and metrics.unanswered_query_rate is not None:
        metrics.unanswered_query_rate.set(1.0 if payload.get("low_confidence") else 0.0)

    yield f"data: {json.dumps({'token': '', 'done': True, 'citations': payload.get('citations', []), 'confidence_score': payload.get('confidence_score', 0.0), 'low_confidence': payload.get('low_confidence', False), 'model': payload.get('model', ''), 'cached': False})}\n\n"


@router.post("/stream")
async def stream_query(
    request: StreamQueryRequest,
    tenant: TenantContext = Depends(get_authenticated_tenant),
    cache: RedisCache = Depends(get_cache),
    pipeline: IterativeRetrievalPipeline = Depends(get_pipeline),
    persistence: QueryPersistenceService = Depends(get_query_persistence),
) -> StreamingResponse:
    metrics = get_metrics()
    cached = cache.get(tenant.id, request.query) if request.use_cache else None
    metrics.observe_cache_hit(hit=cached is not None)
    if metrics.enabled and metrics.cache_hit_rate is not None:
        metrics.cache_hit_rate.set(cache.statistics().hit_rate)

    return StreamingResponse(
        _sse_stream(pipeline, request, tenant, cached, cache, persistence),
        media_type="text/event-stream",
    )


@router.get("/cache/stats")
def cache_stats(cache: RedisCache = Depends(get_cache)) -> Dict[str, Any]:
    return cache.statistics().to_dict()


@router.get("/history")
def query_history(
    tenant_id: str,
    limit: int = 50,
    x_tenant_key: Optional[str] = Header(None, alias="X-Tenant-Key"),
    persistence: QueryPersistenceService = Depends(get_query_persistence),
) -> Dict[str, Any]:
    tenant = resolve_tenant_context(tenant_id, x_tenant_key)
    return {"tenant_id": tenant.id, "queries": persistence.list_history(tenant.id, limit=limit)}


@router.post("/generate")
def generate_answer(
    request: StreamQueryRequest,
    tenant: TenantContext = Depends(get_authenticated_tenant),
    cache: RedisCache = Depends(get_cache),
    pipeline: IterativeRetrievalPipeline = Depends(get_pipeline),
    persistence: QueryPersistenceService = Depends(get_query_persistence),
) -> Dict[str, Any]:
    metrics = get_metrics()
    cached = cache.get(tenant.id, request.query) if request.use_cache else None
    metrics.observe_cache_hit(hit=cached is not None)

    started = time.perf_counter()
    if cached is not None:
        latency_ms = int((time.perf_counter() - started) * 1000)
        _persist_query(persistence, tenant.id, request.query, cached, latency_ms, cached=True)
        return {"query": request.query, **cached, "cached": True}

    state = pipeline.run(
        tenant_id=tenant.id,
        query=request.query,
        top_k=request.top_k,
    )
    payload = _pipeline_payload(state)
    if request.use_cache:
        cache.set(tenant.id, request.query, payload, ttl=request.ttl)

    latency_ms = int((time.perf_counter() - started) * 1000)
    _persist_query(persistence, tenant.id, request.query, payload, latency_ms, cached=False)

    if metrics.enabled and metrics.unanswered_query_rate is not None:
        metrics.unanswered_query_rate.set(1.0 if payload.get("low_confidence") else 0.0)

    return {"query": request.query, **payload, "cached": False}

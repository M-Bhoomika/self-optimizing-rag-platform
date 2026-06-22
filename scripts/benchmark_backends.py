#!/usr/bin/env python3
"""Benchmark retrieval backends with build time, latency, and recall@10."""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np

from api.retrieval.factory import get_vector_store


def _seed(store, tenant_id: str, count: int, dimension: int) -> tuple[np.ndarray, List[str]]:
    rng = np.random.default_rng(42)
    vectors = rng.random((count, dimension), dtype=np.float32)
    ids: List[str] = []
    for index in range(count):
        chunk_id = f"chunk-{index}"
        ids.append(chunk_id)
        store.upsert(
            tenant_id=tenant_id,
            chunk_id=chunk_id,
            document_id="doc-1",
            embedding=vectors[index].tolist(),
            chunk_text=f"chunk text {index}",
            metadata={},
        )
    return vectors, ids


def _brute_force_recall(
    vectors: np.ndarray,
    query: np.ndarray,
    retrieved_ids: List[str],
    all_ids: List[str],
    k: int = 10,
) -> float:
    distances = np.linalg.norm(vectors - query, axis=1)
    true_top = set(all_ids[i] for i in np.argsort(distances)[:k])
    retrieved = set(retrieved_ids[:k])
    return len(true_top & retrieved) / float(k)


def benchmark_backend(backend: str, count: int, dimension: int, top_k: int) -> Dict[str, Any]:
    build_start = time.perf_counter()
    store = get_vector_store(backend)
    tenant_id = "bench-tenant"
    vectors, ids = _seed(store, tenant_id, count, dimension)
    build_time = time.perf_counter() - build_start

    query = np.random.default_rng(7).random(dimension, dtype=np.float32)
    latencies: List[float] = []
    retrieved_ids: List[str] = []
    for _ in range(100):
        start = time.perf_counter()
        results = store.similarity_search(tenant_id, query.tolist(), top_k=top_k)
        latencies.append((time.perf_counter() - start) * 1000)
        retrieved_ids = [item.chunk_id for item in results]

    latencies.sort()
    p50 = latencies[len(latencies) // 2]
    p95 = latencies[int(len(latencies) * 0.95) - 1]
    recall = _brute_force_recall(vectors, query, retrieved_ids, ids, k=min(top_k, 10))

    return {
        "backend": backend,
        "build_time_seconds": round(build_time, 4),
        "query_latency_ms_p50": round(p50, 4),
        "query_latency_ms_p95": round(p95, 4),
        "recall_at_10": round(recall, 4),
        "vector_count": count,
        "dimension": dimension,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark vector store backends")
    parser.add_argument("--backend", action="append", dest="backends")
    parser.add_argument("--count", type=int, default=500)
    parser.add_argument("--dimension", type=int, default=128)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    backends = args.backends or ["memory", "hnsw"]
    for candidate in ("faiss",):
        try:
            get_vector_store(candidate)
            backends.append(candidate)
        except Exception:
            pass

    results = [
        benchmark_backend(backend, args.count, args.dimension, args.top_k)
        for backend in backends
    ]

    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "environment": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
        },
        "results": results,
    }

    print(json.dumps(payload, indent=2))
    if args.output:
        args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

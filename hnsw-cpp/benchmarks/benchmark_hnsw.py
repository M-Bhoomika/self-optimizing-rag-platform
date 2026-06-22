#!/usr/bin/env python3
"""Benchmark HNSW (C++ extension) against FAISS when dependencies are installed.

This script measures latency on your machine and writes results to stdout.
It does not ship pre-recorded benchmark numbers.

Usage:
    python hnsw-cpp/benchmarks/benchmark_hnsw.py
    python hnsw-cpp/benchmarks/benchmark_hnsw.py --dim 128 --num-vectors 10000 --queries 100
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _try_import_hnsw():
    try:
        import hnsw_cpp  # type: ignore

        return hnsw_cpp
    except ImportError:
        return None


def _try_import_faiss():
    try:
        import faiss  # type: ignore

        return faiss
    except ImportError:
        return None


def benchmark_hnsw(vectors: np.ndarray, queries: np.ndarray, k: int, ef: int) -> float | None:
    hnsw_mod = _try_import_hnsw()
    if hnsw_mod is None:
        print("HNSW: skipped (hnsw_cpp extension not built)")
        return None

    dim = vectors.shape[1]
    index = hnsw_mod.HNSWIndex(dim, vectors.shape[0], M=16, ef_construction=200)
    ids = list(range(vectors.shape[0]))
    index.add_items(vectors.astype(np.float32), ids)

    start = time.perf_counter()
    for q in queries:
        index.search(q.astype(np.float32), k=k, ef=ef)
    elapsed = time.perf_counter() - start
    return elapsed


def benchmark_faiss(vectors: np.ndarray, queries: np.ndarray, k: int) -> float | None:
    faiss = _try_import_faiss()
    if faiss is None:
        print("FAISS: skipped (install faiss-cpu)")
        return None

    dim = vectors.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(vectors.astype(np.float32))

    start = time.perf_counter()
    for q in queries:
        index.search(q.astype(np.float32).reshape(1, -1), k)
    elapsed = time.perf_counter() - start
    return elapsed


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark HNSW vs FAISS")
    parser.add_argument("--dim", type=int, default=128)
    parser.add_argument("--num-vectors", type=int, default=5000)
    parser.add_argument("--queries", type=int, default=50)
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--ef", type=int, default=50)
    args = parser.parse_args()

    rng = np.random.default_rng(42)
    vectors = rng.random((args.num_vectors, args.dim), dtype=np.float32)
    queries = rng.random((args.queries, args.dim), dtype=np.float32)

    print(f"Config: dim={args.dim} vectors={args.num_vectors} queries={args.queries} k={args.k}")

    hnsw_elapsed = benchmark_hnsw(vectors, queries, args.k, args.ef)
    faiss_elapsed = benchmark_faiss(vectors, queries, args.k)

    if hnsw_elapsed is not None:
        print(f"HNSW total={hnsw_elapsed:.4f}s avg_query={(hnsw_elapsed / args.queries) * 1000:.3f}ms")
    if faiss_elapsed is not None:
        print(f"FAISS total={faiss_elapsed:.4f}s avg_query={(faiss_elapsed / args.queries) * 1000:.3f}ms")

    if hnsw_elapsed is None and faiss_elapsed is None:
        print("No backends available. Build hnsw_cpp or install faiss-cpu.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

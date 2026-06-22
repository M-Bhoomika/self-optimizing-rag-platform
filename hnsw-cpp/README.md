# HNSW C++ Index

C++ HNSW (Hierarchical Navigable Small World) index with pybind11 Python bindings.
Provides fast approximate nearest-neighbor search for high-dimensional embeddings.

## Build

Requires CMake 3.18+, a C++17 compiler, Python development headers, and pybind11.

```bash
cd hnsw-cpp
cmake -S . -B build -DHNSWCPP_USE_HNSWLIB=ON
cmake --build build
# Module output: build/hnsw_cpp*.so (platform dependent)
```

To build without hnswlib (brute-force fallback for development):

```bash
cmake -S . -B build -DHNSWCPP_USE_HNSWLIB=OFF
cmake --build build
```

## Python API

```python
import hnsw_cpp
import numpy as np

index = hnsw_cpp.HNSWIndex(dim=128, max_elements=10000, M=16, ef_construction=200)
vectors = np.random.rand(1000, 128).astype("float32")
ids = list(range(1000))
index.add_items(vectors, ids)

query = np.random.rand(128).astype("float32")
results = index.search(query, k=10, ef=50)  # [(id, distance), ...]

index.save("/tmp/hnsw.index")
index.load("/tmp/hnsw.index")
```

## Parameter Guide

| Parameter | Meaning |
|-----------|---------|
| **M** | Max bi-directional links per node. Higher M improves recall and index quality but increases memory and build time. Typical range: 8–64. |
| **ef_construction** | Candidate list size during index build. Higher values improve index quality at the cost of slower builds. Typical range: 100–500. |
| **ef** | Candidate list size during search. Higher ef improves recall/latency tradeoff toward recall; lower ef is faster with lower recall. Tune at query time. |

### Recall vs latency

HNSW is approximate: increasing **ef** at search time generally raises recall (finds more true nearest neighbors) but increases query latency. **ef_construction** affects index quality offline; **M** affects graph connectivity and memory footprint.

Measure recall and latency on your dataset using `benchmarks/benchmark_hnsw.py`. The script prints timings from your machine — it does not ship benchmark results.

## Benchmarks

```bash
python hnsw-cpp/benchmarks/benchmark_hnsw.py
python hnsw-cpp/benchmarks/benchmark_hnsw.py --dim 1536 --num-vectors 20000
```

Compares HNSW (when built) against FAISS flat L2 (when `faiss-cpu` is installed).

## Integration

The module is integrated as an optional retrieval backend:

- Python adapter: `api/retrieval/hnsw_store.py` (`HNSWVectorStore`, `BruteForceHNSWVectorStore`)
- Factory selection: `RETRIEVAL_BACKEND=hnsw` in `api/retrieval/factory.py`

## Future work
- Add recall@k evaluation against a brute-force gold standard in the benchmark script.
- Package build via `pip install .` / scikit-build-core.

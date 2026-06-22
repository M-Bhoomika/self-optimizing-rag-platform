# Project Scope

Honest summary of repository capabilities, intentional gaps, and expansion paths.

## Goals

- Modular multi-tenant RAG backend with testable service layers.
- Interface-driven embeddings, retrieval, generation, and evaluation.
- Local development without external APIs; optional integrations behind clear imports.
- Documented deployment scaffolds (Docker, Kubernetes, monitoring).

## Current Capabilities

| Area | Status | Notes |
|------|--------|-------|
| Database schema | Done | PostgreSQL + pgvector (`api/db/schema.sql`) |
| ORM / repositories | Done | Tenant, Document, Chunk, RagExperiment ORM; Query via SQL repository; full Tenant CRUD |
| Document/chunk persistence | Done | Upload path persists to PostgreSQL when `SKIP_DB=false` |
| Experiment persistence | Done | `rag_experiments` table via `ExperimentPersistenceService` |
| Query persistence | Done | Wired on `/api/v1/query/*` and `/api/v1/rag/query` |
| Auth / multi-tenant | Done | `X-Tenant-Key`, middleware, query/document quotas, tenant isolation |
| Ingestion | Done | Parse, validate, chunk, index + `/api/v1/documents/upload` |
| Embeddings | Done | Dummy + sentence-transformers providers |
| Retrieval stores | Done | In-memory, FAISS, Chroma, hybrid, HNSW, pgvector |
| Iterative pipeline | Done | LangGraph optional; fallback runner built-in |
| Generation | Done | Local fallback + OpenAI-compatible providers |
| Streaming SSE | Done | `/api/v1/query/stream` |
| Redis cache | Done | Key `{tenant_id}:{query_hash}`, TTL, stats |
| Worker queue | Done | Redis-backed queue + `scripts/run_worker.py` |
| Evaluation execution | Done | `EvaluationService`, `/api/v1/experiments/run` |
| Experiment tracking | Done | In-memory + optional MLflow + PostgreSQL |
| Frontend | Done | Chat, upload, experiments, dashboard, admin wired to API |
| Settings | Done | pydantic-settings env loading + validation |
| Health / readiness | Done | `/health`, `/health/ready` |
| Tracing | Done | Optional OpenTelemetry → Jaeger when enabled |
| Prometheus metrics | Scaffold | `/metrics` when `prometheus-client` installed |
| C++ HNSW | Partial | pybind11 module; BruteForce fallback when not built |
| Kubernetes | Scaffold | Manifests not cluster-validated in CI |
| Tests | Done | 95+ pytest tests (offline, `SKIP_DB=true` in CI) |

## Requires External Services

- **PostgreSQL** — persistence activates when `SKIP_DB=false` and DB is reachable.
- **Redis** — optional; in-memory cache and queue fallbacks when unavailable.
- **MLflow server** — optional; `--use-mlflow` / `use_mlflow=true` on experiment runs.
- **RAGAS LLM judges** — package optional; heuristic proxy scores run offline.
- **Compiled `hnsw_cpp`** — optional; `BruteForceHNSWVectorStore` used when extension missing.
- **OpenAI-compatible API** — optional; required only when `LLM_PROVIDER=openai`.
- **OpenTelemetry packages** — optional; tracing disabled unless explicitly enabled.

## Future Expansion

1. Validate and harden Kubernetes manifests against a live cluster.
2. Full RAGAS metric execution with configured LLM judges (beyond heuristic fallback).
3. CI lint tooling (ruff/black/mypy) to replace the current lint placeholder.
4. End-to-end integration tests against live Postgres/Redis in CI.

## Optional Dependencies

```bash
pip install prometheus-client redis langgraph ragas mlflow faiss-cpu chromadb sentence-transformers pyspark pydantic-settings python-multipart opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp opentelemetry-instrumentation-fastapi
```

Build HNSW extension:

```bash
cmake -S hnsw-cpp -B hnsw-cpp/build && cmake --build hnsw-cpp/build
```

Frontend:

```bash
cd frontend && npm install && npm run dev
```

# Project 5 Specification — Self-Optimizing RAG Platform

**Canonical source:** This document consolidates the full Project 5 requirements from the
project conversation (initial structure through final gap-closure tasks). It is the
authoritative checklist for implementation auditing.

**Status legend used in acceptance checklist:**
- Requirements must be implemented with real functionality (not placeholders) unless
  explicitly marked as scaffold/optional.
- Performance numbers in this document are **target/demo expectations**, not verified
  benchmark results, unless measured locally via provided scripts.

---

## 1. Project Overview

Build a **production-grade, multi-tenant Retrieval-Augmented Generation (RAG) platform**
that:

- Ingests enterprise documents (txt, markdown, html) and indexes them for vector search.
- Retrieves relevant context iteratively (query rewrite, relevance assessment, reranking).
- Generates grounded answers with citations, confidence scoring, and low-confidence routing.
- Caches repeated queries in Redis.
- Streams answers to clients over Server-Sent Events (SSE).
- Evaluates retrieval/generation quality (heuristic + optional RAGAS).
- Tracks experiments (in-memory + optional MLflow).
- Exposes observability (Prometheus metrics, Grafana dashboard scaffold).
- Supports optional high-performance vector search (C++ HNSW, FAISS, Chroma, hybrid).
- Provides a Next.js frontend for chat, document upload, experiments, and dashboard.
- Deploys via Docker Compose and Kubernetes manifests (scaffold).

**Design principles:**
- Multi-tenant isolation at retrieval, cache, and auth layers.
- Interface-driven providers (embeddings, LLM, vector stores).
- Repository pattern for PostgreSQL persistence.
- Graceful degradation when optional dependencies (Redis, RAGAS, MLflow, hnsw_cpp) are
  unavailable.
- No fabricated benchmark numbers in documentation or code.

---

## 2. Complete Tech Stack with Justifications

| Layer | Technology | Justification |
|-------|------------|---------------|
| **API** | Python 3.12, FastAPI, Pydantic v2 | Async HTTP, SSE streaming, typed contracts |
| **Config** | pydantic-settings, python-dotenv | Centralized env loading and validation |
| **Database** | PostgreSQL + pgvector | Durable multi-tenant storage + vector column type |
| **ORM** | SQLAlchemy 2.x | Tenant/Document/Chunk ORM; Core SQL for query logs |
| **Cache** | Redis (optional) | Low-latency query result caching with TTL |
| **Embeddings** | Dummy (offline), sentence-transformers (local) | Testability without external APIs |
| **LLM** | Local fallback, OpenAI-compatible API | Offline dev + production gateway support |
| **Vector search** | In-memory, FAISS, ChromaDB, hybrid, HNSW (C++) | Tradeoffs: speed vs filters vs custom index |
| **Orchestration** | LangGraph (optional) | Iterative retrieval state machine |
| **Evaluation** | Heuristic metrics, RAGAS (optional) | Offline metrics + industry-standard eval |
| **Experiment tracking** | In-memory tracker, MLflow (optional) | Reproducible experiment comparison |
| **Batch ingestion** | PySpark (optional) | Large-scale document processing |
| **Observability** | prometheus-client, Grafana JSON | Standard metrics + dashboard import |
| **Frontend** | Next.js, TypeScript, React | Streaming chat UI and admin surfaces |
| **Infra** | Docker, Docker Compose, Kubernetes | Local dev and deployment scaffold |
| **Testing** | pytest | Offline unit/integration tests with mocks |

---

## 3. Step-by-Step Build Process

1. **Foundation** — README, `.gitignore`, directory structure, `docker-compose.yml`,
   `.env.example`.
2. **Database** — `api/db/schema.sql`, session management, `init_db`, ORM models,
   repositories.
3. **Ingestion** — parser, chunker, validators, `IngestionService`.
4. **Embeddings** — `EmbeddingProvider` interface, dummy + sentence-transformers,
   factory.
5. **Retrieval** — vector store abstractions (in-memory, FAISS, Chroma, hybrid, HNSW),
   `RetrievalService`, reranker.
6. **Generation** — prompts, LLM providers (local, OpenAI-compatible), structured
   responses with citations.
7. **RAG pipeline** — LangGraph or fallback runner: rewrite → retrieve → assess →
   rerank → generate.
8. **API** — FastAPI app, health/readiness, RAG routes, query/stream routes, document
   upload, experiments.
9. **Auth** — `X-Tenant-Key` resolution, middleware, quota, tenant isolation.
10. **Persistence** — query history to PostgreSQL via `QueryRepository`.
11. **Cache** — Redis wrapper with in-memory fallback, SSE streaming.
12. **Evaluation** — heuristic metrics, RAGAS integration, experiment runner.
13. **C++ HNSW** — pybind11 module + Python `VectorStore` adapter.
14. **PySpark** — batch ingestion scaffold.
15. **Observability** — Prometheus metrics middleware + `/metrics`.
16. **Frontend** — Next.js pages wired to live API.
17. **Kubernetes** — manifests with PVCs and HPA scaffold.
18. **Tests** — comprehensive pytest suite (offline by default).
19. **Documentation** — README, architecture, API reference, deployment, this spec.

---

## 4. Database Schema

Defined in `api/db/schema.sql`. Exact tables and columns:

### `tenants`
- `id` UUID PK
- `name` TEXT NOT NULL
- `api_key_hash` TEXT
- `document_quota` INTEGER
- `query_quota_per_day` INTEGER
- `created_at` TIMESTAMPTZ

### `documents`
- `id`, `tenant_id` FK, `title`, `content`, `s3_key`, `document_type`,
  `ingested_at`, `embedding_model`, `chunk_count`, `created_at`

### `chunks`
- `id`, `document_id` FK, `tenant_id` FK, `chunk_text`, `chunk_index`,
  `embedding_vector VECTOR(1536)`, `created_at`

### `queries`
- `id`, `tenant_id` FK, `query_text`, `answer_text`,
  `retrieved_chunk_ids JSONB NOT NULL DEFAULT '[]'::jsonb`,
  `faithfulness_score`, `answer_relevance_score`, `latency_ms`, `model_version`,
  `cached`, `created_at`

### `rag_experiments`
- `id`, `mlflow_run_id TEXT NOT NULL UNIQUE`, `config JSONB NOT NULL`,
  `ragas_scores JSONB NOT NULL`, `deployed_at`, `traffic_percentage DOUBLE PRECISION
  NOT NULL DEFAULT 0`, `created_at`

---

## 5. C++ HNSW with pybind11

**Location:** `hnsw-cpp/`

**Build:** CMake 3.18+, pybind11; optional hnswlib backend (`-DHNSWCPP_USE_HNSWLIB=ON`).

**Python module:** `hnsw_cpp.HNSWIndex`

**Required API surface:**
- `__init__(dim, max_elements, M=16, ef_construction=200)`
- `add_items(vectors: np.ndarray[float32, 2D], ids: list[int64])`
- `search(query_vector, k=10, ef=50) -> list[(id, distance)]`
- `save(path)`, `load(path)`
- `dim` property (read-only)

**Documentation requirements:**
- Explain `M`, `ef_construction`, `ef` search parameter.
- Explain recall/latency tradeoff (conceptual; no fabricated numbers).

**Benchmark:** `hnsw-cpp/benchmarks/benchmark_hnsw.py` compares HNSW vs FAISS when
dependencies installed. Output is measured locally only.

**Integration:** `api/retrieval/hnsw_store.py` wraps module as `VectorStore`;
`BruteForceHNSWVectorStore` fallback when extension not built.
`api/retrieval/factory.py` selects backend via `RETRIEVAL_BACKEND=hnsw`.

---

## 6. Document Ingestion API

**Service:** `api/ingestion/service.py` — `IngestionService.ingest_document()`

**Pipeline:** validate title → parse (txt/md/html) → chunk (sliding window) → embed →
vector store upsert.

**HTTP route:** `POST /api/v1/documents/upload` (`api/routes/documents.py`)
- Form fields: `tenant_id`, `title`, `document_type`, `source`, `file`
- Auth: `X-Tenant-Key` via `tenant_from_form()` → `resolve_tenant_context()`

**Batch path:** `ingestion/spark_ingest.py` — PySpark mapPartitions scaffold.

---

## 7. LangGraph Iterative Retrieval Pipeline

**Files:** `api/retrieval/pipeline.py`, `api/retrieval/state.py`

**State (`RAGState` TypedDict):**
- `query`, `rewritten_queries`, `retrieved_chunks`, `reranked_chunks`,
  `relevance_score`, `confidence_score`, `answer`, `citations`, `iteration_count`,
  `top_k`, `max_iterations`, `relevance_threshold`, `low_confidence`, `model`

**Nodes:**
- `rewrite_query`, `retrieve`, `assess_relevance`, `rerank`, `generate`

**Routing (`route_after_assessment`):**
- Poor relevance + iterations remaining → rewrite again
- Good relevance → rerank → generate
- Max iterations reached → generate with low-confidence flag

**Runner:** LangGraph `StateGraph` when `langgraph` installed; `_fallback_run` /
`run_until_generation` otherwise.

**Generation:** Real `GenerationService` (not placeholder strings).

---

## 8. RAGAS Evaluation Framework

**Files:**
- `api/evaluation/ragas_eval.py` — `RagasEvaluator`, `RagasEvaluationResult`
- `api/evaluation/metrics.py` — heuristic faithfulness, answer relevance, precision/recall
- `api/evaluation/testset.py` — sample evaluation examples (extend to 100+ documented)
- `api/evaluation/service.py` — `EvaluationService.run_experiment()`
- `api/experiments/mlflow_tracker.py` — optional MLflow logging
- `api/experiments/tracker.py` — in-memory + `CompositeExperimentTracker`
- `scripts/run_experiment.py` — CLI runner

**Metrics to track:**
- `ragas_faithfulness`, `ragas_answer_relevance`, `ragas_context_recall`,
  `ragas_context_precision`
- `mean_retrieval_latency_ms`, `mean_generation_latency_ms`

**Behavior:**
- If `ragas` installed: structured evaluation path (heuristic fallback when LLM judges
  not configured).
- If `ragas` not installed: graceful fallback or clear `ImportError` when fallback
  disabled.
- No fabricated scores.

**HTTP:** `POST /api/v1/experiments/run`, `GET /api/v1/experiments/runs`

---

## 9. PySpark Batch Ingestion

**Files:** `ingestion/spark_ingest.py`, `ingestion/README.md`

**Requirements:**
- Read JSON documents from local or S3-style path.
- Chunk via existing chunker.
- Embed via `EmbeddingProvider` abstraction.
- Prepare rows for PostgreSQL/Chroma bulk writes.
- Use `mapPartitions` pattern with model broadcast placeholder.
- Document `spark-submit` command.
- No fake performance claims.

---

## 10. Streaming API with SSE

**Route:** `POST /api/v1/query/stream` (`api/routes/query.py`)

**Requirements:**
- FastAPI `StreamingResponse`, `media_type=text/event-stream`
- Token events: `data: {"token": "...", "done": false}`
- Final event: `data: {"token": "", "done": true, "citations": [...], ...}`
- Token-by-token streaming from LLM provider on cache miss
- Cached responses replay tokens from stored answer
- Auth via `get_authenticated_tenant()` + `X-Tenant-Key`
- Non-streaming alternative: `POST /api/v1/query/generate`

**Legacy route:** `POST /api/v1/rag/query` remains functional with real generation.

---

## 11. Redis Query Caching

**Files:** `api/cache/redis_cache.py`, `CacheStatistics`

**Key format:** `{tenant_id}:{sha256(query)}`

**Requirements:**
- Configurable TTL (per-request `ttl` + `CACHE_TTL` env default)
- Cache lookup before generation
- Cache write after generation
- Statistics: hits, misses, writes, hit_rate
- Endpoint: `GET /api/v1/query/cache/stats`
- Graceful in-memory fallback when Redis unavailable
- Retry on transient read failures (`api/utils/retry.py`)

---

## 12. Prometheus Metrics and Grafana Dashboards

**Files:**
- `api/observability/metrics.py` — `MetricsRegistry`, `get_metrics()`
- `api/observability/middleware.py` — `PrometheusMiddleware`
- `api/app/main.py` — `GET /metrics`
- `monitoring/prometheus.yml`
- `monitoring/grafana/dashboards/rag-overview.json`

**Required metric names:**
- `request_count`
- `request_latency_seconds`
- `retrieval_latency_seconds`
- `generation_latency_seconds`
- `cache_hit_rate`
- `context_recall_score`
- `unanswered_query_rate`

**Behavior:** `/metrics` returns 503 when `prometheus-client` not installed.

---

## 13. Next.js TypeScript Frontend

**Location:** `frontend/`

**Pages:**
- `/` — navigation
- `/chat` — streaming chat (`ChatInterface.tsx`)
- `/documents` — upload (`DocumentUploader.tsx`)
- `/experiments` — experiment table (`ExperimentTable.tsx`)
- `/dashboard` — health, backends, cache stats
- `/admin` — admin scaffold

**Components:** `ChatInterface`, `CitationPanel`, `ExperimentTable`, `DocumentUploader`

**Requirements:**
- TypeScript + Next.js App Router
- Chat: live SSE to `/api/v1/query/stream`, `X-Tenant-Key` header support
- Documents: live upload to `/api/v1/documents/upload`
- Experiments: live calls to `/api/v1/experiments/run` and `/runs`
- Dashboard: `/health/ready`, `/api/v1/rag/health/details`, `/api/v1/query/cache/stats`
- `NEXT_PUBLIC_API_BASE` env (default `http://localhost:8000`)

---

## 14. Kubernetes Deployment

**Location:** `infrastructure/kubernetes/`

**Manifests:**
- `namespace.yaml`
- `api-deployment.yaml`, `worker-deployment.yaml`
- `postgres-statefulset.yaml`, `chromadb-statefulset.yaml`
- `redis-deployment.yaml`
- `prometheus-deployment.yaml`, `grafana-deployment.yaml`
- `hpa.yaml`
- PVCs for stateful services
- `README.md` with scaling strategy

**Constraint:** Manifests are scaffold; cluster validation not claimed as complete.

---

## 15. Comprehensive Pytest Suite

**Location:** `tests/`

**Required coverage areas:**
- Chunking (`tests/ingestion/`)
- Retrieval + vector stores + HNSW + factory (`tests/retrieval/`)
- Reranking (`tests/retrieval/test_reranker.py`)
- Generation + providers (`tests/generation/`)
- Embeddings factory (`tests/embeddings/`)
- Cache (`tests/cache/`)
- Streaming + API routes (`tests/api/`)
- Auth + quota + isolation (`tests/api/test_auth.py`)
- Persistence (`tests/services/test_query_persistence.py`)
- E2E query flow (`tests/api/test_e2e_query.py`)
- Evaluation + RAGAS (`tests/evaluation/`)
- Settings validation (`tests/config/`)
- Confidence routing (`tests/retrieval/test_confidence_routing.py`)
- Iterative pipeline (`tests/retrieval/test_iterative_pipeline.py`)

**Constraint:** Normal test execution must not require external services (Postgres,
Redis, OpenAI). Use `SKIP_DB=true`, in-memory stores, and mocks.

---

## 16. Interview Stories

Talking points for portfolio/interview discussions (derived from project goals):

1. **Multi-tenant RAG architecture** — Designed tenant-scoped vector stores, cache keys,
   and API key auth (`X-Tenant-Key`) with quota enforcement and isolation validation.

2. **Iterative retrieval with confidence routing** — Built a LangGraph-compatible pipeline
   that rewrites queries on poor retrieval and routes low-confidence answers when relevance
   thresholds are not met.

3. **Provider abstraction pattern** — Swappable embedding, LLM, and vector store backends
   (dummy/local for offline dev; OpenAI-compatible, FAISS, Chroma, HNSW for production paths).

4. **Production streaming + caching** — SSE token streaming with Redis-backed query cache,
   structured citation events, and Prometheus observability hooks.

5. **Evaluation-driven iteration** — Executable evaluation pipeline with experiment tracking
   and optional RAGAS/MLflow integration for measuring retrieval/generation quality over time.

6. **Performance engineering (HNSW)** — Custom C++ HNSW module with pybind11 bindings and
   benchmark scripts for local latency/recall tradeoff exploration (measured, not fabricated).

---

## 17. Final Acceptance Checklist

Every concrete requirement as a checklist item. Mark during audit as:
✅ FULLY IMPLEMENTED | ⚠️ PARTIALLY IMPLEMENTED | ❌ NOT IMPLEMENTED

### Foundation & Configuration
- [ ] Root README describes platform accurately without fake benchmarks
- [ ] `.env.example` documents all required/optional env vars
- [ ] `docker-compose.yml` runs Postgres, Redis, ChromaDB, MLflow, Prometheus, Grafana, Jaeger
- [ ] `api/config/settings.py` loads config from environment (no TODO placeholders)
- [ ] `ApplicationSettings.validate()` validates LLM and retrieval backend settings
- [ ] Structured JSON logging via `configure_logging()`

### Database
- [ ] `api/db/schema.sql` defines `tenants` with exact specified columns
- [ ] `api/db/schema.sql` defines `documents` with exact specified columns
- [ ] `api/db/schema.sql` defines `chunks` with `embedding_vector VECTOR(1536)`
- [ ] `api/db/schema.sql` defines `queries` with exact specified columns and JSONB default
- [ ] `api/db/schema.sql` defines `rag_experiments` with NOT NULL/UNIQUE constraints
- [ ] `api/db/init_db.py` applies schema
- [ ] `Tenant` ORM model maps tenants table
- [ ] `Document` ORM model maps documents table
- [ ] `Chunk` ORM model maps chunks table (including pgvector column)
- [ ] `TenantRepository` CRUD + `get_by_api_key_hash()`
- [ ] `DocumentRepository` persistence
- [ ] `QueryRepository.create_query_record()` persists query logs
- [ ] `QueryRepository.update_evaluation_scores()` persists faithfulness/relevance
- [ ] `QueryRepository.count_queries_today()` for quota enforcement
- [ ] `QueryRepository.list_queries_for_tenant()` for history API
- [ ] Ingestion persists documents/chunks to PostgreSQL (not just in-memory)

### Authentication & Multi-Tenant Security
- [ ] API key hashed with `hash_api_key()` (SHA-256)
- [ ] Tenant resolved from `X-Tenant-Key` header
- [ ] `TenantAuthMiddleware` enforces header when `AUTH_REQUIRED=true`
- [ ] `resolve_tenant_context()` validates tenant ID matches authenticated tenant
- [ ] Daily query quota enforced (`enforce_query_quota()` → HTTP 429)
- [ ] Auth tests cover missing key, valid key, isolation mismatch, quota exceeded

### Ingestion
- [ ] Parse txt, markdown, html (`parse_document_text()`)
- [ ] Validate title and content
- [ ] Sliding-window chunking (`chunk_text()`)
- [ ] `IngestionService.ingest_document()` indexes to vector store
- [ ] `POST /api/v1/documents/upload` accepts multipart upload
- [ ] PySpark batch job structure in `ingestion/spark_ingest.py`
- [ ] PySpark README documents spark-submit

### Embeddings
- [ ] `EmbeddingProvider` interface
- [ ] `DummyEmbeddingProvider` (deterministic offline)
- [ ] `SentenceTransformersProvider` with dimension validation
- [ ] `get_embedding_provider()` factory with env selection
- [ ] Batch embedding via `embed_documents()`

### Retrieval & Vector Stores
- [ ] `InMemoryVectorStore` with tenant isolation
- [ ] `FAISSVectorStore` (optional dep)
- [ ] `ChromaVectorStore` with metadata filters (optional dep)
- [ ] `HybridVectorStore` routes by filter presence
- [ ] `HNSWVectorStore` using `hnsw_cpp` module
- [ ] `BruteForceHNSWVectorStore` fallback without compiled extension
- [ ] `get_vector_store()` factory (`RETRIEVAL_BACKEND` env)
- [ ] `RetrievalService.index_chunks()` and `retrieve()`
- [ ] `CrossEncoderReranker` (optional dep)
- [ ] Tenant isolation tested in retrieval tests

### C++ HNSW Module
- [ ] `hnsw-cpp/CMakeLists.txt` builds pybind11 module
- [ ] `HNSWIndex.__init__(dim, max_elements, M, ef_construction)`
- [ ] `add_items(vectors, ids)`
- [ ] `search(query_vector, k, ef)`
- [ ] `save(path)` and `load(path)`
- [ ] README explains M, ef_construction, ef, recall/latency tradeoff
- [ ] `hnsw-cpp/benchmarks/benchmark_hnsw.py` (local measurement only)
- [ ] `scripts/benchmark_backends.py` compares backends locally

### LangGraph Iterative Pipeline
- [ ] `RAGState` TypedDict with all required fields
- [ ] Nodes: rewrite, retrieve, assess, rerank, generate
- [ ] LangGraph `StateGraph` when langgraph installed
- [ ] Fallback runner when langgraph not installed
- [ ] Conditional routing: rewrite / rerank / low-confidence
- [ ] `run_until_generation()` for streaming path
- [ ] Confidence scoring (`compute_confidence_score()`)
- [ ] Low-confidence answer prefix and routing
- [ ] Pipeline tests pass

### Generation
- [ ] `LLMProvider` interface with `generate()` and `stream_generate()`
- [ ] `LocalFallbackProvider` (offline context-grounded answers)
- [ ] `OpenAICompatibleProvider` (OpenAI-compatible chat completions + streaming)
- [ ] `DummyLLMProvider` for deterministic tests
- [ ] `get_llm_provider()` factory (`LLM_PROVIDER` env)
- [ ] `GenerationService.generate_answer()` returns `GenerationResponse`
- [ ] Structured citations in `GenerationResponse.citations`
- [ ] `GenerationService.stream_answer()` for SSE token streaming
- [ ] No placeholder "not implemented" answers in production routes

### RAG Orchestration & API Routes
- [ ] `RAGService.retrieve_context()` runs full pipeline
- [ ] `POST /api/v1/rag/query` returns contexts + generated answer + confidence
- [ ] `GET /api/v1/rag/config` returns settings
- [ ] `GET /api/v1/rag/health/details` reports backends
- [ ] `POST /api/v1/query/generate` non-streaming with cache
- [ ] `POST /api/v1/query/stream` SSE streaming
- [ ] `GET /api/v1/query/cache/stats`
- [ ] `GET /api/v1/query/history` lists persisted queries
- [ ] Query persistence wired on generate/stream/rag routes

### Redis Caching
- [ ] Cache key `{tenant_id}:{sha256(query)}`
- [ ] Configurable TTL
- [ ] Lookup before generation
- [ ] Write after generation
- [ ] `CacheStatistics` with hits/misses/writes/hit_rate
- [ ] In-memory fallback when Redis unavailable
- [ ] Cache tests pass

### SSE Streaming
- [ ] `StreamingResponse` with `text/event-stream`
- [ ] Token-by-token events with `done: false`
- [ ] Final event with citations and `done: true`
- [ ] Cached response streaming support
- [ ] Streaming tests pass

### RAGAS & Evaluation
- [ ] `RagasEvaluator` with heuristic fallback
- [ ] Tracks all six metric fields in `RagasEvaluationResult`
- [ ] Sample test set in `get_sample_testset()`
- [ ] Documentation for extending to 100+ pairs
- [ ] `EvaluationService.evaluate_examples()` runs pipeline on test set
- [ ] `EvaluationService.run_experiment()` logs metrics to tracker
- [ ] Optional MLflow via `MLflowTracker`
- [ ] `POST /api/v1/experiments/run` HTTP endpoint
- [ ] `GET /api/v1/experiments/runs` lists runs
- [ ] `scripts/run_experiment.py` CLI
- [ ] No fabricated evaluation scores
- [ ] `rag_experiments` table persisted from experiment runs

### Prometheus & Grafana
- [ ] All seven required metric names registered
- [ ] `PrometheusMiddleware` records request metrics
- [ ] `GET /metrics` endpoint (503 without prometheus_client)
- [ ] `monitoring/prometheus.yml` config
- [ ] Grafana dashboard JSON scaffold

### Frontend
- [ ] Next.js TypeScript project with package.json
- [ ] Chat page streams from live API
- [ ] Chat sends `X-Tenant-Key` when provided
- [ ] Citation panel renders final SSE citations
- [ ] Documents page uploads to live API
- [ ] Experiments page runs and lists experiments
- [ ] Dashboard shows readiness, backends, cache stats
- [ ] Admin page exists (scaffold acceptable)

### Kubernetes
- [ ] All listed manifest files present
- [ ] PVCs for stateful services
- [ ] HPA scaffold for API/worker
- [ ] README documents scaling strategy
- [ ] Not claimed as production-validated

### Production Hardening
- [ ] `GET /health` liveness
- [ ] `GET /health/ready` readiness with dependency checks
- [ ] Global exception handler returns 500 JSON
- [ ] Retry logic for transient cache failures
- [ ] `SKIP_DB` flag for test/offline mode

### Testing
- [ ] 80+ pytest tests
- [ ] Tests pass without external services by default
- [ ] Auth integration tests
- [ ] Persistence tests (mocked DB)
- [ ] E2E upload + query test
- [ ] CI workflow runs pytest (`.github/workflows/ci.yml`)

### Documentation
- [ ] `README.md` accurate feature list
- [ ] `docs/architecture.md`
- [ ] `docs/api_reference.md`
- [ ] `docs/deployment.md`
- [ ] `docs/project_scope.md`
- [ ] `docs/project5_specification.md` (this document)

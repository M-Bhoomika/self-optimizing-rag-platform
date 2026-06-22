# Self-Optimizing RAG Platform

A modular backend for document ingestion, vector retrieval, answer generation,
iterative retrieval orchestration, and evaluation. The codebase uses
interface-driven providers so storage backends and model integrations can be
swapped without rewriting callers.

**Retrieval-Augmented Generation (RAG)** grounds language model answers in your
own documents. A RAG pipeline retrieves relevant content first, then uses that
context to generate a response.

## Key Features

### Document Ingestion
- Validation, parsing (txt/markdown/html), and sliding-window chunking
- Vector indexing plus PostgreSQL persistence for documents and chunk embeddings (`api/services/document_persistence.py`)
- Upload API: `POST /api/v1/documents/upload` with document quota enforcement
- PySpark batch ingestion scaffold (`ingestion/spark_ingest.py`)

### Retrieval
- Pluggable vector stores: in-memory, FAISS, ChromaDB, hybrid, HNSW, and pgvector (`RETRIEVAL_BACKEND`)
- Iterative retrieval pipeline: query rewrite → retrieve → assess → rerank → generate
- Optional cross-encoder reranking
- Confidence scoring and low-confidence answer routing
- C++ HNSW module with pybind11 bindings (`hnsw-cpp/`)

### Generation
- LLM provider abstraction with local fallback and OpenAI-compatible provider
- Structured `GenerationResponse` with citations, confidence score, and low-confidence routing
- Streaming query API (SSE) and non-streaming generation endpoint
- Provider selection via `LLM_PROVIDER` environment variable

### Evaluation & Experimentation
- Heuristic metrics and optional RAGAS integration
- In-memory experiment tracking with optional MLflow and PostgreSQL `rag_experiments` persistence
- HTTP and CLI experiment runners (`/api/v1/experiments/run`, `scripts/run_experiment.py`)

### Platform
- Multi-tenant data model, repositories, FastAPI routes
- API key auth via `X-Tenant-Key`, query/document quotas, tenant isolation
- Redis query cache with key `{tenant_id}:{query_hash}`, configurable TTL, and statistics
- Background worker queue for async ingest/eval tasks (`scripts/run_worker.py`)
- Prometheus metrics (`/metrics` when `prometheus-client` is installed)
- Optional OpenTelemetry tracing to Jaeger (`OTEL_TRACING_ENABLED` or `OTEL_EXPORTER_OTLP_ENDPOINT`)
- Next.js frontend wired to live APIs (chat, upload, experiments, dashboard, admin)
- Docker, Compose, and Kubernetes deployment scaffolds

## Architecture

```
Client (Next.js)
  |
FastAPI API Layer          (api/app, api/routes)
  |
RAG Orchestration          (api/rag, iterative pipeline)
  |
+-----------------------------+
| Retrieval | Generation    |
+-----------------------------+
  |
Vector Store + Embeddings  (api/retrieval, api/embeddings, hnsw-cpp)
  |
Repositories               (api/repositories)
  |
PostgreSQL + pgvector      (api/db, api/models)
```

Supporting services (Redis, ChromaDB, MLflow, Prometheus, Grafana, Jaeger) run
via Docker Compose for local development.

## Tech Stack

**Backend:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.x  
**Data:** PostgreSQL, pgvector  
**Retrieval (optional):** NumPy, FAISS, ChromaDB, sentence-transformers, hnsw_cpp  
**Orchestration (optional):** LangGraph  
**Evaluation (optional):** ragas, mlflow  
**Observability (optional):** prometheus-client, OpenTelemetry  
**Batch (optional):** PySpark  
**Frontend:** Next.js, TypeScript, React  
**Infrastructure:** Docker, Docker Compose, Kubernetes manifests, Prometheus/Grafana scaffolds  
**Testing:** pytest

## Repository Structure

```
.github/workflows/   CI pipeline
api/
  app/             FastAPI app, middleware, /metrics
  cache/           Redis cache wrapper
  config/          Settings models
  db/              Schema and initialization
  embeddings/      Embedding providers
  evaluation/      Metrics, RAGAS integration, test set
  experiments/     In-memory + MLflow experiment tracking
  generation/      Prompts, LLM providers, generation service
  ingestion/       Parsing, chunking, ingestion workflow
  models/          SQLAlchemy ORM models
  observability/   Prometheus metrics, tracing, middleware
  rag/             RAG orchestration
  repositories/    Persistence repositories
  retrieval/       Vector stores, pipeline, reranker
  routes/          REST, SSE, admin, and document routes
  services/        Query, document, and experiment persistence
  worker/          Redis-backed background task queue
docker/            API and worker Dockerfiles
docs/              Architecture, API, deployment, scope, specification
frontend/          Next.js UI (chat, documents, experiments, dashboard, admin)
hnsw-cpp/          C++ HNSW index + pybind11 bindings
ingestion/         PySpark batch ingestion job
infrastructure/    Compose-related config, Kubernetes manifests
monitoring/        Prometheus + Grafana dashboard scaffold
scripts/           Startup scripts, worker, demo seed, experiment runner
tests/             pytest suites (generation, cache, streaming, embeddings, retrieval, api)
```

## Running Locally

```bash
docker compose up -d
pip install -r requirements.txt
python -m api.db.init_db
uvicorn api.app.main:app --reload
python -m pytest tests/ -q
```

Optional integrations:

```bash
pip install prometheus-client redis langgraph ragas mlflow faiss-cpu chromadb sentence-transformers pyspark opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp opentelemetry-instrumentation-fastapi
```

Background worker (uses `REDIS_URL` or in-memory queue fallback):

```bash
python scripts/run_worker.py
```

Environment variables are defined in `.env.example` (all variables consumed by
`api/config/settings.py`). Copy it to `.env` and adjust for your environment.

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | local Postgres URL | SQLAlchemy database URL |
| `DB_POOL_SIZE` | `5` | Connection pool size |
| `SKIP_DB` | unset | Set `true` in tests to skip PostgreSQL writes |
| `AUTH_REQUIRED` | `false` | Require `X-Tenant-Key` on API routes |
| `AUTH_HEADER_NAME` | `X-Tenant-Key` | API key header name |
| `RETRIEVAL_BACKEND` | `memory` | `memory`, `faiss`, `chroma`, `hybrid`, `hnsw`, `pgvector` |
| `RETRIEVAL_TOP_K` | `5` | Default retrieval top-k |
| `RETRIEVAL_SIMILARITY_THRESHOLD` | `0.0` | Similarity threshold |
| `EMBEDDING_PROVIDER` | `dummy` | `dummy` or `sentence-transformers` |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformers model |
| `EMBEDDING_DIMENSION` | `1536` | Expected embedding dimension |
| `REDIS_URL` | — | Redis URL; in-memory fallback when unset |
| `CACHE_TTL` | `300` | Default cache TTL in seconds |
| `LLM_PROVIDER` | `local` | `local`, `openai`, or `openai-compatible` |
| `OPENAI_API_KEY` | — | Required when `LLM_PROVIDER=openai` |
| `OPENAI_BASE_URL` | OpenAI API URL | OpenAI-compatible base URL |
| `OPENAI_MODEL` | `gpt-4o-mini` | Chat model name |
| `ENABLE_EVALUATION` | `true` | Persist heuristic scores on query logs |
| `FAITHFULNESS_THRESHOLD` | `0.7` | Evaluation threshold |
| `LOG_LEVEL` | `INFO` | Logging level |
| `MLFLOW_TRACKING_URI` | — | Optional MLflow server URL |
| `OTEL_TRACING_ENABLED` | unset | Set `true` to enable Jaeger/OTLP tracing |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | — | OTLP endpoint (e.g. `http://localhost:4317`) |

Helper scripts: `scripts/start_local.sh` / `scripts/start_local.ps1`

Benchmark results are **not** checked into the repository. Generate locally:

```bash
python scripts/benchmark_backends.py --output monitoring/benchmark_results.json
python hnsw-cpp/benchmarks/benchmark_hnsw.py
```

See `monitoring/benchmark_results.template.json` for the expected output shape.

Docker Compose runs postgres, redis, chromadb, api, worker, frontend, mlflow, prometheus, grafana, and jaeger — see [docs/docker_compose_services.md](docs/docker_compose_services.md).

## Documentation

- [Architecture](docs/architecture.md)
- [API Reference](docs/api_reference.md)
- [Deployment](docs/deployment.md)
- [Project Scope](docs/project_scope.md)
- [Project 5 Specification](docs/project5_specification.md)

## Design Principles

- Multi-tenant architecture
- Interface-driven providers (embeddings, retrieval, generation)
- Repository pattern for persistence
- Graceful degradation when optional dependencies are missing
- Separation of concerns across service modules

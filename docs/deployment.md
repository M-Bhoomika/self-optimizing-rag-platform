# Deployment

Guide for deploying the Self-Optimizing RAG Platform using Docker and the
local monitoring stack.

## Prerequisites

- Docker and Docker Compose
- Python 3.12+ (for local development outside containers)
- Copy `.env.example` to `.env` and adjust values as needed

## Docker Deployment

### Build images

From the project root:

```bash
docker build -f docker/api.Dockerfile -t rag-platform-api:latest .
docker build -f docker/worker.Dockerfile -t rag-platform-worker:latest .
```

### API service

The API image runs Uvicorn on port 8000:

```bash
docker run --rm -p 8000:8000 \
  --env-file .env \
  rag-platform-api:latest
```

Health check endpoint: `GET /health`

### Worker service

The worker image is prepared for background task processing (ingestion,
embedding, evaluation jobs). The default command runs the demo seed script in
dry-run mode. Override the command in your orchestrator once a task-queue
consumer is implemented:

```bash
docker run --rm \
  --env-file .env \
  rag-platform-worker:latest \
  python scripts/seed_demo_data.py --dry-run
```

### Infrastructure stack

Start supporting services (Postgres, Redis, ChromaDB, MLflow, Prometheus,
Grafana, Jaeger):

```bash
docker compose up -d
```

Or use the helper scripts:

```bash
./scripts/start_local.sh infra        # Linux/macOS
.\scripts\start_local.ps1 infra       # Windows
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `POSTGRES_USER` | PostgreSQL username | `rag_user` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `rag_password` |
| `POSTGRES_DB` | PostgreSQL database name | `rag_platform` |
| `DATABASE_URL` | SQLAlchemy connection URL | `postgresql://rag_user:rag_password@postgres:5432/rag_platform` |
| `REDIS_URL` | Redis connection URL | `redis://redis:6379/0` |
| `CACHE_TTL` | Default query cache TTL (seconds) | `300` |
| `LLM_PROVIDER` | LLM provider (`local` or `openai`) | `local` |
| `OPENAI_API_KEY` | OpenAI API key (required for `openai` provider) | — |
| `OPENAI_BASE_URL` | OpenAI-compatible API base URL | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | Chat model name | `gpt-4o-mini` |
| `EMBEDDING_PROVIDER` | Embedding provider (`dummy` or `sentence-transformers`) | `dummy` |
| `EMBEDDING_MODEL` | Sentence-transformers model name | `all-MiniLM-L6-v2` |
| `EMBEDDING_DIMENSION` | Expected embedding dimension | `1536` |
| `CHROMA_HOST` | ChromaDB hostname | `chromadb` |
| `CHROMA_PORT` | ChromaDB port | `8000` |
| `MLFLOW_TRACKING_URI` | MLflow tracking server | `http://mlflow:5000` |

## Monitoring Stack

### Prometheus

- Metrics module: `api/observability/metrics.py`
- Middleware: `api/observability/middleware.py`
- Endpoint: `GET /metrics` (returns 503 if `prometheus-client` is not installed)

Metric names:

- `request_count`
- `request_latency_seconds`
- `retrieval_latency_seconds`
- `generation_latency_seconds`
- `cache_hit_rate`
- `context_recall_score`
- `unanswered_query_rate`

Config: `monitoring/prometheus.yml` (Compose currently mounts `infrastructure/prometheus/prometheus.yml`).

### Grafana

Dashboard: `monitoring/grafana/dashboards/rag-overview.json` (import via Grafana UI on port 3001).

### Jaeger

UI at `http://localhost:16686` when Compose is running. Enable application
tracing with `OTEL_TRACING_ENABLED=true` or by setting
`OTEL_EXPORTER_OTLP_ENDPOINT` (default OTLP gRPC target when only the flag is
set: `http://localhost:4317`). Instrumentation lives in
`api/observability/tracing.py` and covers FastAPI requests plus retrieval and
generation pipeline spans.

## Kubernetes

Manifests: `infrastructure/kubernetes/` — see README in that folder for apply order.

## Frontend

```bash
cd frontend && npm install && npm run dev
```

Set `NEXT_PUBLIC_API_BASE=http://localhost:8000` for streaming chat.

## Scaling Strategy

### API tier

- Run multiple API container replicas behind a load balancer.
- API processes are stateless; in-memory vector stores are suitable for
  development only. Production deployments should use persistent vector backends
  (pgvector, ChromaDB, FAISS with shared storage).
- Scale horizontally based on request latency (`request_latency` p95) and CPU.

### Worker tier

- Scale worker replicas independently based on queue depth.
- Workers handle ingestion, embedding, and evaluation jobs asynchronously.
- Each worker connects to shared Postgres, Redis, and vector store services.

### Data tier

- Postgres: vertical scaling or read replicas for query-heavy workloads.
- Redis: used for caching and task queues; scale with Redis Cluster if needed.
- ChromaDB: scale with dedicated vector search nodes for large corpora.

## Local Development Workflow

```bash
# 1. Start infrastructure
./scripts/start_local.sh infra

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialize database schema
python -m api.db.init_db

# 4. Start API
./scripts/start_local.sh api

# 5. Run tests
./scripts/start_local.sh test

# 6. Generate demo data
./scripts/start_local.sh seed
```

## Documentation

- [Architecture](architecture.md)
- [API Reference](api_reference.md)
- [Deployment](deployment.md)
- [Project Scope](project_scope.md)

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`) runs a lint placeholder,
the pytest suite, and Docker build verification on push and pull request.

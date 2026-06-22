# Docker Compose Services

| Service | Container | Host port | Purpose |
|---------|-----------|-----------|---------|
| postgres | rag-postgres | 5432 | PostgreSQL + pgvector |
| redis | rag-redis | 6379 | Cache + worker queue |
| chromadb | rag-chromadb | 8001 | Vector store (HTTP 8000 in container) |
| api | rag-api | 8000 | FastAPI application |
| worker | rag-worker | — | Background ingest/eval consumer |
| frontend | rag-frontend | 3000 | Next.js UI |
| mlflow | rag-mlflow | 5000 | Experiment tracking UI |
| prometheus | rag-prometheus | 9090 | Metrics scrape |
| grafana | rag-grafana | 3001 | Dashboards (UI port 3000 in container) |
| jaeger | rag-jaeger | 16686, 4317, 4318 | Tracing UI + OTLP |

Start all services:

```bash
docker compose up -d
```

Environment defaults are documented in `.env.example`.

# API Reference

Base URL (local development): `http://localhost:8000`

Most endpoints return JSON. Streaming query responses use Server-Sent Events (SSE).

## Authentication

When `AUTH_REQUIRED=true`, protected `/api/*` routes require the tenant API key
header (default name: `X-Tenant-Key`, configurable via `AUTH_HEADER_NAME`).

Tenant resolution and quota enforcement are implemented in `api/app/auth.py`.
The authenticated tenant id must match the `tenant_id` supplied in request
bodies or form fields.

## Health

### `GET /health`

Basic liveness check.

**Response**

```json
{
  "status": "ok",
  "service": "Self-Optimizing RAG Platform",
  "version": "0.1.0"
}
```

---

## RAG

Prefix: `/api/v1/rag`

### `POST /api/v1/rag/query`

Run the full iterative RAG pipeline (rewrite → retrieve → assess → rerank →
generate) and return retrieved contexts plus a generated answer.

**Request body**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `tenant_id` | string | yes | — | Tenant identifier |
| `query` | string | yes | — | User query text |
| `top_k` | integer | no | `5` | Number of chunks to retrieve |

**Example request**

```json
{
  "tenant_id": "tenant-1",
  "query": "How does vector search work?",
  "top_k": 5
}
```

**Response**

| Field | Type | Description |
|-------|------|-------------|
| `query` | string | Echo of the input query |
| `contexts` | array | Retrieved context chunks |
| `contexts[].chunk_id` | string | Chunk identifier |
| `contexts[].document_id` | string | Source document identifier |
| `contexts[].chunk_text` | string | Chunk content |
| `contexts[].score` | float | Similarity score |
| `contexts[].metadata` | object | Chunk metadata |
| `generated_answer` | string | LLM-generated answer |
| `retrieved_count` | integer | Number of contexts returned |
| `confidence_score` | float | Combined retrieval + overlap confidence |
| `low_confidence` | boolean | True when answer quality is below threshold |
| `model` | string | LLM provider model name |
| `citations` | array | Source chunks cited in the answer |

**Example response**

```json
{
  "query": "How does vector search work?",
  "contexts": [
    {
      "chunk_id": "doc-1:0",
      "document_id": "doc-1",
      "chunk_text": "Vector search finds similar embeddings.",
      "score": 0.87,
      "metadata": {}
    }
  ],
  "generated_answer": "Based on the provided context, Vector search finds similar embeddings.",
  "retrieved_count": 1,
  "confidence_score": 0.72,
  "low_confidence": false,
  "model": "local-fallback",
  "citations": [
    {
      "chunk_id": "doc-1:0",
      "document_id": "doc-1",
      "chunk_text": "Vector search finds similar embeddings.",
      "score": 0.87
    }
  ]
}
```

---

### `GET /api/v1/rag/config`

Return the current application configuration.

**Response**

Nested JSON object with sections: `database`, `retrieval`, `embedding`, `evaluation`.

**Example response (abbreviated)**

```json
{
  "database": {
    "database_url": "postgresql://rag_user:rag_password@localhost:5432/rag_platform",
    "pool_size": 5
  },
  "retrieval": {
    "top_k": 5,
    "similarity_threshold": 0.0
  },
  "embedding": {
    "model_name": "dummy",
    "embedding_dimension": 1536
  },
  "evaluation": {
    "enable_evaluation": true,
    "faithfulness_threshold": 0.7
  }
}
```

---

### `GET /api/v1/rag/health/details`

Return service health details including backend identifiers.

**Response**

```json
{
  "service": "Self-Optimizing RAG Platform",
  "version": "0.1.0",
  "retrieval_backend": "in-memory",
  "embedding_backend": "dummy"
}
```

---

## Query (Streaming & Generation)

Prefix: `/api/v1/query`

### `POST /api/v1/query/stream`

Stream an iterative retrieval + generation result over Server-Sent Events (SSE).

**Request body**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `tenant_id` | string | yes | — | Tenant identifier |
| `query` | string | yes | — | User query text |
| `top_k` | integer | no | `5` | Number of chunks to retrieve |
| `use_cache` | boolean | no | `true` | Enable Redis/in-memory cache |
| `ttl` | integer | no | `300` | Cache TTL in seconds |

**SSE events**

Token events during generation:

```
data: {"token": "Based", "done": false}
data: {"token": "on", "done": false}
```

Final event with citations and metadata:

```
data: {"token": "", "done": true, "citations": [...], "confidence_score": 0.72, "low_confidence": false, "model": "local-fallback", "cached": false}
```

Cached responses set `"cached": true` in the final event.

---

### `POST /api/v1/query/generate`

Non-streaming generation using the full RAG pipeline with optional caching.

**Response**

```json
{
  "query": "What is RAG?",
  "answer": "Based on the provided context, ...",
  "citations": [{"chunk_id": "...", "document_id": "...", "score": 0.9}],
  "confidence_score": 0.65,
  "low_confidence": false,
  "model": "local-fallback",
  "cached": false
}
```

---

### `GET /api/v1/query/cache/stats`

Return in-process cache statistics.

**Response**

```json
{
  "hits": 3,
  "misses": 2,
  "writes": 2,
  "total_requests": 5,
  "hit_rate": 0.6
}
```

---

## Metrics

### `GET /metrics`

Prometheus exposition endpoint. Returns `503` when `prometheus-client` is not installed.

Expected metric names when enabled:

- `request_count`
- `request_latency_seconds`
- `retrieval_latency_seconds`
- `generation_latency_seconds`
- `cache_hit_rate`
- `context_recall_score`
- `unanswered_query_rate`

---

## Admin

Prefix: `/api/v1/admin`

### `GET /api/v1/admin/status`

Platform status including retrieval backend, cache backend, worker queue depth,
and whether `SKIP_DB` is active.

### `GET /api/v1/admin/config`

Sanitized application configuration from `ApplicationSettings.to_dict()`.

### `GET /api/v1/admin/tenants`

List tenants from PostgreSQL when available, otherwise in-memory test tenants.

### `GET /api/v1/admin/tenants/{tenant_id}/stats`

Document count, query count, and recent query history for a tenant.

### `GET /api/v1/admin/experiments`

List experiment rows persisted to the `rag_experiments` table.

---

## Interactive Documentation

When the API is running locally, FastAPI auto-generates interactive docs:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

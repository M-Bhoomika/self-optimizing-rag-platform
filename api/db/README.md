# Database

PostgreSQL schema for the Self-Optimizing RAG Platform. The schema lives in
`schema.sql` and relies on two extensions: `pgcrypto` (for `gen_random_uuid()`)
and `vector` (pgvector, for embedding columns).

## Tables

- **tenants** — Top-level isolation boundary. Stores `name`, `api_key_hash`,
  `document_quota`, and `query_quota_per_day`.
- **documents** — Source documents scoped to a tenant. Tracks `title`, `content`,
  `s3_key`, `document_type`, `ingested_at`, `embedding_model`, and `chunk_count`.
- **chunks** — Retrievable document segments. Each row holds `chunk_text`,
  `chunk_index`, an optional `embedding_vector` (`VECTOR(1536)`), and links to
  both `document_id` and `tenant_id`.
- **queries** — Query log for analytics. Stores `query_text`, `answer_text`,
  `retrieved_chunk_ids` (JSONB), evaluation scores, `latency_ms`, `model_version`,
  and a `cached` flag.
- **rag_experiments** — Tracked experiment configurations linked to MLflow via
  `mlflow_run_id`. Holds `config`, `ragas_scores`, `deployed_at`, and
  `traffic_percentage`.

## Why pgvector together with ChromaDB

PostgreSQL with pgvector is the **system of record**: it stores canonical
relational data with strong consistency, foreign keys, and tenant isolation, and
can run vector similarity queries alongside relational/JSONB data.

ChromaDB complements Postgres as a **dedicated vector search layer** optimized
for approximate nearest-neighbor retrieval with metadata filtering. Application
code can route filter-free queries to FAISS/Chroma and keep Postgres as the
durable source of truth that vector indexes can be rebuilt from.

## Dependencies

Database driver dependencies are listed in the root `requirements.txt`. The
`api/db/requirements.txt` file retains the minimal DB-only subset for
standalone schema initialization.

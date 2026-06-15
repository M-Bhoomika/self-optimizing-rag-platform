# Database

PostgreSQL schema for the Self-Optimizing RAG Platform. The schema lives in
`schema.sql` and relies on two extensions: `pgcrypto` (for `gen_random_uuid()`)
and `vector` (pgvector, for embedding columns).

## Tables

- **tenants** — Top-level isolation boundary for the multi-tenant architecture.
  Stores tenant identity (`name`, `slug`) and per-tenant `settings`. Every other
  table references a tenant.
- **documents** — Source documents ingested into the platform. Tracks origin
  (`source_uri`), `document_type`, processing `status`, and arbitrary
  `metadata`, scoped to a tenant.
- **chunks** — Document content split into retrievable chunks. Each chunk holds
  its `content`, an optional `embedding` (`VECTOR(1536)`), and `metadata`, and
  links back to both its `document_id` and `tenant_id`.
- **queries** — User queries issued against the platform. Stores the
  `query_text`, the generated `response_text`, latency, optional link to the
  `rag_experiment` that served it, and `metadata` for analytics.
- **rag_experiments** — RAG configurations/experiments used for automated
  evaluation and experiment tracking. Captures `config`, recorded `metrics`,
  lifecycle `status`, and `deployed_at` when an experiment is promoted.

## Why pgvector together with ChromaDB

PostgreSQL with pgvector is the **system of record**: it stores the canonical
relational data (tenants, documents, chunks, queries, experiments) with strong
consistency, foreign keys, and tenant isolation, and can run vector similarity
queries directly alongside that relational/JSONB data. This keeps metadata
filtering and embeddings in one transactional store.

ChromaDB is used as a **dedicated, high-throughput vector search layer**
optimized for approximate nearest-neighbor retrieval at scale. It complements
pgvector by serving fast similarity lookups during the iterative retrieval loop,
while Postgres remains the durable source of truth that ChromaDB can be rebuilt
from. Using both lets the platform combine reliable relational guarantees with
specialized, performant vector retrieval.

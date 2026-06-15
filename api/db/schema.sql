-- Self-Optimizing RAG Platform — database schema
--
-- Extensions:
--   pgcrypto  -> gen_random_uuid() for UUID primary keys
--   vector    -> pgvector type for embedding similarity search

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

-- ---------------------------------------------------------------------------
-- tenants
-- Top-level isolation boundary for the multi-tenant architecture.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tenants (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                  TEXT NOT NULL,
    api_key_hash          TEXT,
    document_quota        INTEGER,
    query_quota_per_day   INTEGER,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- documents
-- Source documents ingested into the platform, scoped to a tenant.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS documents (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id         UUID NOT NULL REFERENCES tenants (id) ON DELETE CASCADE,
    title             TEXT,
    content           TEXT,
    s3_key            TEXT,
    document_type     TEXT,
    ingested_at       TIMESTAMPTZ,
    embedding_model   TEXT,
    chunk_count       INTEGER,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- chunks
-- Chunked, embedded pieces of a document used for retrieval.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS chunks (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id       UUID NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    tenant_id         UUID NOT NULL REFERENCES tenants (id) ON DELETE CASCADE,
    chunk_text        TEXT NOT NULL,
    chunk_index       INTEGER NOT NULL DEFAULT 0,
    embedding_vector  VECTOR(1536),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- queries
-- User queries issued against the platform, scoped to a tenant.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS queries (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL REFERENCES tenants (id) ON DELETE CASCADE,
    query_text              TEXT NOT NULL,
    answer_text             TEXT,
    retrieved_chunk_ids     JSONB NOT NULL DEFAULT '[]'::jsonb,
    faithfulness_score      DOUBLE PRECISION,
    answer_relevance_score  DOUBLE PRECISION,
    latency_ms              INTEGER,
    model_version           TEXT,
    cached                  BOOLEAN NOT NULL DEFAULT false,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- rag_experiments
-- Tracked RAG configurations/experiments and their deployment state.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rag_experiments (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mlflow_run_id        TEXT NOT NULL UNIQUE,
    config               JSONB NOT NULL,
    ragas_scores         JSONB NOT NULL,
    deployed_at          TIMESTAMPTZ,
    traffic_percentage   DOUBLE PRECISION NOT NULL DEFAULT 0,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Indexes
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_documents_tenant_id        ON documents (tenant_id);
CREATE INDEX IF NOT EXISTS idx_documents_document_type     ON documents (document_type);

CREATE INDEX IF NOT EXISTS idx_chunks_tenant_id            ON chunks (tenant_id);
CREATE INDEX IF NOT EXISTS idx_chunks_document_id          ON chunks (document_id);

CREATE INDEX IF NOT EXISTS idx_queries_tenant_id           ON queries (tenant_id);
CREATE INDEX IF NOT EXISTS idx_queries_created_at          ON queries (created_at);

CREATE INDEX IF NOT EXISTS idx_rag_experiments_deployed_at ON rag_experiments (deployed_at);

# Tenant Isolation for Vector Stores

## ChromaDB (`api/retrieval/chroma_store.py`)

- Every upsert stores `tenant_id` in chunk metadata.
- `similarity_search` always applies a metadata filter: `{"tenant_id": {"$eq": tenant_id}}`.
- Cross-tenant reads are rejected at the query layer even when collections are shared.

## pgvector / PostgreSQL (`api/retrieval/pgvector_store.py`, `api/models/chunk.py`)

- The `chunks` table includes a `tenant_id` foreign key.
- Vector search SQL includes `WHERE tenant_id = :tenant_id`.
- Repository writes always set both `document_id` and `tenant_id`.

## In-memory / FAISS / HNSW adapters

- Stores partition data by `tenant_id` keys or metadata.
- See `tests/retrieval/test_vector_stores.py` and `tests/retrieval/test_retrieval_service.py`.

## Operational note

Tenant isolation in vector stores complements API auth (`X-Tenant-Key`) but does not
replace it. Always authenticate callers before accepting uploads or queries.

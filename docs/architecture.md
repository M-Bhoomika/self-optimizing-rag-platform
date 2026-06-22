# Architecture



System architecture for the Self-Optimizing RAG Platform.



## System Overview



```

Client (Next.js)

  |

FastAPI API Layer          (api/app, api/routes)

  |

Iterative RAG Pipeline     (api/retrieval/pipeline.py)

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



Supporting infrastructure: Redis (query cache), ChromaDB, MLflow, Prometheus,

Grafana, Jaeger via Docker Compose.



## Ingestion Flow



1. Document arrives with metadata (`tenant_id`, title, type, source).

2. Validate → parse → chunk (`api/ingestion`).

3. Embed via `EmbeddingProvider` (`api/embeddings`).

4. Index in vector store; persist documents and chunks via repositories when PostgreSQL is enabled.



Batch path: `ingestion/spark_ingest.py` reads JSON (local or S3-style path),

chunks per partition, embeds, and prepares bulk-write rows.



## Iterative Retrieval Flow



Implemented in `api/retrieval/pipeline.py` with LangGraph when installed, or a

built-in fallback runner otherwise.



```

rewrite_query -> retrieve -> assess_relevance

  | poor + iterations left -> rewrite_query

  | good -> rerank -> generate

  | max iterations -> generate (low-confidence)

```



State fields (`RAGState`): query, rewritten_queries, retrieved_chunks,

reranked_chunks, relevance_score, confidence_score, answer, citations,

iteration_count, low_confidence, model.



## Generation Flow



1. Context + question → `build_rag_prompt` (`api/generation/prompts.py`).

2. `LLMProvider.generate` or `LLMProvider.stream_generate`.

3. Providers:

   - `LocalFallbackProvider` — offline, context-grounded answers (default).

   - `OpenAICompatibleProvider` — OpenAI-compatible chat completions API.

   - `DummyLLMProvider` — deterministic output for tests.

4. `GenerationService.generate_answer` returns `GenerationResponse` with

   citations, confidence score, and low-confidence flag.

5. Confidence combines retrieval relevance with answer-context overlap.



## Query Cache



`api/cache/redis_cache.py` implements tenant-scoped caching:



- Key format: `{tenant_id}:{sha256(query)}`

- Lookup before generation; write after generation

- Configurable TTL per request or via `CACHE_TTL`

- In-memory fallback when Redis is unavailable

- `CacheStatistics` tracks hits, misses, writes, and hit rate



## Streaming API



`/api/v1/query/stream` uses FastAPI `StreamingResponse` with

`text/event-stream`:



1. Cache lookup (optional via `use_cache`).

2. On cache hit: stream cached answer tokens, then final citation event.

3. On cache miss: run retrieval pipeline, stream generation tokens from the

   LLM provider, cache structured payload, emit final event with citations.



## Embedding Providers



`api/embeddings/factory.py` selects providers via `EMBEDDING_PROVIDER`:



- `DummyEmbeddingProvider` — deterministic offline embeddings (default).

- `SentenceTransformersProvider` — local sentence-transformers models with

  batch embedding and dimension validation.



## Evaluation Flow



- Heuristic metrics in `api/evaluation/metrics.py`.

- Sample test set in `api/evaluation/testset.py` (extend to 100+ pairs).

- RAGAS integration in `api/evaluation/ragas_eval.py` (requires `ragas` package; heuristic fallback built-in).

- Experiment tracking: in-memory (`ExperimentTracker`), optional MLflow
  (`MLflowTracker`), and PostgreSQL `rag_experiments` persistence.



## Observability



`api/observability/` defines Prometheus metrics, optional OpenTelemetry tracing,
and HTTP middleware. `/metrics` is exposed when `prometheus-client` is installed.
Enable Jaeger/OTLP export with `OTEL_TRACING_ENABLED=true` or
`OTEL_EXPORTER_OTLP_ENDPOINT`. Grafana dashboard scaffold:

`monitoring/grafana/dashboards/rag-overview.json`.



## C++ HNSW Module



`hnsw-cpp/` provides pybind11 bindings over an hnswlib-compatible index (or a

documented brute-force fallback without hnswlib). Benchmarks:

`hnsw-cpp/benchmarks/benchmark_hnsw.py` (prints measured timings locally).



## Deployment Targets



- **Docker Compose** — local infrastructure (`docker-compose.yml`)

- **Dockerfiles** — `docker/api.Dockerfile`, `docker/worker.Dockerfile` (runs `scripts/run_worker.py`)

- **Kubernetes** — scaffold manifests in `infrastructure/kubernetes/`


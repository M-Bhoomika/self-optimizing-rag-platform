"""FastAPI dependency providers."""

from __future__ import annotations

from functools import lru_cache

from api.app.auth import TenantAuthService
from api.cache.redis_cache import RedisCache
from api.config.settings import get_settings
from api.embeddings.factory import get_embedding_provider
from api.evaluation.service import EvaluationService
from api.generation.factory import get_llm_provider
from api.generation.service import GenerationService
from api.rag.service import RAGService
from api.retrieval.factory import get_vector_store
from api.retrieval.pipeline import IterativeRetrievalPipeline
from api.retrieval.service import RetrievalService
from api.services.query_persistence import QueryPersistenceService


@lru_cache(maxsize=1)
def get_settings_cached():
    return get_settings()


@lru_cache(maxsize=1)
def get_embedding_provider_cached():
    return get_embedding_provider()


@lru_cache(maxsize=1)
def get_vector_store_cached():
    return get_vector_store()


@lru_cache(maxsize=1)
def get_retrieval_service() -> RetrievalService:
    return RetrievalService(
        embedding_provider=get_embedding_provider_cached(),
        vector_store=get_vector_store_cached(),
    )


@lru_cache(maxsize=1)
def get_generation_service() -> GenerationService:
    return GenerationService(llm_provider=get_llm_provider())


@lru_cache(maxsize=1)
def get_cache() -> RedisCache:
    settings = get_settings()
    return RedisCache(redis_url=settings.cache.redis_url, default_ttl=settings.cache.ttl)


@lru_cache(maxsize=1)
def get_pipeline() -> IterativeRetrievalPipeline:
    return IterativeRetrievalPipeline(
        retrieval_service=get_retrieval_service(),
        generation_service=get_generation_service(),
    )


@lru_cache(maxsize=1)
def get_rag_service() -> RAGService:
    return RAGService(retrieval_service=get_retrieval_service())


@lru_cache(maxsize=1)
def get_query_persistence() -> QueryPersistenceService:
    return QueryPersistenceService()


@lru_cache(maxsize=1)
def get_evaluation_service() -> EvaluationService:
    return EvaluationService(pipeline=get_pipeline())


@lru_cache(maxsize=1)
def get_tenant_auth_service() -> TenantAuthService:
    return TenantAuthService(session=None)

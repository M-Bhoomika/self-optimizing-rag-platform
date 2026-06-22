"""Shared pytest configuration."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("AUTH_REQUIRED", "false")
os.environ.setdefault("SKIP_DB", "true")
os.environ.setdefault("RETRIEVAL_BACKEND", "memory")


@pytest.fixture(autouse=True)
def reset_app_state() -> None:
    from api.app.auth import clear_test_tenants
    from api.app import dependencies
    from api.experiments.tracker import ExperimentTracker

    clear_test_tenants()
    ExperimentTracker.shared()._runs.clear()
    from api.config import settings as settings_module
    for fn in (
        dependencies.get_settings_cached,
        dependencies.get_embedding_provider_cached,
        dependencies.get_vector_store_cached,
        dependencies.get_retrieval_service,
        dependencies.get_generation_service,
        dependencies.get_cache,
        dependencies.get_pipeline,
        dependencies.get_rag_service,
        dependencies.get_query_persistence,
        dependencies.get_evaluation_service,
        dependencies.get_tenant_auth_service,
    ):
        fn.cache_clear()
    settings_module.get_settings.cache_clear()

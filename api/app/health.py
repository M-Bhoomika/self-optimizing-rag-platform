"""Health check router."""

from __future__ import annotations

from fastapi import APIRouter

SERVICE_NAME = "Self-Optimizing RAG Platform"
SERVICE_VERSION = "0.1.0"

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    """Basic liveness check."""
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
    }

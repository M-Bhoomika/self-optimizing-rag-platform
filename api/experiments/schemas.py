"""Experiment-tracking Pydantic models."""

from __future__ import annotations

from datetime import datetime
from typing import Dict

from pydantic import BaseModel, Field


class ExperimentConfig(BaseModel):
    """Configuration describing a single RAG experiment."""

    experiment_name: str
    embedding_model: str
    chunk_size: int
    overlap: int
    top_k: int


class ExperimentRun(BaseModel):
    """A tracked experiment run with its config and recorded metrics."""

    run_id: str
    config: ExperimentConfig
    metrics: Dict[str, float] = Field(default_factory=dict)
    created_at: datetime

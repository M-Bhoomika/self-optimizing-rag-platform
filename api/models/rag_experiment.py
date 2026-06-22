"""RAG experiment ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import DateTime, Double, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class RagExperiment(Base):
    __tablename__ = "rag_experiments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    mlflow_run_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    config: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    ragas_scores: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    deployed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    traffic_percentage: Mapped[float] = mapped_column(Double, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<RagExperiment id={self.id!r} mlflow_run_id={self.mlflow_run_id!r}>"

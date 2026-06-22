"""SQLAlchemy type for pgvector columns."""

from __future__ import annotations

from typing import Any, List, Optional, Sequence

from sqlalchemy.types import UserDefinedType


class Vector1536(UserDefinedType):
    """PostgreSQL ``VECTOR(1536)`` column type without requiring pgvector at import time."""

    cache_ok = True

    def get_col_spec(self, **kwargs: Any) -> str:
        return "VECTOR(1536)"

    def bind_processor(self, dialect: Any):
        def process(value: Optional[Sequence[float]]) -> Optional[str]:
            if value is None:
                return None
            return "[" + ",".join(str(float(v)) for v in value) + "]"

        return process

    def result_processor(self, dialect: Any, coltype: Any):
        def process(value: Any) -> Optional[List[float]]:
            if value is None:
                return None
            if isinstance(value, list):
                return [float(v) for v in value]
            text = str(value).strip("[]")
            if not text:
                return []
            return [float(part) for part in text.split(",") if part.strip()]

        return process

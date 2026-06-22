"""Database session management with lazy engine initialization."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator, Optional

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None


def get_engine() -> Engine:
    global _engine, _SessionLocal
    if _engine is None:
        from sqlalchemy import create_engine

        from api.config.settings import get_settings

        settings = get_settings()
        url = settings.database.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg://", 1)
        _engine = create_engine(
            url,
            pool_pre_ping=True,
            pool_size=settings.database.pool_size,
            connect_args={"connect_timeout": 2},
            future=True,
        )
        _SessionLocal = sessionmaker(
            bind=_engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            class_=Session,
            future=True,
        )
    return _engine


def get_session_factory() -> sessionmaker:
    get_engine()
    assert _SessionLocal is not None
    return _SessionLocal


def _db_disabled() -> bool:
    return os.getenv("SKIP_DB", "").lower() in {"1", "true", "yes"}


@contextmanager
def get_db_session() -> Iterator[Session]:
    """Yield a database session, committing on success and rolling back on error."""
    if _db_disabled():
        raise RuntimeError("Database access disabled (SKIP_DB=true).")
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Iterator[Session]:
    """FastAPI dependency for request-scoped database sessions."""
    with get_db_session() as session:
        yield session

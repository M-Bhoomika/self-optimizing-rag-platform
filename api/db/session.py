"""SQLAlchemy engine and session factory.

Exposes a process-wide engine, a configured ``sessionmaker``, and a
``get_db_session()`` helper that yields a session and guarantees cleanup.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .config import get_database_url

engine: Engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
    future=True,
)


@contextmanager
def get_db_session() -> Iterator[Session]:
    """Yield a database session, committing on success and rolling back on error.

    Usage:
        with get_db_session() as session:
            session.execute(...)
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

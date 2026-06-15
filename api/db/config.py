"""Database configuration.

Loads connection settings from the environment. The canonical value is
``DATABASE_URL`` (e.g. ``postgresql://user:pass@host:5432/dbname``). The URL is
normalized to use the psycopg (v3) driver so SQLAlchemy selects the right
dialect.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")


def get_database_url() -> str:
    """Return the configured database URL, normalized for psycopg v3.

    Raises:
        RuntimeError: if ``DATABASE_URL`` is not set in the environment.
    """
    url = os.getenv("DATABASE_URL", DATABASE_URL)
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Define it in your environment or .env file, "
            "e.g. postgresql+psycopg://rag_user:rag_password@localhost:5432/rag_platform"
        )

    # Ensure the psycopg (v3) driver is used.
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)

    return url

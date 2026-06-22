"""Initialize the PostgreSQL database from ``schema.sql``.

Run directly:

    python -m api.db.init_db

Connects using ``DATABASE_URL``, reads the co-located ``schema.sql`` file, and
executes it inside a transaction. The schema is written to be idempotent
(``CREATE EXTENSION IF NOT EXISTS`` / ``CREATE TABLE IF NOT EXISTS`` /
``CREATE INDEX IF NOT EXISTS``), so it is safe to run repeatedly.
"""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .session import get_engine

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def read_schema() -> str:
    """Read the schema SQL file from disk."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
    return SCHEMA_PATH.read_text(encoding="utf-8")


def init_db() -> bool:
    """Create the schema in PostgreSQL.

    Returns:
        True on success, False on failure.
    """
    try:
        schema_sql = read_schema()
    except OSError as exc:
        print(f"[init_db] FAILURE: could not read schema file: {exc}")
        return False

    try:
        with get_engine().begin() as connection:
            connection.execute(text(schema_sql))
        print("[init_db] SUCCESS: schema created/verified.")
        return True
    except SQLAlchemyError as exc:
        print(f"[init_db] FAILURE: database error while applying schema: {exc}")
        return False


def main() -> None:
    success = init_db()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

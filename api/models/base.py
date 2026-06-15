"""Shared SQLAlchemy declarative base.

All ORM models inherit from :class:`Base`. Using the 2.0 declarative style
(`DeclarativeBase`) so models can use `Mapped`/`mapped_column` annotations.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base class shared by all ORM models."""

    pass

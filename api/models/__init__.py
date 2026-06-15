"""ORM model layer for the RAG platform.

Re-exports the declarative ``Base`` and the domain models so they can be
imported from a single namespace and registered on the shared metadata.
"""

from .base import Base
from .chunk import Chunk
from .document import Document
from .tenant import Tenant

__all__ = ["Base", "Tenant", "Document", "Chunk"]

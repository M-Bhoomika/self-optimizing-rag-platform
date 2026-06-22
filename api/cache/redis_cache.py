"""Redis-backed query cache with statistics."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class CacheStatistics:
    """In-process cache operation counters."""

    hits: int = 0
    misses: int = 0
    writes: int = 0

    @property
    def total_requests(self) -> int:
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests

    def to_dict(self) -> Dict[str, float | int]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "writes": self.writes,
            "total_requests": self.total_requests,
            "hit_rate": self.hit_rate,
        }


@dataclass
class RedisCache:
    """Tenant-scoped cache with Redis backend and in-memory fallback."""

    redis_url: Optional[str] = None
    default_ttl: int = 300
    _client: Any = field(default=None, init=False, repr=False)
    _memory: Dict[str, str] = field(default_factory=dict, init=False, repr=False)
    _enabled: bool = field(default=False, init=False, repr=False)
    stats: CacheStatistics = field(default_factory=CacheStatistics, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.redis_url:
            try:
                import redis  # type: ignore

                self._client = redis.Redis.from_url(self.redis_url, decode_responses=True)
                self._client.ping()
                self._enabled = True
            except Exception:
                self._client = None
                self._enabled = False

    @staticmethod
    def make_key(tenant_id: str, query: str) -> str:
        digest = hashlib.sha256(query.encode("utf-8")).hexdigest()
        return f"{tenant_id}:{digest}"

    def get(self, tenant_id: str, query: str) -> Optional[Dict[str, Any]]:
        from api.utils.retry import retry_call

        def _read() -> Optional[Dict[str, Any]]:
            key = self.make_key(tenant_id, query)
            raw: Optional[str]
            if self._enabled and self._client is not None:
                raw = self._client.get(key)
            else:
                raw = self._memory.get(key)
            if raw is None:
                self.stats.misses += 1
                return None
            self.stats.hits += 1
            return json.loads(raw)

        try:
            return retry_call(_read, attempts=2, exceptions=(Exception,))
        except Exception:
            self.stats.misses += 1
            return None

    def set(
        self,
        tenant_id: str,
        query: str,
        value: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> None:
        key = self.make_key(tenant_id, query)
        payload = json.dumps(value)
        ttl_seconds = self.default_ttl if ttl is None else ttl
        if self._enabled and self._client is not None:
            self._client.setex(key, ttl_seconds, payload)
        else:
            self._memory[key] = payload
        self.stats.writes += 1

    @property
    def enabled(self) -> bool:
        return self._enabled

    def statistics(self) -> CacheStatistics:
        return self.stats

"""Redis cache tests."""

from __future__ import annotations

from api.cache.redis_cache import RedisCache


def test_cache_key_format() -> None:
    key = RedisCache.make_key("tenant-a", "hello")
    assert key.startswith("tenant-a:")
    assert len(key.split(":")) == 2


def test_cache_memory_roundtrip() -> None:
    cache = RedisCache(redis_url=None)
    cache.set("tenant-a", "hello", {"answer": "world"}, ttl=60)
    assert cache.get("tenant-a", "hello") == {"answer": "world"}


def test_cache_statistics() -> None:
    cache = RedisCache(redis_url=None)
    assert cache.get("tenant-a", "missing") is None
    cache.set("tenant-a", "q", {"answer": "a"})
    assert cache.get("tenant-a", "q") is not None
    stats = cache.statistics()
    assert stats.hits == 1
    assert stats.misses == 1
    assert stats.writes == 1
    assert stats.hit_rate == 0.5

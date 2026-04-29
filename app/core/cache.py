"""
In-memory TTL cache for API response caching.

Stores results in memory with a configurable expiry time.
No external service required — suitable for single-process deployments.
"""

import time
from cachetools import TTLCache

# Feed cache: max 500 entries, each expires after 60 seconds
feed_cache = TTLCache(maxsize=500, ttl=60)

# Lock-free for reads; use with caution on multi-threaded writes
_cache_timestamps: dict = {}


def cache_set(cache: TTLCache, key: str, value) -> None:
    cache[key] = value
    _cache_timestamps[key] = time.time()


def cache_get(cache: TTLCache, key: str):
    return cache.get(key)


def cache_get_timestamp(key: str) -> float | None:
    return _cache_timestamps.get(key)

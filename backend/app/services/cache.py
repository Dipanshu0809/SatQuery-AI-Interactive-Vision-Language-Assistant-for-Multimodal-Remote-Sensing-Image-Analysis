"""
Minimal in-memory TTL cache for external API responses (fires, weather,
imagery metadata). Not distributed/persistent — fine for a single-process
demo/portfolio deployment. Swap for Redis if this ever needs to scale
across workers.
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class _Entry:
    value: Any
    expires_at: float
    fetched_at: float


class TTLCache:
    def __init__(self):
        self._store: dict[str, _Entry] = {}
        self._inflight: dict[str, "asyncio.Future"] = {}

    def get(self, key: str) -> tuple[Any, float] | None:
        entry = self._store.get(key)
        if not entry:
            return None
        if time.time() > entry.expires_at:
            del self._store[key]
            return None
        return entry.value, entry.fetched_at

    def set(self, key: str, value: Any, ttl_seconds: int):
        now = time.time()
        self._store[key] = _Entry(value=value, expires_at=now + ttl_seconds, fetched_at=now)

    async def get_or_fetch(self, key: str, ttl_seconds: int, fetch_fn: Callable):
        cached = self.get(key)
        if cached is not None:
            value, fetched_at = cached
            return value, fetched_at, True
        # If the same key is already being fetched, wait for that result instead of
        # sending a duplicate request upstream (saves API quota).
        pending = self._inflight.get(key)
        if pending is not None:
            value = await asyncio.shield(pending)
            return value, time.time(), True
        fut = asyncio.get_running_loop().create_future()
        self._inflight[key] = fut
        try:
            value = await fetch_fn()
        except BaseException as exc:
            fut.set_exception(exc)
            fut.exception()  # mark retrieved so asyncio does not warn
            raise
        finally:
            self._inflight.pop(key, None)
        fut.set_result(value)
        self.set(key, value, ttl_seconds)
        return value, time.time(), False


cache = TTLCache()

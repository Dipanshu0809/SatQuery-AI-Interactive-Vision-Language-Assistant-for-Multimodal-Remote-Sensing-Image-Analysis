"""
Shared reliability helpers for every live data source.

- request_with_retry / arequest_with_retry: HTTP calls with sensible timeouts and
  automatic retries (exponential backoff) on timeouts, connection errors and the
  temporary status codes 408/425/429/500/502/503/504.
- MemoCache: small thread-safe TTL cache used to avoid repeating identical
  upstream requests (saves Copernicus processing units, Gemini quota and time).

Log messages show only the host name, never the full URL, because some URLs
(NASA FIRMS) contain an API key.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import random
import threading
import time
from typing import Any
from urllib.parse import urlsplit

import httpx

logger = logging.getLogger("satquery.resilience")

RETRY_STATUS = {408, 425, 429, 500, 502, 503, 504}


def _host(url: str) -> str:
    return urlsplit(url).netloc or "upstream"


def _wait_seconds(attempt: int, backoff: float, response: httpx.Response | None = None) -> float:
    if response is not None:
        retry_after = response.headers.get("Retry-After", "")
        if retry_after.isdigit():
            return min(float(retry_after), 20.0)
    return backoff * (2 ** attempt) + random.uniform(0, 0.4)


def request_with_retry(method: str, url: str, *, timeout: Any = 60.0, attempts: int = 3,
                       backoff: float = 1.0, **kwargs) -> httpx.Response:
    """Synchronous HTTP request with retries. Returns the final response
    (callers decide what a non-2xx status means). Raises the last transport
    error if every attempt failed to get a response."""
    for attempt in range(attempts):
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                response = client.request(method, url, **kwargs)
        except httpx.TransportError as exc:  # timeouts, DNS, connection resets
            if attempt == attempts - 1:
                raise
            wait = _wait_seconds(attempt, backoff)
            logger.warning("%s %s: %s; retrying in %.1fs (%d/%d)", method, _host(url),
                           type(exc).__name__, wait, attempt + 1, attempts - 1)
            time.sleep(wait)
            continue
        if response.status_code in RETRY_STATUS and attempt < attempts - 1:
            wait = _wait_seconds(attempt, backoff, response)
            logger.warning("%s %s returned %s; retrying in %.1fs (%d/%d)", method, _host(url),
                           response.status_code, wait, attempt + 1, attempts - 1)
            time.sleep(wait)
            continue
        return response
    raise RuntimeError("unreachable")  # pragma: no cover


async def arequest_with_retry(method: str, url: str, *, timeout: Any = 60.0, attempts: int = 3,
                              backoff: float = 1.0, **kwargs) -> httpx.Response:
    """Async version of request_with_retry."""
    for attempt in range(attempts):
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.request(method, url, **kwargs)
        except httpx.TransportError as exc:
            if attempt == attempts - 1:
                raise
            wait = _wait_seconds(attempt, backoff)
            logger.warning("%s %s: %s; retrying in %.1fs (%d/%d)", method, _host(url),
                           type(exc).__name__, wait, attempt + 1, attempts - 1)
            await asyncio.sleep(wait)
            continue
        if response.status_code in RETRY_STATUS and attempt < attempts - 1:
            wait = _wait_seconds(attempt, backoff, response)
            logger.warning("%s %s returned %s; retrying in %.1fs (%d/%d)", method, _host(url),
                           response.status_code, wait, attempt + 1, attempts - 1)
            await asyncio.sleep(wait)
            continue
        return response
    raise RuntimeError("unreachable")  # pragma: no cover


def describe_transport_error(exc: Exception, service: str) -> str:
    """Human-readable message for a network failure after all retries."""
    if isinstance(exc, httpx.TimeoutException):
        return f"{service} did not respond in time, even after retries. Please try again in a minute."
    return f"Could not connect to {service} ({type(exc).__name__}). Check the internet connection and try again."


def make_key(*parts: Any) -> str:
    """Stable cache key from JSON-serialisable parts (bytes are hashed)."""
    h = hashlib.sha256()
    for p in parts:
        if isinstance(p, (bytes, bytearray)):
            h.update(hashlib.sha256(p).digest())
        else:
            h.update(json.dumps(p, sort_keys=True, default=str).encode())
        h.update(b"|")
    return h.hexdigest()


class MemoCache:
    """Thread-safe TTL cache with a size limit (oldest entries evicted first)."""

    def __init__(self, max_items: int = 256):
        self._data: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()
        self._max = max_items

    def get(self, key: str) -> Any | None:
        with self._lock:
            item = self._data.get(key)
            if not item:
                return None
            expires, value = item
            if time.time() > expires:
                del self._data[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl_seconds: float) -> None:
        with self._lock:
            if len(self._data) >= self._max:
                oldest = min(self._data, key=lambda k: self._data[k][0])
                del self._data[oldest]
            self._data[key] = (time.time() + ttl_seconds, value)

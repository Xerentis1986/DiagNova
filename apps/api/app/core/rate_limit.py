"""Einfaches In-Memory-Rate-Limit (pro Prozess). Für Multi-Worker später Redis o. ä."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    retry_after_sec: float
    remaining: int
    limit: int
    window_sec: float


class SlidingWindowRateLimiter:
    """Sliding-Window-Zähler nach Schlüssel (z. B. IP oder E-Mail)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str, *, limit: int, window_sec: float) -> RateLimitResult:
        now = time.monotonic()
        cutoff = now - window_sec
        with self._lock:
            q = self._hits[key]
            while q and q[0] < cutoff:
                q.popleft()
            if len(q) >= limit:
                oldest = q[0] if q else now
                retry = max(0.0, window_sec - (now - oldest))
                return RateLimitResult(
                    allowed=False,
                    retry_after_sec=retry,
                    remaining=0,
                    limit=limit,
                    window_sec=window_sec,
                )
            q.append(now)
            return RateLimitResult(
                allowed=True,
                retry_after_sec=0.0,
                remaining=max(0, limit - len(q)),
                limit=limit,
                window_sec=window_sec,
            )

    def reset(self, key: str | None = None) -> None:
        with self._lock:
            if key is None:
                self._hits.clear()
            else:
                self._hits.pop(key, None)


# Prozessweite Limiter (Tests können resetten)
login_limiter = SlidingWindowRateLimiter()
api_write_limiter = SlidingWindowRateLimiter()

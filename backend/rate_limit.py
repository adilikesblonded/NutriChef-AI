"""
Simple in-memory, per-client sliding-window rate limiter.

Protects the Spoonacular daily quota once the app is public: without it a
single visitor could use up the whole day's quota for everyone. State lives
in process memory, which is fine for a single-instance deployment.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque


class RateLimiter:

    def __init__(self, limit: int, window_seconds: int = 3600):
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str) -> int | None:
        """Record a request. Returns seconds until retry if over the limit, else None."""
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > self.window:
                hits.popleft()

            if len(hits) >= self.limit:
                return int(self.window - (now - hits[0])) + 1

            hits.append(now)
            return None

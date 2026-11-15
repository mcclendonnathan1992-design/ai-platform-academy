"""RateLimit concept: stop one client from using all the capacity.

Spec:
  purpose:    share a scarce resource (model time) fairly
  principle:  each client may make N requests per window; the (N+1)th is
              refused until older requests age out
  actions:    allow(client) -> (allowed, retry_after_seconds)

Sliding window, in memory, per process. With several replicas each pod keeps
its own counts, so the real limit is N x replicas. That is a design tradeoff
worth discussing in Module 02 (the fix is a shared store such as Redis).
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Callable


class RateLimiter:
    def __init__(
        self,
        limit_per_window: int,
        window_s: float = 60.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.limit = limit_per_window
        self.window = window_s
        self._clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> tuple[bool, float]:
        if self.limit <= 0:  # disabled
            return True, 0.0
        now = self._clock()
        hits = self._hits[key]
        while hits and now - hits[0] >= self.window:
            hits.popleft()
        if len(hits) >= self.limit:
            return False, self.window - (now - hits[0])
        hits.append(now)
        return True, 0.0

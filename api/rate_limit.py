"""In-memory limits for POST /ask: per client per minute, and for everyone per day.

Enough for a single-instance demo; counters reset when the process restarts.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone


class RateLimitExceeded(Exception):
    def __init__(self, message: str, retry_after: int):
        super().__init__(message)
        self.retry_after = retry_after


class AskRateLimiter:
    def __init__(self, per_minute: int, per_day: int, clock=time.monotonic, today=None):
        self.per_minute = per_minute
        self.per_day = per_day
        self._clock = clock
        self._today = today or (lambda: datetime.now(timezone.utc).date())
        self._recent: dict[str, deque[float]] = defaultdict(deque)
        self._day = None
        self._day_count = 0
        self._lock = threading.Lock()

    def check(self, client: str) -> None:
        """Count one request from `client`, or raise RateLimitExceeded."""
        with self._lock:
            now = self._clock()
            today = self._today()
            if today != self._day:
                self._day, self._day_count = today, 0
            if self._day_count >= self.per_day:
                raise RateLimitExceeded("The demo has reached its daily question limit. Try again tomorrow.", 3600)

            recent = self._recent[client]
            while recent and now - recent[0] >= 60:
                recent.popleft()
            if len(recent) >= self.per_minute:
                retry_after = int(60 - (now - recent[0])) + 1
                raise RateLimitExceeded("Too many questions in a minute. Please wait a moment.", retry_after)

            recent.append(now)
            self._day_count += 1

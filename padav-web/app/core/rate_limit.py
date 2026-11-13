"""In-process abuse protection.

State lives in memory, so limits are per worker process. For multi-instance
deployments swap ``_Store`` for a Redis-backed implementation; the public classes
stay the same.
"""
import threading
import time
from collections import defaultdict, deque

from fastapi import Request

from app.core.config import settings
from app.core.exceptions import RateLimitedError


class SlidingWindowLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str) -> int | None:
        """Record a hit. Returns None if allowed, else seconds until retry."""
        now = time.monotonic()
        with self._lock:
            bucket = self._hits[key]
            while bucket and now - bucket[0] >= self.window:
                bucket.popleft()
            if len(bucket) >= self.limit:
                return int(self.window - (now - bucket[0])) + 1
            bucket.append(now)
            if len(self._hits) > 10_000:  # bound memory under key-spraying
                self._evict(now)
            return None

    def _evict(self, now: float) -> None:
        for k in [k for k, b in self._hits.items() if not b or now - b[-1] >= self.window]:
            del self._hits[k]

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


class RateLimit:
    """FastAPI dependency: ``Depends(RateLimit("auth", limit=20))``."""

    _registry: list[SlidingWindowLimiter] = []

    def __init__(self, scope: str, limit: int, window_seconds: int = 60) -> None:
        self.scope = scope
        self._limiter = SlidingWindowLimiter(limit, window_seconds)
        RateLimit._registry.append(self._limiter)

    def __call__(self, request: Request) -> None:
        if not settings.rate_limit_enabled:
            return
        # NOTE: behind a reverse proxy run uvicorn with --proxy-headers and
        # --forwarded-allow-ips so request.client reflects the real client.
        client = request.client.host if request.client else "unknown"
        retry = self._limiter.hit(f"{self.scope}:{client}")
        if retry is not None:
            raise RateLimitedError(retry)

    @classmethod
    def reset_all(cls) -> None:
        for limiter in cls._registry:
            limiter.reset()


class LoginThrottle:
    """Locks an account/IP pair after repeated failed logins (credential stuffing)."""

    def __init__(self, max_failures: int, lockout_seconds: int) -> None:
        self._max = max_failures
        self._lockout = lockout_seconds
        self._failures: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, key: str, now: float) -> deque[float]:
        bucket = self._failures[key]
        while bucket and now - bucket[0] >= self._lockout:
            bucket.popleft()
        return bucket

    def ensure_allowed(self, key: str) -> None:
        if not settings.rate_limit_enabled:
            return
        now = time.monotonic()
        with self._lock:
            bucket = self._prune(key, now)
            if len(bucket) >= self._max:
                raise RateLimitedError(int(self._lockout - (now - bucket[0])) + 1,
                                       "Try Again 😒, Too Many Requests.")

    def record_failure(self, key: str) -> None:
        with self._lock:
            self._failures[key].append(time.monotonic())

    def clear(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)

    def reset(self) -> None:
        with self._lock:
            self._failures.clear()


login_throttle = LoginThrottle(settings.login_max_failures, settings.login_lockout_seconds)
auth_rate_limit = RateLimit("auth", settings.auth_rate_limit_per_minute)
write_rate_limit = RateLimit("write", 120)


def reset_rate_limits() -> None:
    RateLimit.reset_all()
    login_throttle.reset()

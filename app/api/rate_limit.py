from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field


@dataclass
class _Bucket:
    tokens: float
    updated: float


@dataclass
class TokenBucketLimiter:
    rate: float = 10.0
    capacity: float = 10.0
    _buckets: dict[str, _Bucket] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def allow(self, key: str, now: float | None = None) -> bool:
        current = time.monotonic() if now is None else now
        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                self._buckets[key] = _Bucket(tokens=self.capacity - 1.0, updated=current)
                return True
            elapsed = max(0.0, current - bucket.updated)
            bucket.tokens = min(self.capacity, bucket.tokens + elapsed * self.rate)
            bucket.updated = current
            if bucket.tokens >= 1.0:
                bucket.tokens -= 1.0
                return True
            return False


def client_key(client_host: str | None, api_key: str | None) -> str:
    if api_key:
        return f"key:{api_key}"
    return f"ip:{client_host or 'unknown'}"

import threading
import time
from collections import defaultdict, deque

from fastapi import Depends, HTTPException, Request

_lock = threading.Lock()
_hits: dict[str, deque[float]] = defaultdict(deque)


def hit(key: str, limit: int, window_seconds: int) -> None:
    """Record an attempt. Raise 429 if `limit` attempts already happened in the window."""
    now = time.monotonic()
    with _lock:
        attempts = _hits[key]
        while attempts and now - attempts[0] > window_seconds:
            attempts.popleft()
        if len(attempts) >= limit:
            retry_after = int(window_seconds - (now - attempts[0])) + 1
            raise HTTPException(
                status_code=429,
                detail="Too many attempts. Please wait a few minutes and try again.",
                headers={"Retry-After": str(retry_after)},
            )
        attempts.append(now)


def limit_by_ip(name: str, limit: int, window_seconds: int):
    """Route dependency that limits requests per client IP."""
    def dependency(request: Request) -> None:
        ip = request.client.host if request.client else "unknown"
        hit(f"{name}:ip:{ip}", limit, window_seconds)
    return Depends(dependency)
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status


class FixedWindowRateLimiter:
    def __init__(self):
        self.arr = defaultdict(deque)

    def allow(self, key, limit, window_seconds):
        t = time.monotonic()
        q = self.arr[key]
        old = t - window_seconds

        while q and q[0] <= old:
            q.popleft()

        if len(q) >= limit:
            return False

        q.append(t)
        return True


limiter = FixedWindowRateLimiter()


def enforce_rate_limit(
    request: Request, scope, limit, window_seconds=60, identifier=None
):
    host = request.client.host if request.client else "unknown"
    key = f"{scope}:{host}:{identifier or '*'}"

    if not limiter.allow(key, limit, window_seconds):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests",
        )

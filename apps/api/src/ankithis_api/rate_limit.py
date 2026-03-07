"""Redis-based rate limiting middleware."""

from __future__ import annotations

import time

from fastapi import HTTPException, status
from redis import Redis

from ankithis_api.config import settings

_redis: Redis | None = None


def _get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


def check_rate_limit(user_id: str, action: str, limit: int) -> None:
    """Check if user has exceeded rate limit for an action.

    Uses a sliding window counter stored in Redis.
    Raises HTTP 429 if limit exceeded.
    """
    r = _get_redis()
    key = f"ratelimit:{action}:{user_id}"
    now = time.time()
    window = 3600  # 1 hour

    pipe = r.pipeline()
    pipe.zremrangebyscore(key, 0, now - window)
    pipe.zadd(key, {f"{now}": now})
    pipe.zcard(key)
    pipe.expire(key, window)
    results = pipe.execute()

    count = results[2]
    if count > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {limit} {action}s per hour",
        )

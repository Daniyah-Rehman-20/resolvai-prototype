import time
from fastapi import HTTPException, Request, status
from app.core.config import settings
from app.infrastructure.redis import redis_client

async def enforce_rate_limit(request: Request) -> None:
    if request.url.path.startswith(("/health", "/docs", "/openapi.json")):
        return
    identity = request.headers.get("X-Demo-User") or (request.client.host if request.client else "unknown")
    bucket = int(time.time()) // settings.rate_limit_window_seconds
    key = f"ratelimit:{identity}:{bucket}"
    try:
        client = redis_client()
        count = await client.incr(key)
        if count == 1:
            await client.expire(key, settings.rate_limit_window_seconds + 1)
        if count > settings.rate_limit_requests:
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Rate limit exceeded")
    except HTTPException:
        raise
    except Exception:
        # Availability-first fallback for the portfolio demo. Production monitoring
        # must alert when Redis is degraded.
        return

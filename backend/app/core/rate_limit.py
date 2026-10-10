import hashlib
import time

from fastapi import HTTPException, Request, status
from app.core.config import settings
from app.infrastructure.redis import redis_client

# Bounded per-process fallback is for development only. Production fails closed
# if the shared limiter is unavailable; provision and monitor Redis accordingly.
_local_buckets: dict[str, tuple[int, int]] = {}


async def enforce_rate_limit(request: Request) -> None:
    if request.url.path.startswith(("/health", "/docs", "/openapi.json")):
        return
    # Do not trust X-Demo-User or forwarded-IP headers supplied by callers.
    identity = request.client.host if request.client else "unknown"
    identity = hashlib.sha256(identity.encode()).hexdigest()
    auth_path = request.url.path in {"/auth/login", "/auth/register"}
    window = 60 if auth_path else settings.rate_limit_window_seconds
    limit = min(settings.rate_limit_requests, 10) if auth_path else settings.rate_limit_requests
    bucket = int(time.time()) // window
    key = f"ratelimit:{'auth' if auth_path else 'api'}:{identity}:{bucket}"
    try:
        client = redis_client()
        # Set TTL in the same atomic operation so a worker crash cannot strand a key.
        count = await client.eval(
            "local n = redis.call('INCR', KEYS[1]); "
            "if n == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end; return n",
            1, key, window + 1,
        )
    except Exception:
        if settings.app_env not in {"development", "test"}:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                                "Request limiter temporarily unavailable") from None
        now = int(time.time())
        if len(_local_buckets) > 10000:
            for stale_key, (_, expiry) in list(_local_buckets.items()):
                if expiry <= now:
                    _local_buckets.pop(stale_key, None)
            if len(_local_buckets) > 10000:
                raise HTTPException(503, "Request limiter temporarily unavailable")
        previous, _ = _local_buckets.get(key, (0, 0))
        count = previous + 1
        _local_buckets[key] = (count, (bucket + 1) * window + 1)
    if count > limit:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Rate limit exceeded",
                            headers={"Retry-After": str(window)})

import hashlib
import time
from fastapi import HTTPException, status
from app.infrastructure.redis import redis_client

# Process-local fallback keeps the portfolio demo usable if Redis is unavailable.
# Production deployments should require the shared Redis store.
_LOCAL_KEYS: dict[str, float] = {}

class IdempotencyGuard:
    def __init__(self, key: str, scope: str, ttl_seconds: int = 3600):
        self.key = f"idempotency:{scope}:{hashlib.sha256(key.encode()).hexdigest()}"
        self.ttl = ttl_seconds
        self.client = redis_client()
        self.local_fallback = False

    async def acquire(self) -> None:
        try:
            acquired = await self.client.set(self.key, "processing", ex=self.ttl, nx=True)
            if not acquired:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    "Duplicate request is already processing or completed",
                )
            return
        except HTTPException:
            raise
        except Exception:
            self.local_fallback = True
            now = time.time()
            expiry = _LOCAL_KEYS.get(self.key, 0)
            if expiry > now:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    "Duplicate request is already processing or completed",
                )
            _LOCAL_KEYS[self.key] = now + self.ttl

    async def complete(self) -> None:
        if self.local_fallback:
            _LOCAL_KEYS[self.key] = time.time() + self.ttl
            return
        try:
            await self.client.set(self.key, "completed", ex=self.ttl)
        except Exception:
            _LOCAL_KEYS[self.key] = time.time() + self.ttl

    async def release(self) -> None:
        if self.local_fallback:
            _LOCAL_KEYS.pop(self.key, None)
            return
        try:
            value = await self.client.get(self.key)
            if value == "processing":
                await self.client.delete(self.key)
        except Exception:
            _LOCAL_KEYS.pop(self.key, None)

import hashlib
from fastapi import HTTPException, status
from app.infrastructure.redis import redis_client

class IdempotencyGuard:
    def __init__(self, key: str, scope: str, ttl_seconds: int = 3600):
        self.key = f"idempotency:{scope}:{hashlib.sha256(key.encode()).hexdigest()}"
        self.ttl = ttl_seconds
        self.client = redis_client()

    async def acquire(self) -> None:
        try:
            acquired = await self.client.set(self.key, "processing", ex=self.ttl, nx=True)
        except Exception as exc:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Idempotency store unavailable") from exc
        if not acquired:
            raise HTTPException(status.HTTP_409_CONFLICT, "Duplicate request is already processing or completed")

    async def complete(self) -> None:
        await self.client.set(self.key, "completed", ex=self.ttl)

    async def release(self) -> None:
        value = await self.client.get(self.key)
        if value == "processing":
            await self.client.delete(self.key)

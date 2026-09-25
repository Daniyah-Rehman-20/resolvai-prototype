import json
from functools import lru_cache
from redis.asyncio import Redis
from app.core.config import settings

@lru_cache
def redis_client() -> Redis:
    return Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)

async def get_json(key: str):
    value = await redis_client().get(key)
    return json.loads(value) if value else None

async def set_json(key: str, value, ttl_seconds: int = 3600):
    await redis_client().set(key, json.dumps(value, default=str), ex=ttl_seconds)

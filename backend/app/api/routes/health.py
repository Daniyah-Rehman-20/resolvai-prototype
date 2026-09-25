import asyncio
from urllib.parse import urlparse
import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.core.config import settings
from app.db.session import engine
from app.infrastructure.redis import redis_client

router = APIRouter(tags=["health"])

@router.get("/health")
async def health():
    return {"status":"healthy","service":"payresolve-api","version":settings.version}

async def database_ok():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

async def redis_ok():
    try:
        return bool(await redis_client().ping())
    except Exception:
        return False

async def qdrant_ok():
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            return (await client.get(f"{settings.qdrant_url}/readyz")).is_success
    except Exception:
        return False

async def rabbitmq_ok():
    try:
        parsed = urlparse(settings.rabbitmq_url)
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(parsed.hostname or "localhost", parsed.port or 5672), timeout=1.5
        )
        writer.close()
        await writer.wait_closed()
        return True
    except Exception:
        return False

@router.get("/health/ready")
async def ready():
    database, redis, qdrant, rabbitmq = await asyncio.gather(
        database_ok(), redis_ok(), qdrant_ok(), rabbitmq_ok()
    )
    deps = {"database":database,"redis":redis,"qdrant":qdrant,"rabbitmq":rabbitmq}
    critical = database and redis
    payload = {"status":"ready" if critical else "not_ready","dependencies":deps}
    return JSONResponse(status_code=200 if critical else 503, content=payload)

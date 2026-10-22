import asyncio
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

@router.get("/health/ready")
async def ready():
    database, redis = await asyncio.gather(database_ok(), redis_ok())
    deps = {"database":database,"redis":redis}
    critical = database and redis
    payload = {"status":"ready" if critical else "not_ready","dependencies":deps}
    return JSONResponse(status_code=200 if critical else 503, content=payload)

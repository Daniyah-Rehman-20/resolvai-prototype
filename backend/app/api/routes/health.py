from fastapi import APIRouter
from app.core.config import settings
router=APIRouter(tags=["health"])
@router.get("/health")
async def health(): return {"status":"healthy","service":"payresolve-api","version":settings.version}
@router.get("/health/ready")
async def ready(): return {"status":"ready","dependencies":{"database":"configured","redis":"optional/degraded-ok","qdrant":"optional/local-fallback","rabbitmq":"optional/degraded-ok"}}

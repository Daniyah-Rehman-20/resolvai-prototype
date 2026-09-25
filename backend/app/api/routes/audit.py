from fastapi import APIRouter,Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models import AuditEvent
from app.core.security import Principal, require

router=APIRouter(prefix="/audit",tags=["audit"])

@router.get("")
async def all(db:AsyncSession=Depends(get_db), _: Principal = Depends(require("analyst"))):
    r=await db.execute(
        select(AuditEvent).order_by(AuditEvent.timestamp.desc()).limit(250)
    )
    rows=r.scalars().all()
    result=[]
    for event in rows:
        meta=event.metadata_json or {}
        result.append({
            "id":event.id,
            "transactionId":meta.get("transaction_id",""),
            "action":event.action,
            "actor":event.actor,
            "timestamp":event.timestamp,
            "detail":meta.get("note") or f"{event.resource_type}: {event.resource_id}",
        })
    return result

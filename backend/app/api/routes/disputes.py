import uuid
from fastapi import APIRouter,Depends,Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models import Dispute,AuditEvent
from app.schemas.domain import DisputeCreate,DisputeUpdate

router=APIRouter(prefix="/disputes",tags=["disputes"])

def out(d):
    return {
        "id":d.id,
        "transactionId":d.transaction_id,
        "reason":d.reason,
        "status":"IN_REVIEW" if d.status=="UNDER_REVIEW" else d.status,
        "createdAt":d.created_at,
        "note":d.note,
    }

@router.get("")
async def all(db:AsyncSession=Depends(get_db)):
    r=await db.execute(select(Dispute).order_by(Dispute.created_at.desc()))
    return [out(x) for x in r.scalars().all()]

@router.post("",status_code=201)
async def create(b:DisputeCreate,request:Request,db:AsyncSession=Depends(get_db)):
    d=Dispute(
        id=f"DSP-{uuid.uuid4().hex[:8]}",
        transaction_id=b.transaction_id,
        investigation_id=b.investigation_id,
        reason=b.reason,
        status="OPEN",
        note="",
    )
    db.add(d)
    db.add(AuditEvent(
        id=f"AUD-{uuid.uuid4().hex[:8]}",
        actor="demo-reviewer",
        action="DISPUTE_CREATED",
        resource_type="dispute",
        resource_id=d.id,
        metadata_json={"transaction_id":b.transaction_id},
        correlation_id=request.state.correlation_id,
    ))
    await db.commit()
    await db.refresh(d)
    return out(d)

@router.patch("/{id}")
async def patch(id:str,b:DisputeUpdate,request:Request,db:AsyncSession=Depends(get_db)):
    r=await db.execute(select(Dispute).where(Dispute.id==id))
    d=r.scalar_one()
    d.status="UNDER_REVIEW" if b.status=="IN_REVIEW" else b.status
    d.note=b.note
    db.add(AuditEvent(
        id=f"AUD-{uuid.uuid4().hex[:8]}",
        actor="demo-reviewer",
        action=f"DISPUTE_{d.status}",
        resource_type="dispute",
        resource_id=d.id,
        metadata_json={"transaction_id":d.transaction_id,"note":b.note},
        correlation_id=request.state.correlation_id,
    ))
    await db.commit()
    await db.refresh(d)
    return out(d)

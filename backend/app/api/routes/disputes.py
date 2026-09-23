import uuid
from fastapi import APIRouter,Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models import Dispute
from app.schemas.domain import DisputeCreate,DisputeUpdate
router=APIRouter(prefix="/disputes",tags=["disputes"])
def out(d): return {"id":d.id,"transactionId":d.transaction_id,"reason":d.reason,"status":"IN_REVIEW" if d.status=="UNDER_REVIEW" else d.status,"createdAt":d.created_at,"note":d.note}
@router.get("")
async def all(db:AsyncSession=Depends(get_db)):
    r=await db.execute(select(Dispute).order_by(Dispute.created_at.desc())); return [out(x) for x in r.scalars().all()]
@router.post("",status_code=201)
async def create(b:DisputeCreate,db:AsyncSession=Depends(get_db)):
    d=Dispute(id=f"DSP-{uuid.uuid4().hex[:8]}",transaction_id=b.transaction_id,investigation_id=b.investigation_id,reason=b.reason,status="OPEN",note=""); db.add(d); await db.commit(); await db.refresh(d); return out(d)
@router.patch("/{id}")
async def patch(id:str,b:DisputeUpdate,db:AsyncSession=Depends(get_db)):
    r=await db.execute(select(Dispute).where(Dispute.id==id)); d=r.scalar_one(); d.status=b.status; d.note=b.note; await db.commit(); return out(d)

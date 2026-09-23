from fastapi import APIRouter,Depends,Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models import Investigation
from app.schemas.domain import InvestigationCreate
from app.services.investigation import investigate
router=APIRouter(prefix="/investigations",tags=["investigations"])
def out(i): return {"id":i.id,"transactionId":i.transaction_id,"question":i.question,"status":i.status,"steps":i.agent_steps,"summary":i.summary,"cause":i.likely_cause,"evidence":i.evidence,"policyId":i.sources[0]["document"] if i.sources else None,"recommendation":i.recommended_action,"uncertainty":"Synthetic demo result grounded in local policy evidence; sensitive actions are simulated and approval-gated.","requiresApproval":i.approval_required,"createdAt":i.created_at,"duration":i.duration_ms,"sources":i.sources}
@router.post("",status_code=201)
async def create(body:InvestigationCreate,request:Request,db:AsyncSession=Depends(get_db)): return out(await investigate(db,body.transaction_id,body.question,request.state.correlation_id))
@router.get("")
async def list_all(db:AsyncSession=Depends(get_db)):
    r=await db.execute(select(Investigation).order_by(Investigation.created_at.desc())); return [out(x) for x in r.scalars().all()]
@router.get("/{id}")
async def get_one(id:str,db:AsyncSession=Depends(get_db)):
    r=await db.execute(select(Investigation).where(Investigation.id==id)); x=r.scalar_one_or_none(); return out(x) if x else {"error":{"code":"INVESTIGATION_NOT_FOUND","message":f"Investigation {id} was not found."}}

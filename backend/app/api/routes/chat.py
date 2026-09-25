from fastapi import APIRouter,Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.domain import ChatRequest
from app.services.investigation import investigate
from app.rag.service import rag_service
from app.core.security import Principal, require
router=APIRouter(prefix="/chat",tags=["chat"])
@router.post("")
async def chat(b:ChatRequest,db:AsyncSession=Depends(get_db), _: Principal = Depends(require("analyst"))):
    if b.transaction_id:
        i=await investigate(db,b.transaction_id,b.message); return {"mode":"transaction_investigation","investigation_id":i.id,"answer":i.summary,"sources":i.sources}
    src=rag_service.search(b.message,4); return {"mode":"general_rag","answer":"Based on the synthetic PayResolve policies, review the cited evidence and use only simulated actions when escalation is required.","sources":[{k:v for k,v in s.items() if k!='text'} for s in src]}

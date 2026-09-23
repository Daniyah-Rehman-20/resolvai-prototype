from fastapi import APIRouter,Depends
from sqlalchemy import select,func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models import Transaction,Investigation,ApprovalRequest,Dispute
router=APIRouter(prefix="/analytics",tags=["analytics"])
@router.get("")
async def analytics(db:AsyncSession=Depends(get_db)):
    rows=(await db.execute(select(Transaction))).scalars().all(); total=len(rows); counts={}
    for x in rows: counts[x.overall_status]=counts.get(x.overall_status,0)+1
    inv=(await db.execute(select(func.count()).select_from(Investigation))).scalar_one(); approvals=(await db.execute(select(func.count()).select_from(ApprovalRequest))).scalar_one(); disputes=(await db.execute(select(func.count()).select_from(Dispute))).scalar_one()
    pct=lambda n: round(100*n/total,2) if total else 0
    return {"totalTransactions":total,"successRate":pct(counts.get("SUCCESS",0)),"failureRate":pct(counts.get("FAILED",0)+counts.get("PAYMENT_FAILED",0)),"pendingRate":pct(counts.get("PENDING",0)),"refundRate":pct(counts.get("REFUNDED",0)+counts.get("REFUND_PENDING",0)),"disputeRate":pct(counts.get("DISPUTED",0)),"investigations":inv,"approvalRequests":approvals,"disputes":disputes}

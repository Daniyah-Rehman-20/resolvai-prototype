from datetime import datetime, timezone
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import ApprovalRequest, AuditEvent
from app.core.exceptions import ApprovalNotFound, DuplicateOperation
async def get_approval(db,id):
    r=await db.execute(select(ApprovalRequest).where(ApprovalRequest.id==id)); a=r.scalar_one_or_none()
    if not a: raise ApprovalNotFound(f"Approval {id} was not found.")
    return a
async def decide(db,id,decision,note,reviewer="demo-reviewer",correlation_id=""):
    a=await get_approval(db,id)
    if a.status not in {"PENDING","MORE_INFORMATION_REQUIRED"}: raise DuplicateOperation("This approval has already been decided.")
    a.status=decision; a.reviewer=reviewer; a.reviewer_note=note; a.reviewed_at=datetime.now(timezone.utc)
    if decision=="APPROVED":
        a.execution_result={"action":a.recommended_action,"transaction_id":a.transaction_id,"status":"SIMULATED_SUCCESS"}; a.status="EXECUTED"
    db.add(AuditEvent(id=f"AUD-{uuid.uuid4().hex[:8]}",actor=reviewer,action=f"APPROVAL_{decision}",resource_type="approval",resource_id=a.id,metadata_json={"simulated":True},correlation_id=correlation_id))
    await db.commit(); await db.refresh(a); return a

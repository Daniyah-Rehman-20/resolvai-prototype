from datetime import datetime, timezone
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import ApprovalRequest, AuditEvent, Transaction, Dispute
from app.core.exceptions import ApprovalNotFound, DuplicateOperation

async def get_approval(db,id):
    r=await db.execute(select(ApprovalRequest).where(ApprovalRequest.id==id))
    a=r.scalar_one_or_none()
    if not a:
        raise ApprovalNotFound(f"Approval {id} was not found.")
    return a

async def decide(db,id,decision,note,reviewer="demo-reviewer",correlation_id=""):
    a=await get_approval(db,id)
    if a.status not in {"PENDING","MORE_INFORMATION_REQUIRED"}:
        raise DuplicateOperation("This approval has already been decided.")

    a.status=decision
    a.reviewer=reviewer
    a.reviewer_note=note
    a.reviewed_at=datetime.now(timezone.utc)

    if decision=="APPROVED":
        tx=(await db.execute(
            select(Transaction).where(Transaction.transaction_id==a.transaction_id)
        )).scalar_one_or_none()

        if tx and a.recommended_action in {"SIMULATED_REFUND","SIMULATED_REVERSAL"}:
            tx.overall_status="REFUND_PENDING"

        if tx and a.recommended_action=="CREATE_DISPUTE":
            tx.overall_status="DISPUTED"
            existing=(await db.execute(
                select(Dispute).where(
                    Dispute.transaction_id==a.transaction_id,
                    Dispute.status!="RESOLVED",
                )
            )).scalar_one_or_none()
            if not existing:
                db.add(Dispute(
                    id=f"DSP-{uuid.uuid4().hex[:8]}",
                    transaction_id=a.transaction_id,
                    investigation_id=a.investigation_id,
                    reason=a.reason,
                    status="OPEN",
                    note=note,
                ))

        a.execution_result={
            "action":a.recommended_action,
            "transaction_id":a.transaction_id,
            "status":"SIMULATED_SUCCESS",
        }
        a.status="EXECUTED"

    db.add(AuditEvent(
        id=f"AUD-{uuid.uuid4().hex[:8]}",
        actor=reviewer,
        action=f"APPROVAL_{decision}",
        resource_type="approval",
        resource_id=a.id,
        metadata_json={
            "simulated":True,
            "transaction_id":a.transaction_id,
            "note":note,
        },
        correlation_id=correlation_id,
    ))
    await db.commit()
    await db.refresh(a)
    return a

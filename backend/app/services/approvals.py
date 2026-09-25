from datetime import datetime, timezone
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import ApprovalRequest, AuditEvent, Transaction, Dispute
from app.core.exceptions import ApprovalNotFound, DuplicateOperation

async def get_approval(db: AsyncSession, id: str, *, for_update: bool = False):
    stmt = select(ApprovalRequest).where(ApprovalRequest.id == id)
    if for_update:
        stmt = stmt.with_for_update()
    r = await db.execute(stmt)
    approval = r.scalar_one_or_none()
    if not approval:
        raise ApprovalNotFound(f"Approval {id} was not found.")
    return approval

async def decide(
    db: AsyncSession, id: str, decision: str, note: str,
    reviewer: str, correlation_id: str = "",
):
    # Row-level lock prevents two approvers from executing the same action concurrently
    # on PostgreSQL. SQLite remains suitable only for local demo use.
    approval = await get_approval(db, id, for_update=True)
    if approval.status not in {"PENDING", "MORE_INFORMATION_REQUIRED"}:
        raise DuplicateOperation("This approval has already been decided.")

    approval.status = decision
    approval.reviewer = reviewer
    approval.reviewer_note = note
    approval.reviewed_at = datetime.now(timezone.utc)

    if decision == "APPROVED":
        tx = (await db.execute(
            select(Transaction).where(Transaction.transaction_id == approval.transaction_id).with_for_update()
        )).scalar_one_or_none()

        if tx and approval.recommended_action in {"SIMULATED_REFUND", "SIMULATED_REVERSAL"}:
            tx.overall_status = "REFUND_PENDING"

        if tx and approval.recommended_action == "CREATE_DISPUTE":
            tx.overall_status = "DISPUTED"
            existing = (await db.execute(
                select(Dispute).where(
                    Dispute.transaction_id == approval.transaction_id,
                    Dispute.status != "RESOLVED",
                )
            )).scalar_one_or_none()
            if not existing:
                db.add(Dispute(
                    id=f"DSP-{uuid.uuid4().hex[:8]}",
                    transaction_id=approval.transaction_id,
                    investigation_id=approval.investigation_id,
                    reason=approval.reason,
                    status="OPEN",
                    note=note,
                ))

        approval.execution_result = {
            "action": approval.recommended_action,
            "transaction_id": approval.transaction_id,
            "status": "SIMULATED_SUCCESS",
        }
        approval.status = "EXECUTED"

    db.add(AuditEvent(
        id=f"AUD-{uuid.uuid4().hex[:8]}",
        actor=reviewer,
        action=f"APPROVAL_{decision}",
        resource_type="approval",
        resource_id=approval.id,
        metadata_json={
            "simulated": True,
            "transaction_id": approval.transaction_id,
            "note": note,
        },
        correlation_id=correlation_id,
    ))
    await db.commit()
    await db.refresh(approval)
    return approval

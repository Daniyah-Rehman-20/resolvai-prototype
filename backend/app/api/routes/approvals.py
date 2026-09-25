from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models import ApprovalRequest
from app.schemas.domain import ApprovalDecision
from app.services.approvals import decide
from app.core.security import Principal, require
from app.core.idempotency import IdempotencyGuard

router = APIRouter(prefix="/approvals", tags=["approvals"])

def out(a):
    if a.status == "MORE_INFORMATION_REQUIRED":
        status = "MORE_INFO"
    elif a.status == "EXECUTED":
        status = "APPROVED"
    else:
        status = a.status
    return {
        "id": a.id, "transactionId": a.transaction_id, "action": a.recommended_action,
        "reason": a.reason, "evidence": a.evidence,
        "policyId": a.policy_citations[0]["document"] if a.policy_citations else None,
        "reasoning": a.reason, "status": status, "createdAt": a.created_at,
        "decidedAt": a.reviewed_at, "note": a.reviewer_note,
        "executionResult": a.execution_result,
    }

@router.get("")
async def all(
    db: AsyncSession = Depends(get_db),
    _: Principal = Depends(require("analyst")),
):
    r = await db.execute(select(ApprovalRequest).order_by(ApprovalRequest.created_at.desc()))
    return [out(x) for x in r.scalars().all()]

@router.get("/{id}")
async def one(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: Principal = Depends(require("analyst")),
):
    r = await db.execute(select(ApprovalRequest).where(ApprovalRequest.id == id))
    a = r.scalar_one_or_none()
    if not a:
        raise HTTPException(404, f"Approval {id} was not found.")
    return out(a)

@router.post("/{id}/approve")
async def approve(
    id: str, b: ApprovalDecision, request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require("approver")),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
):
    guard = IdempotencyGuard(idempotency_key, f"approval:{id}:approve")
    await guard.acquire()
    try:
        result = out(await decide(db, id, "APPROVED", b.note, principal.subject, request.state.correlation_id))
        await guard.complete()
        return result
    except Exception:
        await guard.release()
        raise

@router.post("/{id}/reject")
async def reject(
    id: str, b: ApprovalDecision, request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require("approver")),
):
    return out(await decide(db, id, "REJECTED", b.note, principal.subject, request.state.correlation_id))

@router.post("/{id}/request-information")
async def info(
    id: str, b: ApprovalDecision, request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require("approver")),
):
    return out(await decide(db, id, "MORE_INFORMATION_REQUIRED", b.note, principal.subject, request.state.correlation_id))

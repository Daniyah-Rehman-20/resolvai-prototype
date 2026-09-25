import time
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.transactions import TransactionRepository
from app.models import Investigation, ApprovalRequest, AuditEvent
from app.agents.graph import investigation_graph
from app.core.constants import Action

def cause_for(action: Action) -> str:
    if action == Action.RECONCILE:
        return "Bank debit and gateway success conflict with merchant failure; reconciliation is required before any simulated refund."
    if action == Action.WAIT_AND_RECHECK:
        return "The UPI transaction is still pending in the synthetic gateway state."
    if action == Action.SIMULATED_REFUND:
        return "Multiple payment records indicate a possible duplicate charge for the same order."
    return "The recorded payment states require operator review."

async def investigate(db: AsyncSession, txid: str, question: str, correlation_id: str = ""):
    started = time.perf_counter()
    tx = await TransactionRepository(db).get(txid)
    result = await investigation_graph.run(tx, question)

    action = Action(result["recommended_action"])
    sources = [
        {k: v for k, v in source.items() if k != "text"}
        for source in result.get("policy_evidence", [])
    ]
    evidence = [f"{tx.transaction_id} · {tx.order_id}", *result.get("evidence", [])]
    steps = [
        {"id":"STEP-1","agent":"Transaction Agent","action":"Compare bank/gateway/merchant/order state","status":"completed","duration":0,"timestamp":""},
        {"id":"STEP-2","agent":"RAG Agent","action":"Retrieve policy evidence with BM25","status":"completed","duration":0,"timestamp":""},
        {"id":"STEP-3","agent":"Resolution Agent","action":"Recommend deterministic next action","status":"completed","duration":0,"timestamp":""},
        {"id":"STEP-4","agent":"Risk Engine","action":"Evaluate action sensitivity and approval requirement","status":"completed","duration":0,"timestamp":""},
    ]
    summary = tx.issue or f"Investigation of {tx.transaction_id}"
    inv = Investigation(
        id=f"INV-{uuid.uuid4().hex[:8]}", transaction_id=txid, question=question,
        status="completed", issue=tx.issue, summary=summary, likely_cause=cause_for(action),
        recommended_action=action.value, risk_level=result["risk_level"],
        approval_required=result["approval_required"], evidence=evidence, sources=sources,
        agent_steps=steps, tool_calls=[], duration_ms=int((time.perf_counter()-started)*1000),
    )
    db.add(inv)

    if result["approval_required"]:
        db.add(ApprovalRequest(
            id=f"APR-{uuid.uuid4().hex[:8]}", transaction_id=txid,
            investigation_id=inv.id, recommended_action=action.value, amount=tx.amount,
            reason=summary, evidence=evidence, policy_citations=sources,
            risk_level=result["risk_level"], status="PENDING",
        ))

    db.add(AuditEvent(
        id=f"AUD-{uuid.uuid4().hex[:8]}", actor="system",
        action="INVESTIGATION_COMPLETED", resource_type="investigation",
        resource_id=inv.id, metadata_json={
            "transaction_id": txid, "recommended_action": action.value,
            "risk_level": result["risk_level"],
        }, correlation_id=correlation_id,
    ))
    await db.commit()
    await db.refresh(inv)
    return inv

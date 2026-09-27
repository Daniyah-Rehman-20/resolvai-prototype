import time
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import investigation_graph
from app.core.constants import Action
from app.models import ApprovalRequest, AuditEvent, Investigation
from app.repositories.transactions import TransactionRepository

def readable(action: Action) -> str:
    return action.value.replace("SIMULATED_", "").replace("_", " ").title()

def cause_for(action: Action) -> str:
    if action == Action.RECONCILE:
        return "Bank debit and gateway success conflict with merchant failure; the payment needs reconciliation before a refund recommendation."
    if action == Action.WAIT_AND_RECHECK:
        return "The payment has not reached a final state, so the safest next step is to wait for confirmation and check again."
    if action == Action.SIMULATED_REFUND:
        return "Multiple payment records indicate a possible duplicate charge for the same order."
    if action == Action.CREATE_DISPUTE:
        return "The transaction is already marked disputed and requires a controlled dispute workflow."
    if action == Action.NO_ACTION:
        return "The recorded payment states are already consistent with a completed outcome."
    return "The recorded payment states do not match a known auto-resolution path and require operator review."

def question_focus(question: str) -> str:
    q = question.lower()
    if any(x in q for x in ["refund", "money back", "return my money"]):
        return "REFUND"
    if any(x in q for x in ["approval", "approve", "human", "risk"]):
        return "APPROVAL"
    if any(x in q for x in ["policy", "rule", "guideline", "sla"]):
        return "POLICY"
    if any(x in q for x in ["status", "where is", "current state", "pending now"]):
        return "STATUS"
    if any(x in q for x in ["why", "what happened", "cause", "reason"]):
        return "CAUSE"
    if any(x in q for x in ["what should", "next step", "what do i do", "action"]):
        return "NEXT_ACTION"
    if any(x in q for x in ["duplicate", "twice", "double charged"]):
        return "DUPLICATE"
    return "GENERAL"

def answer_for_question(tx, question: str, action: Action, result: dict):
    focus = question_focus(question)
    state_line = (
        f"Bank={tx.bank_status}, Gateway={tx.gateway_status}, "
        f"Merchant={tx.merchant_status}, Order={tx.order.status}"
    )
    policy = result.get("policy_evidence", [])
    top_policy = policy[0] if policy else None
    policy_name = (
        top_policy["document"].replace("-", " ").title()
        if top_policy
        else "No matching policy"
    )
    approval = bool(result.get("approval_required"))

    if focus == "STATUS":
        summary = f"{tx.transaction_id} is currently {tx.overall_status}. {state_line}."
        cause = cause_for(action)
    elif focus == "CAUSE":
        summary = f"The state evidence for {tx.transaction_id} is {state_line}."
        cause = cause_for(action)
    elif focus == "NEXT_ACTION":
        summary = f"Recommended next action: {readable(action)}."
        cause = f"{cause_for(action)} This recommendation is based on {state_line}."
    elif focus == "REFUND":
        if action == Action.SIMULATED_REFUND:
            summary = "The evidence supports a refund recommendation, but it must pass the approval workflow first."
        elif action in {Action.RECONCILE, Action.WAIT_AND_RECHECK}:
            summary = f"A refund should not be initiated yet. The current next step is {readable(action)}."
        else:
            summary = f"The current transaction state does not justify an automatic refund. Recommended action: {readable(action)}."
        cause = cause_for(action)
    elif focus == "APPROVAL":
        summary = (
            f"{readable(action)} {'requires' if approval else 'does not require'} human approval "
            f"for this transaction."
        )
        cause = (
            "Sensitive payment actions are approval-gated by the deterministic risk engine."
            if approval
            else "The recommended action does not mutate money or open a sensitive payment case."
        )
    elif focus == "POLICY":
        summary = f"The strongest retrieved policy match is {policy_name}."
        cause = (
            f"It was retrieved using the transaction context plus your question: “{question.strip()}”."
        )
    elif focus == "DUPLICATE":
        summary = (
            "This transaction contains duplicate-payment indicators."
            if "duplicate" in tx.issue.lower()
            else "No duplicate-payment indicator is present in the current transaction evidence."
        )
        cause = cause_for(action)
    else:
        summary = (
            f"For your question “{question.strip()}”, PayResolve found {state_line}. "
            f"Recommended next action: {readable(action)}."
        )
        cause = cause_for(action)
    return summary, cause, focus

async def investigate(
    db: AsyncSession,
    txid: str,
    question: str,
    correlation_id: str = "",
):
    started = time.perf_counter()
    tx = await TransactionRepository(db).get(txid)
    result = await investigation_graph.run(tx, question)

    action = Action(result["recommended_action"])
    sources = [
        {k: v for k, v in source.items() if k != "text"}
        for source in result.get("policy_evidence", [])
    ]
    summary, cause, focus = answer_for_question(tx, question, action, result)
    evidence = [
        f"Question focus: {focus.replace('_', ' ').title()}",
        f"{tx.transaction_id} · {tx.order_id}",
        *result.get("evidence", []),
    ]
    steps = [
        {
            "id": "STEP-1",
            "agent": "Transaction Agent",
            "action": "Compare bank, gateway, merchant and order state",
            "status": "completed",
            "duration": 0,
            "timestamp": "",
        },
        {
            "id": "STEP-2",
            "agent": "RAG Agent",
            "action": f"Retrieve policy evidence for {focus.replace('_', ' ').lower()} question",
            "status": "completed",
            "duration": 0,
            "timestamp": "",
        },
        {
            "id": "STEP-3",
            "agent": "Resolution Agent",
            "action": "Combine transaction state with policy evidence and question intent",
            "status": "completed",
            "duration": 0,
            "timestamp": "",
        },
        {
            "id": "STEP-4",
            "agent": "Risk Engine",
            "action": "Evaluate action sensitivity and approval requirement",
            "status": "completed",
            "duration": 0,
            "timestamp": "",
        },
    ]

    inv = Investigation(
        id=f"INV-{uuid.uuid4().hex[:8]}",
        transaction_id=txid,
        question=question,
        status="completed",
        issue=tx.issue,
        summary=summary,
        likely_cause=cause,
        recommended_action=action.value,
        risk_level=result["risk_level"],
        approval_required=result["approval_required"],
        evidence=evidence,
        sources=sources,
        agent_steps=steps,
        tool_calls=[],
        duration_ms=int((time.perf_counter() - started) * 1000),
    )
    db.add(inv)

    if result["approval_required"]:
        db.add(
            ApprovalRequest(
                id=f"APR-{uuid.uuid4().hex[:8]}",
                transaction_id=txid,
                investigation_id=inv.id,
                recommended_action=action.value,
                amount=tx.amount,
                reason=summary,
                evidence=evidence,
                policy_citations=sources,
                risk_level=result["risk_level"],
                status="PENDING",
            )
        )

    db.add(
        AuditEvent(
            id=f"AUD-{uuid.uuid4().hex[:8]}",
            actor="system",
            action="INVESTIGATION_COMPLETED",
            resource_type="investigation",
            resource_id=inv.id,
            metadata_json={
                "transaction_id": txid,
                "question": question,
                "question_focus": focus,
                "recommended_action": action.value,
                "risk_level": result["risk_level"],
                "note": f"{focus.replace('_', ' ').title()} investigation completed: {readable(action)}",
            },
            correlation_id=correlation_id,
        )
    )
    await db.commit()
    await db.refresh(inv)
    return inv

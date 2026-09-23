import time, uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.transactions import TransactionRepository
from app.models import Investigation, ApprovalRequest, AuditEvent
from app.rag.service import rag_service
from app.agents.risk import evaluate
from app.core.constants import Action

def choose_action(tx):
    if tx.overall_status in {"SUCCESS","REFUNDED"}: return Action.NO_ACTION
    if tx.payment_method=="UPI" and tx.overall_status=="PENDING": return Action.WAIT_AND_RECHECK
    if tx.bank_status=="DEBITED" and tx.gateway_status=="SUCCESS" and tx.merchant_status=="FAILED": return Action.RECONCILE
    if "duplicate" in tx.issue.lower(): return Action.SIMULATED_REFUND
    if tx.overall_status=="DISPUTED": return Action.CREATE_DISPUTE
    return Action.ESCALATE
async def investigate(db:AsyncSession, txid:str, question:str, correlation_id:str=""):
    started=time.perf_counter(); tx=await TransactionRepository(db).get(txid)
    steps=[]; tools=[]
    steps.append({"id":"STEP-1","agent":"Transaction Agent","action":"Compare bank/gateway/merchant/order state","status":"completed","duration":4,"timestamp":""})
    evidence=[f"{tx.transaction_id} · {tx.order_id}",f"Bank: {tx.bank_status}",f"Gateway: {tx.gateway_status}",f"Merchant: {tx.merchant_status}",f"Order: {tx.order.status}"]
    query=f"{tx.payment_method} {tx.overall_status} {tx.issue} {question}"; sources=rag_service.search(query,5)
    steps.append({"id":"STEP-2","agent":"RAG Agent","action":"Retrieve synthetic policy evidence","status":"completed","duration":8,"timestamp":""})
    action=choose_action(tx); risk,approval=evaluate(action,tx.amount)
    if action==Action.RECONCILE: cause="Bank debit and gateway success conflict with merchant failure; reconciliation is required before any simulated refund."
    elif action==Action.WAIT_AND_RECHECK: cause="The UPI transaction is still pending in the synthetic gateway state."
    elif action==Action.SIMULATED_REFUND: cause="Multiple payment records indicate a possible duplicate charge for the same order."
    else: cause="The recorded payment states require operator review."
    summary=tx.issue or f"Investigation of {tx.transaction_id}"
    inv=Investigation(id=f"INV-{uuid.uuid4().hex[:8]}",transaction_id=txid,question=question,status="completed",issue=tx.issue,summary=summary,likely_cause=cause,recommended_action=action.value,risk_level=risk,approval_required=approval,evidence=evidence,sources=[{k:v for k,v in s.items() if k!='text'} for s in sources],agent_steps=steps,tool_calls=tools,duration_ms=int((time.perf_counter()-started)*1000))
    db.add(inv)
    if approval:
        db.add(ApprovalRequest(id=f"APR-{uuid.uuid4().hex[:8]}",transaction_id=txid,investigation_id=inv.id,recommended_action=action.value,amount=tx.amount,reason=summary,evidence=evidence,policy_citations=inv.sources,risk_level=risk,status="PENDING"))
    db.add(AuditEvent(id=f"AUD-{uuid.uuid4().hex[:8]}",actor="system",action="INVESTIGATION_STARTED",resource_type="investigation",resource_id=inv.id,metadata_json={"transaction_id":txid},correlation_id=correlation_id))
    await db.commit(); await db.refresh(inv); return inv

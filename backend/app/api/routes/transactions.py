import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import Principal, require
from app.db.session import get_db
from app.models import AuditEvent, Customer, Order, Transaction
from app.repositories.transactions import TransactionRepository
from app.schemas.domain import PaymentEventIngest, TransactionIngest

router = APIRouter(prefix="/transactions", tags=["transactions"])

def to_frontend(tx):
    return {
        "id": tx.transaction_id,
        "orderId": tx.order_id,
        "customer": {
            "id": tx.customer.id,
            "name": tx.customer.name,
            "email": tx.customer.email,
        },
        "method": tx.payment_method,
        "amount": tx.amount,
        "status": tx.overall_status,
        "bank": tx.bank_status,
        "gateway": tx.gateway_status,
        "merchant": tx.merchant_status,
        "order": tx.order.status,
        "createdAt": tx.created_at,
        "issue": tx.issue,
        "maskedInstrument": tx.masked_payment_reference,
    }

def scenario_values(scenario: str | None):
    scenarios = {
        "PENDING": {
            "bank": "PENDING",
            "gateway": "PENDING",
            "merchant": "PENDING",
            "overall": "PENDING",
            "order": "PENDING",
            "issue": "Payment initiated; final confirmation is pending.",
        },
        "FAILED": {
            "bank": "DEBITED",
            "gateway": "SUCCESS",
            "merchant": "FAILED",
            "overall": "PAYMENT_FAILED",
            "order": "PAYMENT_FAILED",
            "issue": "Bank debit and gateway success were recorded, but merchant confirmation failed.",
        },
        "SUCCESS": {
            "bank": "DEBITED",
            "gateway": "SUCCESS",
            "merchant": "SUCCESS",
            "overall": "SUCCESS",
            "order": "PAYMENT_CONFIRMED",
            "issue": "Payment completed successfully.",
        },
        "DISPUTED": {
            "bank": "DEBITED",
            "gateway": "SUCCESS",
            "merchant": "SUCCESS",
            "overall": "DISPUTED",
            "order": "PAYMENT_CONFIRMED",
            "issue": "Customer dispute was recorded for the completed payment.",
        },
    }
    return scenarios.get(scenario or "PENDING", scenarios["PENDING"])

def derive_overall(tx: Transaction) -> str:
    states = {
        tx.bank_status.upper(),
        tx.gateway_status.upper(),
        tx.merchant_status.upper(),
        tx.order.status.upper(),
    }
    if "DISPUTED" in states:
        return "DISPUTED"
    if tx.merchant_status.upper() == "FAILED" or tx.order.status.upper() in {
        "FAILED",
        "PAYMENT_FAILED",
    }:
        if tx.bank_status.upper() == "DEBITED" and tx.gateway_status.upper() == "SUCCESS":
            return "RECONCILIATION_REQUIRED"
        return "PAYMENT_FAILED"
    if tx.bank_status.upper() == "FAILED" or tx.gateway_status.upper() == "FAILED":
        return "FAILED"
    if (
        tx.bank_status.upper() in {"DEBITED", "SUCCESS"}
        and tx.gateway_status.upper() == "SUCCESS"
        and tx.merchant_status.upper() == "SUCCESS"
        and tx.order.status.upper() in {"SUCCESS", "PAYMENT_CONFIRMED"}
    ):
        return "SUCCESS"
    if "PENDING" in states:
        return "PENDING"
    return tx.overall_status

@router.get("")
async def list_transactions(
    search: str | None = None,
    payment_method: str | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: Principal = Depends(require("viewer")),
):
    rows = await TransactionRepository(db).list(
        search, payment_method, status, page_size, (page - 1) * page_size
    )
    return [to_frontend(x) for x in rows]

@router.post("", status_code=201)
async def ingest_transaction(
    body: TransactionIngest,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require("analyst")),
):
    txid = body.transaction_id or f"TXN-{uuid.uuid4().hex[:8].upper()}"
    existing = await db.execute(
        select(Transaction).where(Transaction.transaction_id == txid)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(409, f"Transaction {txid} already exists")

    customer = None
    if body.customer_id:
        customer = (
            await db.execute(select(Customer).where(Customer.id == body.customer_id))
        ).scalar_one_or_none()
    if customer is None and body.customer_email:
        customer = (
            await db.execute(select(Customer).where(Customer.email == body.customer_email))
        ).scalar_one_or_none()

    if customer is None:
        customer_id = body.customer_id or f"CUS-{uuid.uuid4().hex[:8].upper()}"
        customer = Customer(
            id=customer_id,
            name=body.customer_name,
            email=body.customer_email or f"{customer_id.lower()}@payresolve.local",
        )
        db.add(customer)

    values = scenario_values(body.scenario)
    order_id = body.order_id or f"ORD-{uuid.uuid4().hex[:8].upper()}"
    existing_order = (
        await db.execute(select(Order).where(Order.id == order_id))
    ).scalar_one_or_none()
    order = existing_order or Order(
        id=order_id,
        customer_id=customer.id,
        status=values["order"],
        amount=body.amount,
    )
    if existing_order is None:
        db.add(order)

    tx = Transaction(
        transaction_id=txid,
        order_id=order.id,
        customer_id=customer.id,
        payment_method=body.payment_method.value,
        amount=body.amount,
        currency=body.currency,
        bank_status=body.bank_status or values["bank"],
        gateway_status=body.gateway_status or values["gateway"],
        merchant_status=body.merchant_status or values["merchant"],
        overall_status=(body.overall_status.value if body.overall_status else values["overall"]),
        gateway_reference=f"GW-{uuid.uuid4().hex[:10].upper()}",
        masked_payment_reference=body.masked_payment_reference,
        issue=body.issue or values["issue"],
        customer=customer,
        order=order,
    )
    db.add(tx)
    db.add(
        AuditEvent(
            id=f"AUD-{uuid.uuid4().hex[:8]}",
            actor=principal.subject,
            action="TRANSACTION_INGESTED",
            resource_type="transaction",
            resource_id=txid,
            metadata_json={
                "transaction_id": txid,
                "source_system": body.source_system,
                "note": f"Transaction ingested from {body.source_system}",
            },
            correlation_id="",
        )
    )
    await db.commit()
    await db.refresh(tx)
    return to_frontend(tx)

@router.post("/{transaction_id}/events")
async def ingest_payment_event(
    transaction_id: str,
    body: PaymentEventIngest,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require("analyst")),
):
    tx = await TransactionRepository(db).get(transaction_id)
    source = body.source.upper()
    status = body.status.upper()

    if source == "BANK":
        tx.bank_status = status
    elif source == "GATEWAY":
        tx.gateway_status = status
    elif source == "MERCHANT":
        tx.merchant_status = status
    elif source == "ORDER":
        tx.order.status = status

    if body.issue:
        tx.issue = body.issue
    tx.overall_status = derive_overall(tx)

    db.add(
        AuditEvent(
            id=f"AUD-{uuid.uuid4().hex[:8]}",
            actor=principal.subject,
            action="PAYMENT_EVENT_RECEIVED",
            resource_type="transaction",
            resource_id=transaction_id,
            metadata_json={
                "transaction_id": transaction_id,
                "source": source,
                "status": status,
                "note": f"{source} reported {status}",
            },
            correlation_id="",
        )
    )
    await db.commit()
    await db.refresh(tx)
    return to_frontend(tx)

@router.get("/{transaction_id}")
async def get_transaction(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
    _: Principal = Depends(require("viewer")),
):
    return to_frontend(await TransactionRepository(db).get(transaction_id))

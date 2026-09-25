from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.repositories.transactions import TransactionRepository
from app.core.security import Principal, require

router = APIRouter(prefix="/transactions", tags=["transactions"])

def to_frontend(tx):
    return {"id":tx.transaction_id,"orderId":tx.order_id,"customer":{"id":tx.customer.id,"name":tx.customer.name,"email":tx.customer.email},"method":tx.payment_method,"amount":tx.amount,"status":tx.overall_status,"bank":tx.bank_status,"gateway":tx.gateway_status,"merchant":tx.merchant_status,"order":tx.order.status,"createdAt":tx.created_at,"issue":tx.issue,"maskedInstrument":tx.masked_payment_reference}

@router.get("")
async def list_transactions(
    search: str | None = None, payment_method: str | None = None, status: str | None = None,
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db), _: Principal = Depends(require("viewer")),
):
    rows = await TransactionRepository(db).list(search, payment_method, status, page_size, (page - 1) * page_size)
    return [to_frontend(x) for x in rows]

@router.get("/{transaction_id}")
async def get_transaction(
    transaction_id: str, db: AsyncSession = Depends(get_db),
    _: Principal = Depends(require("viewer")),
):
    return to_frontend(await TransactionRepository(db).get(transaction_id))

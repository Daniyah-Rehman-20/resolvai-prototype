from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Transaction
from app.core.exceptions import TransactionNotFound
class TransactionRepository:
    def __init__(self,db:AsyncSession): self.db=db
    async def get(self,txid:str)->Transaction:
        r=await self.db.execute(select(Transaction).where(Transaction.transaction_id==txid)); tx=r.scalar_one_or_none()
        if not tx: raise TransactionNotFound(f"Transaction {txid} was not found.")
        return tx
    async def list(self,search:str|None=None,payment_method:str|None=None,status:str|None=None,limit:int=50,offset:int=0):
        q=select(Transaction).order_by(Transaction.created_at.desc())
        if search: q=q.where(or_(Transaction.transaction_id.ilike(f"%{search}%"),Transaction.order_id.ilike(f"%{search}%")))
        if payment_method: q=q.where(Transaction.payment_method==payment_method)
        if status: q=q.where(Transaction.overall_status==status)
        r=await self.db.execute(q.limit(limit).offset(offset)); return list(r.scalars().all())

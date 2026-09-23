import asyncio
from sqlalchemy import select
from app.db.base import Base
from app.db.session import engine,SessionLocal
from app.models import Customer,Order,Transaction
SCENARIOS=[
("TXN-10021","CREDIT_CARD",2000,"DEBITED","SUCCESS","FAILED","PAYMENT_FAILED","Merchant confirmation failed after successful gateway processing."),
("TXN-10035","UPI",850,"PENDING","PENDING","PENDING","PENDING","UPI payment has been pending for 20 minutes."),
("TXN-10031","CREDIT_CARD",1200,"DEBITED","SUCCESS","SUCCESS","SUCCESS","Successful card payment."),
("TXN-10032","DEBIT_CARD",700,"FAILED","FAILED","FAILED","FAILED","Card declined by bank."),
("TXN-10033","UPI",450,"DEBITED","SUCCESS","SUCCESS","SUCCESS","Successful UPI payment."),
("TXN-10034","CREDIT_CARD",1600,"DEBITED","SUCCESS","SUCCESS","REFUND_PENDING","Refund pending."),
("TXN-10036","CASH",999,"N/A","N/A","PENDING","PENDING","Cash on delivery collection mismatch."),
("TXN-10037","CREDIT_CARD",3100,"DEBITED","SUCCESS","FAILED","RECONCILIATION_REQUIRED","Merchant reconciliation required."),
("TXN-10038","UPI",550,"DEBITED","SUCCESS","SUCCESS","DISPUTED","Dispute opened."),
("TXN-10039","CREDIT_CARD",1300,"DEBITED","SUCCESS","SUCCESS","REFUNDED","Refund completed."),
]
async def seed():
    async with engine.begin() as c: await c.run_sync(Base.metadata.create_all)
    async with SessionLocal() as db:
        if (await db.execute(select(Transaction))).scalars().first(): return
        for i in range(1,31):
            cid=f"CUS-{i:03d}"; oid=f"ORD-{1000+i}"; db.add(Customer(id=cid,name=f"Demo Customer {i}",email=f"customer{i}@example.test")); db.add(Order(id=oid,customer_id=cid,status="PAYMENT_CONFIRMED",amount=100+i*50))
        await db.flush()
        for i in range(30):
            if i < len(SCENARIOS): txid,method,amount,bank,gateway,merchant,status,issue=SCENARIOS[i]
            else:
                txid=f"TXN-{10040+i}"; method="UPI" if i%2 else "CREDIT_CARD"; amount=500+i*75; bank=gateway=merchant=status="SUCCESS"; issue="Successful synthetic payment."
            cid=f"CUS-{i+1:03d}"; oid=f"ORD-{1001+i}"
            order=(await db.execute(select(Order).where(Order.id==oid))).scalar_one(); order.status="PAYMENT_FAILED" if status in {"FAILED","PAYMENT_FAILED","RECONCILIATION_REQUIRED"} else ("PENDING" if status=="PENDING" else "PAYMENT_CONFIRMED")
            db.add(Transaction(transaction_id=txid,order_id=oid,customer_id=cid,payment_method=method,amount=amount,currency="INR",bank_status=bank,gateway_status=gateway,merchant_status=merchant,overall_status=status,gateway_reference=f"GW-{i:06d}",masked_payment_reference="**** demo",issue=issue))
        # duplicate pair
        order=(await db.execute(select(Order).where(Order.id=="ORD-1029"))).scalar_one(); order.status="PAYMENT_CONFIRMED"
        for txid in ["TXN-10070","TXN-10071"]: db.add(Transaction(transaction_id=txid,order_id="ORD-1029",customer_id="CUS-029",payment_method="CREDIT_CARD",amount=2500,currency="INR",bank_status="DEBITED",gateway_status="SUCCESS",merchant_status="SUCCESS",overall_status="SUCCESS",gateway_reference=f"GW-{txid[-5:]}",masked_payment_reference="**** 4242",issue="Possible duplicate payment for the same order."))
        await db.commit()
if __name__=="__main__": asyncio.run(seed())

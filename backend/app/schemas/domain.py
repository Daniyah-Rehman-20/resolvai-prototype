from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.core.constants import PaymentMethod, PaymentStatus, ApprovalStatus, Action
class CustomerOut(BaseModel): model_config=ConfigDict(from_attributes=True); id:str; name:str; email:str
class TransactionCreate(BaseModel): transaction_id:str; order_id:str; customer_id:str; payment_method:PaymentMethod; amount:float=Field(gt=0); currency:str="INR"; bank_status:str; gateway_status:str; merchant_status:str; overall_status:PaymentStatus; masked_payment_reference:str; issue:str=""
class TransactionOut(BaseModel):
    model_config=ConfigDict(from_attributes=True); id:str; orderId:str; customer:CustomerOut; method:PaymentMethod; amount:float; status:str; bank:str; gateway:str; merchant:str; order:str; createdAt:datetime; issue:str; maskedInstrument:str
class InvestigationCreate(BaseModel): transaction_id:str; question:str=Field(min_length=3,max_length=2000)
class SourceOut(BaseModel): document:str; section:str|None=None; chunk_id:str; relevance:float|None=None
class InvestigationOut(BaseModel): id:str; transactionId:str; question:str; status:str; steps:list[dict]; summary:str; cause:str; evidence:list[str]; policyId:str|None=None; recommendation:str; uncertainty:str; requiresApproval:bool; createdAt:datetime; duration:int; sources:list[SourceOut]=[]
class ApprovalDecision(BaseModel): note:str=Field(min_length=2,max_length=2000)
class ApprovalOut(BaseModel): id:str; transactionId:str; action:str; reason:str; evidence:list[str]; policyId:str|None=None; reasoning:str; status:str; createdAt:datetime; decidedAt:datetime|None=None; note:str|None=None
class DisputeCreate(BaseModel): transaction_id:str; investigation_id:str|None=None; reason:str
class DisputeUpdate(BaseModel): status:str; note:str
class ChatRequest(BaseModel): message:str; transaction_id:str|None=None

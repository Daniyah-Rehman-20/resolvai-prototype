from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict
from app.core.constants import PaymentMethod, PaymentStatus

class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    email: str

class TransactionCreate(BaseModel):
    transaction_id: str
    order_id: str
    customer_id: str
    payment_method: PaymentMethod
    amount: float = Field(gt=0)
    currency: str = "INR"
    bank_status: str
    gateway_status: str
    merchant_status: str
    overall_status: PaymentStatus
    masked_payment_reference: str
    issue: str = ""

class TransactionIngest(BaseModel):
    transaction_id: str | None = None
    order_id: str | None = None
    customer_id: str | None = None
    customer_name: str = Field(default="Customer", min_length=1, max_length=120)
    customer_email: str | None = None
    payment_method: PaymentMethod = PaymentMethod.UPI
    amount: float = Field(gt=0, le=10_000_000)
    currency: str = "INR"
    scenario: Literal["PENDING", "FAILED", "SUCCESS", "DISPUTED"] | None = "PENDING"
    bank_status: str | None = None
    gateway_status: str | None = None
    merchant_status: str | None = None
    overall_status: PaymentStatus | None = None
    masked_payment_reference: str = "**** 4242"
    issue: str = ""
    source_system: str = Field(default="PAYMENT_GATEWAY", max_length=80)

class PaymentEventIngest(BaseModel):
    source: Literal["BANK", "GATEWAY", "MERCHANT", "ORDER"]
    status: str = Field(min_length=2, max_length=80)
    issue: str | None = Field(default=None, max_length=1000)

class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    orderId: str
    customer: CustomerOut
    method: PaymentMethod
    amount: float
    status: str
    bank: str
    gateway: str
    merchant: str
    order: str
    createdAt: datetime
    issue: str
    maskedInstrument: str

class InvestigationCreate(BaseModel):
    transaction_id: str
    question: str = Field(min_length=3, max_length=2000)

class SourceOut(BaseModel):
    document: str
    section: str | None = None
    chunk_id: str
    relevance: float | None = None

class InvestigationOut(BaseModel):
    id: str
    transactionId: str
    question: str
    status: str
    steps: list[dict]
    summary: str
    cause: str
    evidence: list[str]
    policyId: str | None = None
    recommendation: str
    uncertainty: str
    requiresApproval: bool
    createdAt: datetime
    duration: int
    sources: list[SourceOut] = []

class ApprovalDecision(BaseModel):
    note: str = Field(min_length=2, max_length=2000)

class ApprovalOut(BaseModel):
    id: str
    transactionId: str
    action: str
    reason: str
    evidence: list[str]
    policyId: str | None = None
    reasoning: str
    status: str
    createdAt: datetime
    decidedAt: datetime | None = None
    note: str | None = None

class DisputeCreate(BaseModel):
    transaction_id: str
    investigation_id: str | None = None
    reason: str

class DisputeUpdate(BaseModel):
    status: str
    note: str

class ChatRequest(BaseModel):
    message: str
    transaction_id: str | None = None

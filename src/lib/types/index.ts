export type PaymentMethod = "CREDIT_CARD" | "DEBIT_CARD" | "UPI" | "CASH";
export type PaymentStatus =
  | "SUCCESS"
  | "FAILED"
  | "PAYMENT_FAILED"
  | "RECONCILIATION_REQUIRED"
  | "PENDING"
  | "REFUND_PENDING"
  | "REFUNDED"
  | "DISPUTED";

export interface Customer {
  id: string;
  name: string;
  email: string;
}

export interface Transaction {
  id: string;
  orderId: string;
  customer: Customer;
  method: PaymentMethod;
  amount: number;
  status: PaymentStatus;
  bank: string;
  gateway: string;
  merchant: string;
  order: string;
  createdAt: string;
  issue: string;
  maskedInstrument: string;
}

export interface AgentStep {
  id: string;
  agent: string;
  action: string;
  status: "waiting" | "running" | "completed" | "failed" | "requires_approval";
  duration: number;
  timestamp: string;
}

export interface Investigation {
  id: string;
  transactionId: string;
  question: string;
  status: "running" | "completed" | "failed";
  steps: AgentStep[];
  summary: string;
  cause: string;
  evidence: string[];
  policyId: string | null;
  recommendation: string;
  uncertainty: string;
  requiresApproval: boolean;
  createdAt: string;
  duration: number;
}

export interface ApprovalRequest {
  id: string;
  transactionId: string;
  action: string;
  reason: string;
  evidence: string[];
  policyId: string | null;
  reasoning: string;
  status: "PENDING" | "APPROVED" | "REJECTED" | "MORE_INFO";
  createdAt: string;
  decidedAt?: string;
  note?: string;
}

export interface PolicyDocument {
  id: string;
  name: string;
  type: string;
  uploadedAt: string;
  status: "PROCESSING" | "READY" | "FAILED";
  chunks: number;
  indexed: boolean;
  content: string;
}

export interface AuditEvent {
  id: string;
  transactionId: string;
  action: string;
  actor: string;
  timestamp: string;
  detail: string;
}

export interface Dispute {
  id: string;
  transactionId: string;
  reason: string;
  status: "OPEN" | "IN_REVIEW" | "RESOLVED";
  createdAt: string;
  note: string;
}

export interface Settings {
  theme: "light" | "dark";
  notifications: boolean;
  simulateFailure: boolean;
}

export interface AppData {
  version: number;
  transactions: Transaction[];
  investigations: Investigation[];
  approvals: ApprovalRequest[];
  documents: PolicyDocument[];
  audit: AuditEvent[];
  disputes: Dispute[];
  settings: Settings;
}

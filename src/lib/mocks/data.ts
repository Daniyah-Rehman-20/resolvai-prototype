import type {
  AppData,
  Investigation,
  PaymentMethod,
  PaymentStatus,
  Transaction,
} from "@/lib/types";
const methods: PaymentMethod[] = ["CREDIT_CARD", "UPI", "DEBIT_CARD", "CASH"];
const statuses: PaymentStatus[] = [
  "FAILED",
  "REFUND_PENDING",
  "PENDING",
  "DISPUTED",
  "SUCCESS",
  "SUCCESS",
  "SUCCESS",
  "REFUNDED",
  "SUCCESS",
  "SUCCESS",
  "PENDING",
  "SUCCESS",
];
const names = [
  "Aarav Mehta",
  "Isha Kapoor",
  "Kabir Shah",
  "Meera Rao",
  "Rohan Sen",
  "Anaya Das",
  "Vihaan Jain",
  "Sara Ali",
];
const issues: Record<PaymentStatus, string> = {
  SUCCESS: "Payment completed",
  FAILED: "Payment deducted, order failed",
  PENDING: "Settlement confirmation pending",
  REFUND_PENDING: "Duplicate payment refund",
  REFUNDED: "Refund completed",
  DISPUTED: "Merchant receipt mismatch",
  PAYMENT_FAILED: "Payment failed",
  RECONCILIATION_REQUIRED: "Reconciliation required",
};
export const transactions: Transaction[] = Array.from(
  { length: 48 },
  (_, i) => {
    const status = statuses[i % statuses.length];
    const method = methods[i % 4];
    const success = status === "SUCCESS";
    const cash = method === "CASH";
    return {
      id: `TXN-${10001 + i}`,
      orderId: `ORD-${501 + i}`,
      customer: {
        id: `USER-${101 + i}`,
        name: names[i % names.length],
        email: `user${101 + i}@example.test`,
      },
      method,
      amount: [2000, 1499, 849, 4200, 1299, 650, 3200, 999][i % 8],
      status,
      bank: cash
        ? "NOT_APPLICABLE"
        : status === "REFUNDED"
          ? "CREDITED"
          : "DEBITED",
      gateway: cash
        ? "NOT_APPLICABLE"
        : status === "PENDING"
          ? "PENDING"
          : "SUCCESS",
      merchant: success || status === "REFUNDED" ? "RECEIVED" : "NOT_RECEIVED",
      order: success
        ? "CONFIRMED"
        : status === "REFUNDED"
          ? "CANCELLED"
          : "PAYMENT_FAILED",
      createdAt: new Date(
        Date.UTC(2026, 8, 21 - Math.floor(i / 7), 14 - (i % 7), 12 + (i % 40)),
      ).toISOString(),
      issue:
        cash && !success && status !== "REFUNDED"
          ? "Cash collection not reflected"
          : issues[status],
      maskedInstrument: cash
        ? "Cash on delivery"
        : method === "UPI"
          ? "u***@demo"
          : "•••• •••• •••• 4242",
    };
  },
);
export const agentDefinitions = [
  ["Supervisor", "Understanding issue"],
  ["Transaction Agent", "Checking transaction"],
  ["Gateway Agent", "Checking gateway"],
  ["Merchant Agent", "Checking merchant"],
  ["RAG Agent", "Retrieving payment policies"],
  ["Resolution Agent", "Analyzing evidence"],
  ["Supervisor", "Generating recommendation"],
];
const policyNames = [
  "Credit Card Failure Policy",
  "Debit Card Payment Policy",
  "UPI Pending Payment Policy",
  "Duplicate Payment Policy",
  "Refund Policy",
  "Chargeback Policy",
  "Merchant Reconciliation Policy",
  "Cash on Delivery Policy",
];
const policyContents = [
  "Demo policy: When a card debit and an unsuccessful order coexist, reconcile gateway and merchant evidence first. A refund proposal requires a human decision. Do not retry the charge automatically.",
  "Demo policy: Compare bank debit, gateway receipt, and merchant acknowledgment. Escalate inconsistent evidence for manual review before proposing a reversal.",
  "Demo policy: A pending UPI status does not establish failure. Request a settlement check and wait for confirmed gateway and merchant evidence. Never request a UPI PIN.",
  "Demo policy: Verify that two distinct successful debits refer to the same order before proposing a duplicate-payment refund. A reviewer must approve any simulated refund.",
  "Demo policy: Confirm transaction identity, original debit, and any existing refund before proposing a new refund. Human approval is required. Timeframes here are illustrative, not banking guarantees.",
  "Demo policy: Gather transaction and merchant evidence before opening a dispute. A human must authorize the proposed case. This prototype does not submit chargebacks.",
  "Demo policy: Reconcile merchant acknowledgment with gateway settlement evidence. A missing receipt may reflect a delayed callback; treat this as a hypothesis until verified.",
  "Demo policy: Match delivery and collection records to the order. Card gateway and bank states are not applicable to cash. Escalate missing collection evidence to operations.",
];
export const seed: AppData = {
  version: 2,
  transactions,
  investigations: [],
  documents: policyNames.map((name, i) => ({
    id: `POL-${i + 1}`,
    name,
    type: "PDF",
    uploadedAt: "2026-09-18T09:00:00.000Z",
    status: "READY",
    chunks: 8 + i * 3,
    indexed: true,
    content: policyContents[i],
  })),
  approvals: [0, 1, 3, 10].map((idx, i) => ({
    id: `APR-${201 + i}`,
    transactionId: transactions[idx].id,
    action: [
      "Initiate refund",
      "Initiate refund",
      "Create dispute",
      "Escalate payment",
    ][i],
    reason: transactions[idx].issue,
    evidence: [
      `Bank: ${transactions[idx].bank}`,
      `Gateway: ${transactions[idx].gateway}`,
      `Merchant: ${transactions[idx].merchant}`,
    ],
    policyId: `POL-${[1, 4, 8, 3][i]}`,
    reasoning:
      "The recorded payment states require reconciliation. Review the available evidence before authorizing the proposed simulated action.",
    status: "PENDING",
    createdAt: "2026-09-21T14:30:00.000Z",
  })),
  audit: [
    {
      id: "AUD-SEED",
      transactionId: "TXN-10001",
      action: "Case opened",
      actor: "Supervisor",
      timestamp: "2026-09-21T14:15:00.000Z",
      detail: "Payment/order state mismatch detected in demo data.",
    },
  ],
  disputes: [3, 15, 27, 39].map((idx, i) => ({
    id: `DSP-${301 + i}`,
    transactionId: transactions[idx].id,
    reason: transactions[idx].issue,
    status: i === 0 ? "IN_REVIEW" : "OPEN",
    createdAt: transactions[idx].createdAt,
    note: "Awaiting merchant reconciliation evidence.",
  })),
  settings: { theme: "light", notifications: true, simulateFailure: false },
};
// Historical simulated traces supply an initial operational view, not business claims.
seed.investigations = [0, 4, 5, 2].map((idx, i): Investigation => ({
  id: `INV-${401 + i}`,
  transactionId: transactions[idx].id,
  question: "Review payment states",
  status: "completed",
  steps: agentDefinitions.map(([agent, action], j) => ({
    id: `STEP-${j}`,
    agent,
    action,
    status: "completed",
    duration: 800 + j * 120,
    timestamp: "2026-09-21T14:20:00.000Z",
  })),
  summary: transactions[idx].issue,
  cause:
    idx === 4 || idx === 5
      ? "All recorded payment states agree."
      : "Missing or delayed merchant acknowledgment is a possible cause.",
  evidence: [
    `Gateway: ${transactions[idx].gateway}`,
    `Merchant: ${transactions[idx].merchant}`,
  ],
  policyId: "POL-7",
  recommendation:
    idx === 4 || idx === 5
      ? "No further action required."
      : "Request reconciliation and human review.",
  uncertainty:
    "Based only on fictional records. No external payment provider was checked.",
  requiresApproval: idx !== 4 && idx !== 5,
  createdAt: "2026-09-21T14:20:00.000Z",
  duration: 5600 + i * 700,
}));

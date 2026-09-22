import { seed, agentDefinitions } from "@/lib/mocks/data";
import type {
  AppData,
  ApprovalRequest,
  Investigation,
  Settings,
  Dispute,
} from "@/lib/types";
const KEY = "payresolve-demo-v2";
const pause = (ms = 180) => new Promise((resolve) => setTimeout(resolve, ms));
let memory: AppData | null = null;
function read(): AppData {
  if (memory) return structuredClone(memory);
  if (typeof window !== "undefined") {
    const raw = localStorage.getItem(KEY);
    if (raw) {
      try {
        const parsed = JSON.parse(raw);
        if (
          parsed.version === 2 &&
          Array.isArray(parsed.transactions) &&
          Array.isArray(parsed.approvals) &&
          Array.isArray(parsed.documents) &&
          Array.isArray(parsed.investigations) &&
          Array.isArray(parsed.audit) &&
          Array.isArray(parsed.disputes) &&
          parsed.settings
        ) {
          memory = parsed;
          return structuredClone(parsed);
        }
      } catch {
        /* Recover malformed local demo state from fixtures. */
      }
    }
  }
  return structuredClone(seed);
}
function write(data: AppData) {
  localStorage.setItem(KEY, JSON.stringify(data));
  memory = structuredClone(data);
}
const id = (prefix: string) => `${prefix}-${crypto.randomUUID().slice(0, 8)}`;
function audit(
  data: AppData,
  transactionId: string,
  action: string,
  detail: string,
  actor = "Demo reviewer",
) {
  data.audit.unshift({
    id: id("AUD"),
    transactionId,
    action,
    detail,
    actor,
    timestamp: new Date().toISOString(),
  });
}
export async function getWorkspace(): Promise<AppData> {
  await pause();
  return read();
}
export async function getTransactions() {
  return (await getWorkspace()).transactions;
}
export async function getTransaction(transactionId: string) {
  return (await getTransactions()).find((t) => t.id === transactionId);
}
export async function getInvestigation(investigationId: string) {
  return (await getWorkspace()).investigations.find(
    (i) => i.id === investigationId,
  );
}
export async function getApprovals() {
  return (await getWorkspace()).approvals;
}
export async function getKnowledgeDocuments() {
  return (await getWorkspace()).documents;
}
export async function startInvestigation(
  transactionId: string,
  question: string,
  onUpdate: (value: Investigation) => void,
) {
  const initial = read();
  const tx = initial.transactions.find((t) => t.id === transactionId);
  if (!tx) throw new Error("Transaction not found.");
  const cash = tx.method === "CASH";
  const good = tx.status === "SUCCESS" || tx.status === "REFUNDED";
  const policyId = cash ? "POL-8" : tx.method === "UPI" ? "POL-3" : "POL-7";
  const investigation: Investigation = {
    id: id("INV"),
    transactionId,
    question,
    status: "running",
    steps: agentDefinitions.map(([agent, action], j) => ({
      id: `STEP-${j}`,
      agent,
      action: cash && j === 2 ? "Checking collection record" : action,
      status: "waiting",
      duration: 0,
      timestamp: "",
    })),
    summary: "",
    cause: "",
    evidence: [],
    policyId,
    recommendation: "",
    uncertainty: "",
    requiresApproval: !good,
    createdAt: new Date().toISOString(),
    duration: 0,
  };
  const started = Date.now();
  onUpdate(structuredClone(investigation));
  for (let j = 0; j < investigation.steps.length; j++) {
    const step = investigation.steps[j];
    step.status = "running";
    step.timestamp = new Date().toISOString();
    onUpdate(structuredClone(investigation));
    await pause(450);
    if (initial.settings.simulateFailure && j === 2) {
      step.status = "failed";
      investigation.status = "failed";
      investigation.summary = "The simulated evidence source is unavailable.";
      investigation.duration = Date.now() - started;
      const data = read();
      data.investigations.unshift(investigation);
      audit(
        data,
        transactionId,
        "Investigation failed",
        "Simulated evidence-source failure.",
        "Gateway Agent",
      );
      write(data);
      onUpdate(structuredClone(investigation));
      return investigation;
    }
    step.status = "completed";
    step.duration = 450;
    onUpdate(structuredClone(investigation));
  }
  investigation.status = "completed";
  investigation.duration = Date.now() - started;
  investigation.summary = tx.issue;
  investigation.cause = good
    ? "The recorded outcome is consistent; no unresolved state mismatch was found."
    : cash
      ? "Collection evidence may be missing from the order record."
      : tx.status === "PENDING"
        ? "The gateway has not yet confirmed settlement in the demo record."
        : "A delayed or unsuccessful merchant acknowledgment may explain the mismatch.";
  investigation.evidence = [
    `${tx.id} · ${tx.orderId}`,
    `Bank: ${tx.bank}`,
    `Gateway: ${tx.gateway}`,
    `Merchant: ${tx.merchant}`,
    `Order: ${tx.order}`,
  ];
  investigation.recommendation = good
    ? "No further action required."
    : cash || tx.status === "PENDING" || tx.status === "DISPUTED"
      ? "Escalate payment"
      : "Initiate refund";
  investigation.uncertainty =
    "Illustrative recommendation from fixed demo rules, not a live LLM. No bank or gateway was contacted. A reviewer must verify source evidence.";
  const data = read();
  data.investigations.unshift(investigation);
  if (
    !good &&
    !data.approvals.some(
      (a) =>
        a.transactionId === transactionId &&
        (a.status === "PENDING" || a.status === "MORE_INFO"),
    )
  )
    data.approvals.unshift({
      id: id("APR"),
      transactionId,
      action: investigation.recommendation,
      reason: investigation.summary,
      evidence: investigation.evidence,
      policyId,
      reasoning: investigation.cause,
      status: "PENDING",
      createdAt: new Date().toISOString(),
    });
  audit(
    data,
    transactionId,
    "Investigation completed",
    investigation.recommendation,
    "Supervisor",
  );
  write(data);
  onUpdate(structuredClone(investigation));
  return investigation;
}
export async function decideApproval(
  approvalId: string,
  decision: "APPROVED" | "REJECTED" | "MORE_INFO",
  note: string,
) {
  await pause();
  const data = read();
  const approval = data.approvals.find((a) => a.id === approvalId);
  if (!approval) throw new Error("Approval not found.");
  if (!["PENDING", "MORE_INFO"].includes(approval.status))
    throw new Error("This request has already been decided.");
  if (!note.trim()) throw new Error("Add a review note before continuing.");
  approval.status = decision;
  approval.note = note.trim();
  approval.decidedAt = new Date().toISOString();
  const tx = data.transactions.find((t) => t.id === approval.transactionId)!;
  if (decision === "APPROVED") {
    if (approval.action === "Initiate refund") tx.status = "REFUND_PENDING";
    if (approval.action === "Create dispute") {
      tx.status = "DISPUTED";
      if (
        !data.disputes.some(
          (d) => d.transactionId === tx.id && d.status !== "RESOLVED",
        )
      )
        data.disputes.unshift({
          id: id("DSP"),
          transactionId: tx.id,
          reason: approval.reason,
          status: "OPEN",
          createdAt: new Date().toISOString(),
          note,
        });
    }
  }
  audit(
    data,
    approval.transactionId,
    `${approval.action}: ${decision}`,
    `${note.trim()} — local simulation only`,
  );
  write(data);
}
export const approveAction = (id: string, note: string) =>
  decideApproval(id, "APPROVED", note);
export const rejectAction = (id: string, note: string) =>
  decideApproval(id, "REJECTED", note);
export async function uploadDocument(file: File) {
  if (!/\.(pdf|txt|md)$/i.test(file.name))
    throw new Error("Choose a PDF, TXT, or Markdown file.");
  if (!file.size || file.size > 10 * 1024 * 1024)
    throw new Error("Choose a nonempty file up to 10 MB.");
  const data = read();
  const docId = id("POL");
  data.documents.unshift({
    id: docId,
    name: file.name,
    type: file.name.split(".").pop()!.toUpperCase(),
    uploadedAt: new Date().toISOString(),
    status: "PROCESSING",
    chunks: 0,
    indexed: false,
    content:
      "Simulated upload. File contents are not extracted, indexed, or sent to a server in this frontend.",
  });
  write(data);
  return docId;
}
export async function finishUpload(docId: string) {
  await pause(1200);
  const data = read();
  const doc = data.documents.find((d) => d.id === docId);
  if (doc) {
    doc.status = data.settings.simulateFailure ? "FAILED" : "READY";
    doc.indexed = doc.status === "READY";
    doc.chunks = doc.indexed ? 12 : 0;
    write(data);
  }
}
export async function updateDispute(
  disputeId: string,
  status: Dispute["status"],
  note: string,
) {
  await pause();
  if (!note.trim()) throw new Error("Add a case note.");
  const data = read();
  const dispute = data.disputes.find((d) => d.id === disputeId);
  if (!dispute) throw new Error("Dispute not found.");
  dispute.status = status;
  dispute.note = note;
  audit(data, dispute.transactionId, `Dispute ${status}`, note);
  write(data);
}
export async function saveSettings(settings: Settings) {
  const data = read();
  data.settings = settings;
  write(data);
}
export async function resetDemo() {
  write(structuredClone(seed));
}
export type { ApprovalRequest };

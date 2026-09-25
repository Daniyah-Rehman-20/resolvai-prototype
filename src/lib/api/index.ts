import type {
  AppData,
  ApprovalRequest,
  AuditEvent,
  Dispute,
  Investigation,
  PolicyDocument,
  Settings,
  Transaction,
} from "@/lib/types";

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const SETTINGS_KEY = "payresolve-settings-v1";
const DEMO_TOKEN = process.env.NEXT_PUBLIC_DEMO_TOKEN || "payresolve-demo-token";
const DEMO_ROLE = process.env.NEXT_PUBLIC_DEMO_ROLE || "approver";
const DEFAULT_SETTINGS: Settings = {
  theme: "light",
  notifications: true,
  simulateFailure: false,
};

function readSettings(): Settings {
  if (typeof window === "undefined") return DEFAULT_SETTINGS;
  const raw = localStorage.getItem(SETTINGS_KEY);
  if (!raw) return DEFAULT_SETTINGS;
  try {
    return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) };
  } catch {
    return DEFAULT_SETTINGS;
  }
}

function writeSettings(settings: Settings) {
  if (typeof window !== "undefined") {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
  }
}

async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  // Demo-only identity bridge. Replace with an OIDC/JWT session provider before real deployment.
  headers.set("Authorization", `Bearer ${DEMO_TOKEN}`);
  headers.set("X-Demo-Role", DEMO_ROLE);
  headers.set("X-Demo-User", "payresolve-ui");

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    let message = `Backend request failed (${response.status})`;
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") message = body.detail;
      else if (body?.error?.message) message = body.error.message;
    } catch {
      // Keep the HTTP status message when the response is not JSON.
    }
    throw new Error(message);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function getWorkspace(): Promise<AppData> {
  const [
    transactions,
    investigations,
    approvals,
    documents,
    disputes,
    audit,
  ] = await Promise.all([
    api<Transaction[]>("/transactions?page_size=100"),
    api<Investigation[]>("/investigations"),
    api<ApprovalRequest[]>("/approvals"),
    api<PolicyDocument[]>("/documents"),
    api<Dispute[]>("/disputes"),
    api<AuditEvent[]>("/audit"),
  ]);

  return {
    version: 3,
    transactions,
    investigations,
    approvals,
    documents,
    audit,
    disputes,
    settings: readSettings(),
  };
}

export async function getTransactions() {
  return api<Transaction[]>("/transactions?page_size=100");
}

export async function getTransaction(transactionId: string) {
  return api<Transaction>(`/transactions/${encodeURIComponent(transactionId)}`);
}

export async function getInvestigation(investigationId: string) {
  return api<Investigation>(
    `/investigations/${encodeURIComponent(investigationId)}`,
  );
}

export async function getApprovals() {
  return api<ApprovalRequest[]>("/approvals");
}

export async function getKnowledgeDocuments() {
  return api<PolicyDocument[]>("/documents");
}

export async function startInvestigation(
  transactionId: string,
  question: string,
  onUpdate: (value: Investigation) => void,
) {
  if (readSettings().simulateFailure) {
    const failed: Investigation = {
      id: "INV-SIMULATED",
      transactionId,
      question,
      status: "failed",
      steps: [
        {
          id: "STEP-SIMULATED",
          agent: "Evidence Source",
          action: "Fetch payment evidence",
          status: "failed",
          duration: 0,
          timestamp: new Date().toISOString(),
        },
      ],
      summary: "The simulated evidence source is unavailable.",
      cause: "Failure simulation is enabled in Settings.",
      evidence: [],
      policyId: null,
      recommendation: "",
      uncertainty: "Local failure simulation; no backend action was executed.",
      requiresApproval: false,
      createdAt: new Date().toISOString(),
      duration: 0,
    };
    onUpdate(failed);
    return failed;
  }

  const result = await api<Investigation>("/investigations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      transaction_id: transactionId,
      question,
    }),
  });
  onUpdate(result);
  return result;
}

export async function decideApproval(
  approvalId: string,
  decision: "APPROVED" | "REJECTED" | "MORE_INFO",
  note: string,
) {
  if (!note.trim()) throw new Error("Add a review note before continuing.");
  const endpoint =
    decision === "APPROVED"
      ? "approve"
      : decision === "REJECTED"
        ? "reject"
        : "request-information";

  return api<ApprovalRequest>(
    `/approvals/${encodeURIComponent(approvalId)}/${endpoint}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ note: note.trim() }),
    },
  );
}

export const approveAction = (id: string, note: string) =>
  decideApproval(id, "APPROVED", note);

export const rejectAction = (id: string, note: string) =>
  decideApproval(id, "REJECTED", note);

export async function uploadDocument(file: File) {
  const form = new FormData();
  form.append("file", file);
  const document = await api<PolicyDocument>("/documents", {
    method: "POST",
    body: form,
  });
  return document.id;
}

export async function finishUpload(docId: string) {
  return api<PolicyDocument>(
    `/documents/${encodeURIComponent(docId)}/index`,
    { method: "POST" },
  );
}

export async function updateDispute(
  disputeId: string,
  status: Dispute["status"],
  note: string,
) {
  if (!note.trim()) throw new Error("Add a case note.");
  return api<Dispute>(`/disputes/${encodeURIComponent(disputeId)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status, note: note.trim() }),
  });
}

export async function saveSettings(settings: Settings) {
  writeSettings(settings);
}

export async function resetDemo() {
  await api<{ ok: boolean }>("/demo/reset", { method: "POST" });
  if (typeof window !== "undefined") localStorage.removeItem(SETTINGS_KEY);
}

export type { ApprovalRequest };

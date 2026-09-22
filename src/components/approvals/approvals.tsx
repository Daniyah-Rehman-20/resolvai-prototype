"use client";
import { useState } from "react";
import Link from "next/link";
import {
  ShieldCheck,
  Check,
  X,
  MessageSquareMore,
  FileText,
} from "lucide-react";
import { useWorkspace } from "@/components/layout/workspace";
import { PageTitle, Badge, Modal, Empty, Panel } from "@/components/common/ui";
import { decideApproval } from "@/lib/api";
import type { ApprovalRequest } from "@/lib/types";
import { dateTime, money, label } from "@/lib/utils";
export function Approvals() {
  const { data, refresh, notify } = useWorkspace();
  const [tab, setTab] = useState("PENDING");
  const [decision, setDecision] = useState<{
    approval: ApprovalRequest;
    status: "APPROVED" | "REJECTED" | "MORE_INFO";
  } | null>(null);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const filtered = data.approvals.filter(
    (a) => tab === "ALL" || a.status === tab,
  );
  async function confirm() {
    if (!decision) return;
    setBusy(true);
    setError("");
    try {
      await decideApproval(decision.approval.id, decision.status, note);
      await refresh();
      setDecision(null);
      notify(
        `Decision saved: ${label(decision.status)}. Audit history updated.`,
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="HUMAN-IN-THE-LOOP"
        title="Approval Queue"
        description="AI proposes. You review the evidence and authorize the next step."
      >
        <span className="demo-tag">
          <ShieldCheck size={16} />
          Local simulation only
        </span>
      </PageTitle>
      <div className="tabs" role="tablist" aria-label="Approval status">
        {["PENDING", "MORE_INFO", "APPROVED", "REJECTED", "ALL"].map((s) => (
          <button
            role="tab"
            aria-selected={tab === s}
            onClick={() => setTab(s)}
            key={s}
          >
            {s === "ALL" ? "All decisions" : label(s)}{" "}
            <span>
              {
                data.approvals.filter((a) => s === "ALL" || a.status === s)
                  .length
              }
            </span>
          </button>
        ))}
      </div>
      <div className="approval-grid">
        {filtered.map((a) => {
          const tx = data.transactions.find((t) => t.id === a.transactionId)!;
          const policy = data.documents.find((d) => d.id === a.policyId);
          return (
            <section className="panel approval-card" key={a.id}>
              <div className="approval-card-top">
                <span className="item-icon">
                  <ShieldCheck size={22} />
                </span>
                <div>
                  <small>
                    {a.id} · {dateTime(a.createdAt)}
                  </small>
                  <h2>{a.action}</h2>
                </div>
                <Badge value={a.status} />
              </div>
              <div className="approval-transaction">
                <div>
                  <Link href={`/transactions/${tx.id}`}>{tx.id} ↗</Link>
                  <p>
                    {tx.customer.name} · {label(tx.method)}
                  </p>
                </div>
                <div>
                  <strong>{money(tx.amount)}</strong>
                  <Badge value={tx.status} />
                </div>
              </div>
              <h3>Why this action?</h3>
              <p>{a.reason}</p>
              <div className="evidence-chips">
                {a.evidence.map((e) => (
                  <span key={e}>{e}</span>
                ))}
              </div>
              <details>
                <summary>
                  <FileText size={15} />
                  Policy & reasoning summary
                </summary>
                <h3>{policy?.name}</h3>
                <p>{policy?.content}</p>
                <p>{a.reasoning}</p>
              </details>
              {a.note && (
                <div className="review-note">
                  <strong>Reviewer note</strong>
                  <p>{a.note}</p>
                  <small>{a.decidedAt && dateTime(a.decidedAt)}</small>
                </div>
              )}
              {["PENDING", "MORE_INFO"].includes(a.status) && (
                <div className="approval-actions">
                  <button
                    className="button"
                    onClick={() => {
                      setDecision({ approval: a, status: "APPROVED" });
                      setNote("");
                      setError("");
                    }}
                  >
                    <Check size={16} />
                    Approve
                  </button>
                  <button
                    className="button secondary danger"
                    onClick={() => {
                      setDecision({ approval: a, status: "REJECTED" });
                      setNote("");
                      setError("");
                    }}
                  >
                    <X size={16} />
                    Reject
                  </button>
                  <button
                    className="button ghost"
                    onClick={() => {
                      setDecision({ approval: a, status: "MORE_INFO" });
                      setNote("");
                      setError("");
                    }}
                  >
                    <MessageSquareMore size={16} />
                    More info
                  </button>
                </div>
              )}
            </section>
          );
        })}
      </div>
      {!filtered.length && (
        <Panel title="No requests in this view">
          <Empty
            title="You're all caught up"
            detail="Try another status or start a new investigation."
          />
        </Panel>
      )}
      {decision && (
        <Modal
          title={`Confirm: ${label(decision.status)}`}
          onClose={() => {
            if (!busy) setDecision(null);
          }}
        >
          <p>
            You are reviewing <strong>{decision.approval.action}</strong> for{" "}
            <strong>{decision.approval.transactionId}</strong>.
          </p>
          <div className="callout">
            <ShieldCheck size={20} />
            <p>
              This updates local demo records and creates an audit event. No
              money will move.
            </p>
          </div>
          <label className="field">
            {decision.status === "MORE_INFO"
              ? "What additional evidence do you need?"
              : "Review note (required)"}
            <textarea
              autoFocus
              rows={3}
              maxLength={1000}
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </label>
          {error && (
            <p className="error-text" role="alert">
              {error}
            </p>
          )}
          <div className="modal-actions">
            <button
              className="button secondary"
              disabled={busy}
              onClick={() => setDecision(null)}
            >
              Cancel
            </button>
            <button
              className="button"
              disabled={busy || !note.trim()}
              onClick={confirm}
            >
              {busy ? "Saving…" : "Confirm decision"}
            </button>
          </div>
        </Modal>
      )}
    </>
  );
}

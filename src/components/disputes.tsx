"use client";
import { useState } from "react";
import Link from "next/link";
import { Flag } from "lucide-react";
import { useWorkspace } from "@/components/layout/workspace";
import { PageTitle, Panel, Badge, Modal, Empty } from "@/components/common/ui";
import { updateDispute } from "@/lib/api";
import type { Dispute } from "@/lib/types";
import { money, dateTime } from "@/lib/utils";
export function Disputes() {
  const { data, refresh, notify } = useWorkspace();
  const [filter, setFilter] = useState("ALL");
  const [selected, setSelected] = useState<Dispute | null>(null);
  const [status, setStatus] = useState<Dispute["status"]>("IN_REVIEW");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const rows = data.disputes.filter(
    (d) => filter === "ALL" || d.status === filter,
  );
  async function save() {
    if (!selected) return;
    setBusy(true);
    try {
      await updateDispute(selected.id, status, note);
      await refresh();
      setSelected(null);
      notify("Dispute updated. A local audit event was recorded.");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="CASE MANAGEMENT"
        title="Disputes"
        description="Keep evidence, ownership, and case decisions together."
      >
        <select
          aria-label="Dispute status"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        >
          <option value="ALL">All cases</option>
          <option value="OPEN">Open</option>
          <option value="IN_REVIEW">In review</option>
          <option value="RESOLVED">Resolved</option>
        </select>
      </PageTitle>
      <Panel
        title="Dispute cases"
        subtitle="Case updates are local; resolving a case does not move funds or change payment status"
      >
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Case</th>
                <th>Transaction</th>
                <th>Customer</th>
                <th>Amount</th>
                <th>Reason</th>
                <th>Status</th>
                <th>Created</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((d) => {
                const tx = data.transactions.find(
                  (t) => t.id === d.transactionId,
                )!;
                return (
                  <tr key={d.id}>
                    <td>
                      <span className="inline-icon">
                        <Flag size={16} />
                        {d.id}
                      </span>
                    </td>
                    <td>
                      <Link
                        className="text-link"
                        href={`/transactions/${d.transactionId}`}
                      >
                        {d.transactionId}
                      </Link>
                    </td>
                    <td>{tx.customer.name}</td>
                    <td>{money(tx.amount)}</td>
                    <td className="wrap">{d.reason}</td>
                    <td>
                      <Badge value={d.status} />
                    </td>
                    <td>{dateTime(d.createdAt)}</td>
                    <td>
                      <button
                        className="button secondary"
                        onClick={() => {
                          setSelected(d);
                          setStatus(d.status);
                          setNote(d.note);
                          setError("");
                        }}
                      >
                        Review case
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {!rows.length && (
          <Empty
            title="No cases in this view"
            detail="Choose a different status to see other disputes."
          />
        )}
      </Panel>
      {selected && (
        <Modal
          title={`Review ${selected.id}`}
          onClose={() => {
            if (!busy) setSelected(null);
          }}
        >
          <p>{selected.reason}</p>
          <label className="field">
            Case status
            <select
              aria-label="Case status"
              value={status}
              onChange={(e) => setStatus(e.target.value as Dispute["status"])}
            >
              <option value="OPEN">Open</option>
              <option value="IN_REVIEW">In review</option>
              <option value="RESOLVED">Resolved</option>
            </select>
          </label>
          <label className="field">
            Case note
            <textarea
              aria-label="Case note"
              rows={3}
              maxLength={1000}
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </label>
          {error && (
            <p role="alert" className="error-text">
              {error}
            </p>
          )}
          <div className="modal-actions">
            <button
              className="button secondary"
              disabled={busy}
              onClick={() => setSelected(null)}
            >
              Cancel
            </button>
            <button
              className="button"
              disabled={busy || !note.trim()}
              onClick={save}
            >
              {busy ? "Saving…" : "Confirm case update"}
            </button>
          </div>
        </Modal>
      )}
    </>
  );
}

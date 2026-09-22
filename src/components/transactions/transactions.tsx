"use client";
import { useState } from "react";
import Link from "next/link";
import {
  Search,
  ArrowUpDown,
  ArrowUpRight,
  ChevronLeft,
  ChevronRight,
  ArrowDown,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import { useWorkspace } from "@/components/layout/workspace";
import {
  Badge,
  Empty,
  Panel,
  PageTitle,
  MoreLink,
} from "@/components/common/ui";
import { dateTime, label, money } from "@/lib/utils";
export function Transactions({ initialQuery = "" }: { initialQuery?: string }) {
  const { data } = useWorkspace();
  const [query, setQuery] = useState(initialQuery);
  const [method, setMethod] = useState("ALL");
  const [status, setStatus] = useState("ALL");
  const [date, setDate] = useState("");
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState<"createdAt" | "amount" | "id">("createdAt");
  const [asc, setAsc] = useState(false);
  const filtered = data.transactions
    .filter(
      (t) =>
        `${t.id} ${t.orderId} ${t.customer.name} ${t.customer.id}`
          .toLowerCase()
          .includes(query.toLowerCase()) &&
        (method === "ALL" || t.method === method) &&
        (status === "ALL" || t.status === status) &&
        (!date || t.createdAt.slice(0, 10) === date),
    )
    .sort(
      (a, b) =>
        (sort === "amount"
          ? a.amount - b.amount
          : a[sort].localeCompare(b[sort])) * (asc ? 1 : -1),
    );
  const pages = Math.max(1, Math.ceil(filtered.length / 8));
  const current = Math.min(page, pages);
  const rows = filtered.slice((current - 1) * 8, current * 8);
  function toggleSort(value: typeof sort) {
    if (sort === value) setAsc(!asc);
    else {
      setSort(value);
      setAsc(false);
    }
    setPage(1);
  }
  return (
    <>
      <PageTitle
        eyebrow="PAYMENT RECORDS"
        title="Transactions"
        description="Trace every payment from the first debit to the final outcome."
      >
        <span className="date-pill">
          {data.transactions.length} demo transactions
        </span>
      </PageTitle>
      <section className="panel">
        <div className="filters">
          <div className="input-icon">
            <Search size={17} />
            <input
              aria-label="Search transactions"
              placeholder="Transaction, order, or customer"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setPage(1);
              }}
            />
          </div>
          <select
            aria-label="Payment method"
            value={method}
            onChange={(e) => {
              setMethod(e.target.value);
              setPage(1);
            }}
          >
            <option value="ALL">All payment methods</option>
            {["CREDIT_CARD", "DEBIT_CARD", "UPI", "CASH"].map((m) => (
              <option key={m}>{m}</option>
            ))}
          </select>
          <select
            aria-label="Payment status"
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
          >
            <option value="ALL">All statuses</option>
            {[
              "SUCCESS",
              "FAILED",
              "PENDING",
              "REFUND_PENDING",
              "REFUNDED",
              "DISPUTED",
            ].map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
          <input
            type="date"
            aria-label="Transaction date"
            value={date}
            onChange={(e) => {
              setDate(e.target.value);
              setPage(1);
            }}
          />
          <button
            className="button ghost"
            onClick={() => {
              setQuery("");
              setMethod("ALL");
              setStatus("ALL");
              setDate("");
              setPage(1);
            }}
          >
            Clear
          </button>
        </div>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th
                  aria-sort={
                    sort === "id" ? (asc ? "ascending" : "descending") : "none"
                  }
                >
                  <button onClick={() => toggleSort("id")}>
                    Transaction
                    <ArrowUpDown size={13} />
                  </button>
                </th>
                <th>Order</th>
                <th>Customer</th>
                <th>Method</th>
                <th
                  aria-sort={
                    sort === "amount"
                      ? asc
                        ? "ascending"
                        : "descending"
                      : "none"
                  }
                >
                  <button onClick={() => toggleSort("amount")}>
                    Amount
                    <ArrowUpDown size={13} />
                  </button>
                </th>
                <th>Gateway</th>
                <th>Bank</th>
                <th>Merchant</th>
                <th>Status</th>
                <th
                  aria-sort={
                    sort === "createdAt"
                      ? asc
                        ? "ascending"
                        : "descending"
                      : "none"
                  }
                >
                  <button onClick={() => toggleSort("createdAt")}>
                    Created
                    <ArrowUpDown size={13} />
                  </button>
                </th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((t) => (
                <tr key={t.id}>
                  <td>
                    <Link
                      className="transaction-link"
                      href={`/transactions/${t.id}`}
                    >
                      {t.id}
                    </Link>
                  </td>
                  <td className="mono">{t.orderId}</td>
                  <td>
                    <strong>{t.customer.name}</strong>
                    <small>{t.customer.id}</small>
                  </td>
                  <td>{label(t.method)}</td>
                  <td className="amount">{money(t.amount)}</td>
                  <td>
                    <Badge value={t.gateway} />
                  </td>
                  <td>
                    <Badge value={t.bank} />
                  </td>
                  <td>
                    <Badge value={t.merchant} />
                  </td>
                  <td>
                    <Badge value={t.status} />
                  </td>
                  <td>{dateTime(t.createdAt)}</td>
                  <td>
                    <Link
                      className="icon-button"
                      href={`/transactions/${t.id}`}
                      aria-label={`View ${t.id}`}
                    >
                      <ArrowUpRight size={17} />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!rows.length && (
          <Empty
            title="No transactions match"
            detail="Try a different search or clear your filters."
          />
        )}
        <div className="pagination">
          <span>
            {filtered.length ? (current - 1) * 8 + 1 : 0}–
            {Math.min(current * 8, filtered.length)} of {filtered.length}{" "}
            transactions
          </span>
          <div>
            <button
              className="icon-button"
              aria-label="Previous page"
              disabled={current === 1}
              onClick={() => setPage(current - 1)}
            >
              <ChevronLeft size={18} />
            </button>
            <span>
              Page {current} of {pages}
            </span>
            <button
              className="icon-button"
              aria-label="Next page"
              disabled={current === pages}
              onClick={() => setPage(current + 1)}
            >
              <ChevronRight size={18} />
            </button>
          </div>
        </div>
      </section>
    </>
  );
}
export function TransactionDetail({ id }: { id: string }) {
  const { data } = useWorkspace();
  const tx = data.transactions.find((t) => t.id === id);
  const [tab, setTab] = useState("Overview");
  if (!tx)
    return (
      <Empty
        title="Transaction not found"
        detail="Return to Transactions to choose an existing demo record."
      />
    );
  const investigation = data.investigations.find((i) => i.transactionId === id);
  const events = data.audit.filter((a) => a.transactionId === id);
  const mismatch = !["SUCCESS", "REFUNDED"].includes(tx.status);
  const policy = data.documents.find(
    (p) =>
      p.id ===
      (investigation?.policyId || (tx.method === "CASH" ? "POL-8" : "POL-7")),
  );
  return (
    <>
      <Link href="/transactions" className="back-link">
        ← All transactions
      </Link>
      <PageTitle
        eyebrow="TRANSACTION DETAILS"
        title={tx.id}
        description={`${tx.orderId} · ${dateTime(tx.createdAt)} IST`}
      >
        <Badge value={tx.status} />
        <Link className="button" href={`/investigator?transaction=${tx.id}`}>
          <Sparkles size={17} />
          Investigate payment
        </Link>
      </PageTitle>
      <div className="detail-summary">
        <div>
          <span>Amount</span>
          <strong>{money(tx.amount)}</strong>
        </div>
        <div>
          <span>Customer</span>
          <strong>{tx.customer.name}</strong>
          <small>{tx.customer.id}</small>
        </div>
        <div>
          <span>Payment method</span>
          <strong>{label(tx.method)}</strong>
          <small>{tx.maskedInstrument}</small>
        </div>
        <div>
          <span>Order reference</span>
          <strong>{tx.orderId}</strong>
          <small>{tx.customer.email}</small>
        </div>
      </div>
      <div className="tabs" role="tablist" aria-label="Transaction sections">
        {["Overview", "Investigation", "Audit log"].map((t) => (
          <button
            key={t}
            role="tab"
            aria-selected={tab === t}
            onClick={() => setTab(t)}
          >
            {t}
          </button>
        ))}
      </div>
      {tab === "Overview" && (
        <div className="grid-two detail-grid">
          <Panel
            title="Payment state"
            subtitle="Compare evidence across the payment lifecycle"
          >
            <div
              className={`state-notice ${mismatch ? "warning" : "positive"}`}
            >
              {mismatch ? (
                <AlertTriangle size={18} />
              ) : (
                <CheckCircle2 size={18} />
              )}
              <div>
                <strong>
                  {mismatch
                    ? "Payment states need reconciliation"
                    : "Recorded outcome is consistent"}
                </strong>
                <p>
                  {tx.method === "CASH"
                    ? "Cash records use collection and order evidence; bank and gateway are not applicable."
                    : mismatch
                      ? "A bank debit does not establish that an order was confirmed."
                      : "No outstanding mismatch is recorded for this transaction."}
                </p>
              </div>
            </div>
            <div className="payment-flow">
              {[
                ["Bank", tx.bank],
                ["Payment gateway", tx.gateway],
                ["Merchant", tx.merchant],
                ["Order system", tx.order],
              ].map(([name, state], i) => (
                <div key={name}>
                  <div className="state-row">
                    <span className="step-number">{i + 1}</span>
                    <strong>{name}</strong>
                    <Badge value={state} />
                  </div>
                  {i < 3 && <ArrowDown size={17} className="flow-arrow" />}
                </div>
              ))}
            </div>
          </Panel>
          <Panel
            title="Transaction timeline"
            subtitle="Recorded events and local workspace decisions"
          >
            <div className="timeline">
              <div>
                <span className="timeline-dot" />
                <strong>Payment record created</strong>
                <p>
                  {tx.orderId} · {label(tx.method)}
                </p>
                <small>{dateTime(tx.createdAt)}</small>
              </div>
              <div>
                <span className="timeline-dot" />
                <strong>{label(tx.status)}</strong>
                <p>{tx.issue}</p>
                <small>{dateTime(tx.createdAt)}</small>
              </div>
              {events
                .slice()
                .reverse()
                .map((e) => (
                  <div key={e.id}>
                    <span className="timeline-dot" />
                    <strong>{label(e.action)}</strong>
                    <p>{e.detail}</p>
                    <small>
                      {dateTime(e.timestamp)} · {e.actor}
                    </small>
                  </div>
                ))}
            </div>
          </Panel>
        </div>
      )}
      {tab === "Investigation" && (
        <div className="grid-two">
          <Panel
            title="AI investigation"
            subtitle="Rule-based simulation · recommendations require verification"
          >
            {investigation ? (
              <>
                <Badge value={investigation.status} />
                <h3>{investigation.summary}</h3>
                <p>{investigation.cause}</p>
                <div className="callout">
                  <strong>Recommended action</strong>
                  <p>{investigation.recommendation}</p>
                </div>
                <p className="subtle">{investigation.uncertainty}</p>
                <MoreLink href="/approvals">Review proposed actions</MoreLink>
              </>
            ) : (
              <Empty
                title="Ready to investigate"
                detail="Use Investigate payment to generate a simulated evidence summary."
              />
            )}
          </Panel>
          <Panel
            title="Evidence & retrieved policy"
            subtitle="Fictional sources for this demo"
          >
            <ul className="evidence-list">
              {(
                investigation?.evidence || [
                  `Bank: ${tx.bank}`,
                  `Gateway: ${tx.gateway}`,
                  `Merchant: ${tx.merchant}`,
                ]
              ).map((e) => (
                <li key={e}>
                  <CheckCircle2 size={16} />
                  {e}
                </li>
              ))}
            </ul>
            <h3>{policy?.name}</h3>
            <p>{policy?.content}</p>
            <MoreLink href="/knowledge">Browse policy documents</MoreLink>
            <h3>Agent activity</h3>
            {investigation?.steps.map((s) => (
              <div className="compact-row" key={s.id}>
                <span>{s.agent}</span>
                <Badge value={s.status} />
              </div>
            ))}
          </Panel>
        </div>
      )}
      {tab === "Audit log" && (
        <Panel
          title="Audit history"
          subtitle="Local reviewer decisions and agent events"
        >
          {events.length ? (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Actor</th>
                    <th>Action</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {events.map((e) => (
                    <tr key={e.id}>
                      <td>{dateTime(e.timestamp)}</td>
                      <td>{e.actor}</td>
                      <td>{e.action}</td>
                      <td className="wrap">{e.detail}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <Empty
              title="No audit events yet"
              detail="Investigations and approval decisions will be recorded here."
            />
          )}
        </Panel>
      )}
    </>
  );
}

"use client";
import Link from "next/link";
import {
  ArrowUpRight,
  ArrowLeftRight,
  CheckCheck,
  CircleAlert,
  Clock3,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { useWorkspace } from "@/components/layout/workspace";
import {
  PageTitle,
  Panel,
  Badge,
  MoreLink,
  Empty,
} from "@/components/common/ui";
import { dateTime, money, label, percent } from "@/lib/utils";
import type { Transaction } from "@/lib/types";
export function Trend({ transactions }: { transactions: Transaction[] }) {
  const days = Array.from(
    new Set(transactions.map((t) => t.createdAt.slice(0, 10))),
  ).sort();
  const series = days.map((day) => ({
    day,
    success: transactions.filter(
      (t) => t.createdAt.startsWith(day) && t.status === "SUCCESS",
    ).length,
    other: transactions.filter(
      (t) => t.createdAt.startsWith(day) && t.status !== "SUCCESS",
    ).length,
  }));
  const max = Math.max(1, ...series.map((s) => Math.max(s.success, s.other)));
  const x = (i: number) => 35 + (i * 530) / Math.max(1, series.length - 1);
  const y = (v: number) => 150 - (v / max) * 115;
  return (
    <>
      <div className="chart-legend">
        <span>
          <i className="dot teal" />
          Successful
        </span>
        <span>
          <i className="dot amber" />
          Other outcomes
        </span>
      </div>
      <svg
        viewBox="0 0 600 190"
        className="trend-chart"
        role="img"
        aria-label="Daily successful payments versus other outcomes in the transaction dataset"
      >
        {[0, 1, 2, 3].map((i) => (
          <g key={i}>
            <line
              x1="35"
              x2="575"
              y1={35 + (i * 115) / 3}
              y2={35 + (i * 115) / 3}
              className="chart-grid"
            />
            <text x="8" y={39 + (i * 115) / 3}>
              {Math.round(max - (i * max) / 3)}
            </text>
          </g>
        ))}
        <polyline
          points={series.map((s, i) => `${x(i)},${y(s.success)}`).join(" ")}
          fill="none"
          stroke="var(--accent)"
          strokeWidth="3"
          strokeLinejoin="round"
        />
        <polyline
          points={series.map((s, i) => `${x(i)},${y(s.other)}`).join(" ")}
          fill="none"
          stroke="#d69b46"
          strokeWidth="2"
          strokeDasharray="5 5"
        />
        {series.map((s, i) => (
          <g key={s.day}>
            <circle
              cx={x(i)}
              cy={y(s.success)}
              r="4"
              fill="var(--surface)"
              stroke="var(--accent)"
              strokeWidth="2"
            >
              <title>
                {s.day}: {s.success} successful, {s.other} other outcomes
              </title>
            </circle>
            <text x={x(i)} y="177" textAnchor="middle">
              {s.day.slice(-2)} Sep
            </text>
          </g>
        ))}
      </svg>
      <details className="chart-data">
        <summary>View chart data</summary>
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Success</th>
              <th>Other</th>
            </tr>
          </thead>
          <tbody>
            {series.map((s) => (
              <tr key={s.day}>
                <td>{s.day}</td>
                <td>{s.success}</td>
                <td>{s.other}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </>
  );
}
export function MethodBars({ transactions }: { transactions: Transaction[] }) {
  return (
    <div className="method-bars">
      {["CREDIT_CARD", "DEBIT_CARD", "UPI", "CASH"].map((m, i) => {
        const count = transactions.filter((t) => t.method === m).length;
        return (
          <div key={m}>
            <div className="bar-label">
              <span>{label(m)}</span>
              <strong>
                {count} <small>· {percent(count, transactions.length)}</small>
              </strong>
            </div>
            <div className="bar-track">
              <div
                className={`bar-fill color-${i}`}
                style={{ width: percent(count, transactions.length) }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
export function Dashboard() {
  const { data } = useWorkspace();
  const tx = data.transactions;
  const completed = data.investigations.filter((i) => i.status === "completed");
  const resolved = completed.filter((i) => !i.requiresApproval);
  const average = completed.length
    ? (
        completed.reduce((s, i) => s + i.duration, 0) /
        completed.length /
        1000
      ).toFixed(1) + "s"
    : "—";
  const waiting = data.approvals.filter((a) => a.status === "PENDING");
  const metrics = [
    [
      "Total transactions",
      tx.length,
      "Across all payment methods",
      ArrowLeftRight,
    ],
    [
      "Successful payments",
      tx.filter((t) => t.status === "SUCCESS").length,
      `${percent(tx.filter((t) => t.status === "SUCCESS").length, tx.length)} of transactions`,
      CheckCheck,
    ],
    [
      "Payment exceptions",
      tx.filter((t) =>
        ["FAILED", "PAYMENT_FAILED", "RECONCILIATION_REQUIRED"].includes(t.status),
      ).length,
      "Need investigation or reconciliation",
      CircleAlert,
    ],
    [
      "Pending payments",
      tx.filter((t) => t.status === "PENDING").length,
      "Awaiting confirmation",
      Clock3,
    ],
    ["Human approvals", waiting.length, "Ready for your review", ShieldCheck],
    [
      "AI-resolved cases",
      resolved.length,
      "Resolved · no action needed",
      Sparkles,
    ],
  ] as const;
  return (
    <>
      <PageTitle
        eyebrow="OPERATIONS OVERVIEW"
        title="Dashboard"
        description="A clear view of your payments. A faster path to resolution."
      >
        <span className="date-pill">Live payment operations</span>
      </PageTitle>
      <div className="review-banner">
        <div className="banner-icon">
          <ShieldCheck size={23} />
        </div>
        <div>
          <strong>
            {waiting.length
              ? `${waiting.length} decisions are waiting for you`
              : "You’re all caught up"}
          </strong>
          <p>Review the evidence. You make the final call.</p>
        </div>
        <Link href="/approvals" className="button">
          Review approvals
          <ArrowUpRight size={16} />
        </Link>
      </div>
      <Panel
        title="What PayResolve solves"
        subtitle="Three payment exceptions that normally require an operations team to inspect several systems"
        action={<MoreLink href="/transactions">Run a use case</MoreLink>}
      >
        <div className="issue-grid">
          <div>
            <span>Money deducted, order failed</span>
            <strong>RECONCILE</strong>
          </div>
          <div>
            <span>Payment stuck pending</span>
            <strong>WAIT & RECHECK</strong>
          </div>
          <div>
            <span>Customer charged twice</span>
            <strong>HUMAN-APPROVED REFUND</strong>
          </div>
        </div>
      </Panel>
      <div className="metrics">
        {metrics.map(([name, value, detail, Icon]) => (
          <div className="metric" key={name}>
            <div className="metric-label">
              {name}
              <Icon size={17} />
            </div>
            <strong>{value}</strong>
            <small>{detail}</small>
          </div>
        ))}
      </div>
      <div className="grid-two">
        <Panel
          title="Payment outcomes"
          subtitle="Daily transaction counts · current cohort"
          action={<span className="subtle">7 days</span>}
        >
          <Trend transactions={tx} />
        </Panel>
        <Panel
          title="Payment methods"
          subtitle="Distribution across the transaction dataset"
        >
          <MethodBars transactions={tx} />
          <div className="panel-foot">
            <strong>{money(tx.reduce((s, t) => s + t.amount, 0))}</strong>
            <span>Total transaction value</span>
          </div>
        </Panel>
      </div>
      <div className="grid-two">
        <Panel
          title="Recent investigations"
          subtitle={`Average investigation time ${average}`}
          action={<MoreLink href="/investigator" />}
        >
          <div className="activity-list">
            {data.investigations.slice(0, 4).map((i) => (
              <Link
                key={i.id}
                href={`/transactions/${i.transactionId}`}
                className="activity-item"
              >
                <span className="item-icon">
                  <Sparkles size={18} />
                </span>
                <div>
                  <strong>{i.transactionId}</strong>
                  <p>{i.summary || "Investigation running"}</p>
                </div>
                <Badge value={i.status} />
                <ArrowUpRight size={15} />
              </Link>
            ))}
          </div>
        </Panel>
        <Panel
          title="Awaiting human review"
          subtitle="AI recommendations, authorized by you"
          action={<MoreLink href="/approvals" />}
        >
          {waiting.length ? (
            waiting.slice(0, 3).map((a) => (
              <Link className="approval-preview" key={a.id} href="/approvals">
                <div>
                  <strong>{label(a.action)}</strong>
                  <p>
                    {a.transactionId} · {dateTime(a.createdAt)}
                  </p>
                </div>
                <span>
                  {money(tx.find((t) => t.id === a.transactionId)!.amount)}
                  <ArrowUpRight size={15} />
                </span>
              </Link>
            ))
          ) : (
            <Empty
              title="Queue cleared"
              detail="New proposals will appear after an investigation."
            />
          )}
        </Panel>
      </div>
      <Panel
        title="Issue categories"
        subtitle="Non-successful transactions grouped by recorded issue"
      >
        <div className="issue-grid">
          {Array.from(
            new Set(
              tx.filter((t) => t.status !== "SUCCESS").map((t) => t.issue),
            ),
          ).map((issue) => (
            <div key={issue}>
              <span>{issue}</span>
              <strong>{tx.filter((t) => t.issue === issue).length}</strong>
            </div>
          ))}
        </div>
      </Panel>
    </>
  );
}

"use client";
import { useWorkspace } from "@/components/layout/workspace";
import { PageTitle, Panel } from "@/components/common/ui";
import { Trend } from "@/components/dashboard/dashboard";
import { percent, label } from "@/lib/utils";
export function Analytics() {
  const { data } = useWorkspace();
  const tx = data.transactions;
  const complete = data.investigations.filter((i) => i.status === "completed");
  const resolved = complete.filter((i) => !i.requiresApproval);
  const stats = [
    [
      "Payment success rate",
      percent(tx.filter((t) => t.status === "SUCCESS").length, tx.length),
      "Successful / all transactions",
    ],
    [
      "Dispute rate",
      percent(tx.filter((t) => t.status === "DISPUTED").length, tx.length),
      "Currently disputed / all transactions",
    ],
    [
      "Refund rate",
      percent(tx.filter((t) => t.status === "REFUNDED").length, tx.length),
      "Refunded / all transactions",
    ],
    [
      "AI resolution rate",
      percent(resolved.length, complete.length),
      "No-action resolutions / completed runs",
    ],
    [
      "Human escalation rate",
      percent(
        complete.filter((i) => i.requiresApproval).length,
        complete.length,
      ),
      "Human review required / completed runs",
    ],
    [
      "Avg. investigation time",
      complete.length
        ? (
            complete.reduce((s, i) => s + i.duration, 0) /
            complete.length /
            1000
          ).toFixed(1) + "s"
        : "—",
      "Completed simulation runs",
    ],
    [
      "Avg. resolution time",
      resolved.length
        ? (
            resolved.reduce((s, i) => s + i.duration, 0) /
            resolved.length /
            1000
          ).toFixed(1) + "s"
        : "—",
      "Auto-resolved cases only; human cases excluded",
    ],
  ];
  const issues = Array.from(
    new Set(tx.filter((t) => t.status === "FAILED").map((t) => t.issue)),
  );
  return (
    <>
      <PageTitle
        eyebrow="OPERATIONAL INSIGHTS"
        title="Analytics"
        description="Understand payment outcomes and where human attention matters."
      />
      <div className="analytics-note">
        Metrics are calculated from the current fictional dataset. The
        transaction cohort is 15–21 September 2026; investigation metrics
        include new local runs.
      </div>
      <div className="metrics">
        {stats.map(([title, value, desc]) => (
          <div className="metric" key={title}>
            <span className="metric-label">{title}</span>
            <strong>{value}</strong>
            <small>{desc}</small>
          </div>
        ))}
      </div>
      <div className="grid-two">
        <Panel
          title="Payment outcomes"
          subtitle="Daily counts from the demo cohort"
        >
          <Trend transactions={tx} />
        </Panel>
        <Panel
          title="Top failure reasons"
          subtitle="Transactions currently marked failed"
        >
          <div className="method-bars">
            {issues.map((issue) => {
              const count = tx.filter(
                (t) => t.status === "FAILED" && t.issue === issue,
              ).length;
              return (
                <div key={issue}>
                  <div className="bar-label">
                    <span>{issue}</span>
                    <strong>{count}</strong>
                  </div>
                  <div className="bar-track">
                    <div
                      className="bar-fill"
                      style={{
                        width: percent(
                          count,
                          tx.filter((t) => t.status === "FAILED").length,
                        ),
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </Panel>
      </div>
      <Panel
        title="Performance by payment method"
        subtitle="Success and failure are mutually exclusive recorded statuses; other statuses are counted separately"
      >
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Payment method</th>
                <th>Transactions</th>
                <th>Success rate</th>
                <th>Failure rate</th>
                <th>Other outcomes</th>
              </tr>
            </thead>
            <tbody>
              {["CREDIT_CARD", "DEBIT_CARD", "UPI", "CASH"].map((m) => {
                const rows = tx.filter((t) => t.method === m);
                return (
                  <tr key={m}>
                    <td>
                      <strong>{label(m)}</strong>
                    </td>
                    <td>{rows.length}</td>
                    <td>
                      {percent(
                        rows.filter((t) => t.status === "SUCCESS").length,
                        rows.length,
                      )}
                    </td>
                    <td>
                      {percent(
                        rows.filter((t) => t.status === "FAILED").length,
                        rows.length,
                      )}
                    </td>
                    <td>
                      {
                        rows.filter(
                          (t) => !["SUCCESS", "FAILED"].includes(t.status),
                        ).length
                      }
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Panel>
    </>
  );
}

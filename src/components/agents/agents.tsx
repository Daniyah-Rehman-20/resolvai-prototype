"use client";
import { useState } from "react";
import Link from "next/link";
import { Activity, ArrowDown, Clock3 } from "lucide-react";
import { useWorkspace } from "@/components/layout/workspace";
import { PageTitle, Panel, Badge, Empty } from "@/components/common/ui";
import { dateTime } from "@/lib/utils";
export function Agents() {
  const { data } = useWorkspace();
  const [selected, setSelected] = useState(data.investigations[0]?.id || "");
  const run = data.investigations.find((i) => i.id === selected);
  return (
    <>
      <PageTitle
        eyebrow="OBSERVABLE BY DESIGN"
        title="Agent Activity"
        description="Inspect every handoff, evidence check, and recommendation."
      >
        <span className="demo-tag">
          <Activity size={16} />
          Simulated execution traces
        </span>
      </PageTitle>
      <label className="field run-selector">
        Investigation run
        <select value={selected} onChange={(e) => setSelected(e.target.value)}>
          {data.investigations.map((i) => (
            <option key={i.id} value={i.id}>
              {i.id} · {i.transactionId} · {i.status}
            </option>
          ))}
        </select>
      </label>
      {run ? (
        <>
          <div className="grid-two">
            <Panel
              title="Execution path"
              subtitle={`${run.transactionId} · ${dateTime(run.createdAt)}`}
            >
              <div className="execution-flow">
                {run.steps.map((s, i) => (
                  <div key={s.id}>
                    <div className="execution-node">
                      <span className="item-icon">
                        <Activity size={18} />
                      </span>
                      <div>
                        <strong>{s.agent}</strong>
                        <p>{s.action}</p>
                      </div>
                      <Badge value={s.status} />
                    </div>
                    {i < run.steps.length - 1 && <ArrowDown size={18} />}
                  </div>
                ))}
                {run.requiresApproval && run.status === "completed" && (
                  <>
                    <ArrowDown size={18} />
                    <Link
                      href="/approvals"
                      className="execution-node approval-node"
                    >
                      <strong>Human approval</strong>
                      <Badge value="requires_approval" />
                    </Link>
                  </>
                )}
              </div>
            </Panel>
            <Panel title="Run summary" subtitle="Measured simulation timing">
              <div className="large-stat">
                <Clock3 size={23} />
                <strong>{(run.duration / 1000).toFixed(1)}s</strong>
                <span>Total duration</span>
              </div>
              <Badge value={run.status} />
              <h3>Outcome</h3>
              <p>{run.summary || "Waiting for completion"}</p>
              <h3>Recommendation</h3>
              <p>{run.recommendation || "No recommendation generated"}</p>
              <p className="microcopy">
                These are frontend simulation traces. LangGraph and MCP are
                future backend integrations.
              </p>
              <Link
                href={`/transactions/${run.transactionId}`}
                className="text-link"
              >
                Open transaction →
              </Link>
            </Panel>
          </div>
          <Panel title="Step log">
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Agent</th>
                    <th>Action</th>
                    <th>Status</th>
                    <th>Duration</th>
                    <th>Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {run.steps.map((s) => (
                    <tr key={s.id}>
                      <td>{s.agent}</td>
                      <td>{s.action}</td>
                      <td>
                        <Badge value={s.status} />
                      </td>
                      <td>{s.duration} ms</td>
                      <td>{s.timestamp ? dateTime(s.timestamp) : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>
        </>
      ) : (
        <Empty
          title="No execution traces"
          detail="Run an investigation to see agent activity."
        />
      )}
    </>
  );
}

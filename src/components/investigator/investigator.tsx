"use client";
import { useState } from "react";
import Link from "next/link";
import {
  Sparkles,
  ArrowRight,
  CheckCircle2,
  Circle,
  LoaderCircle,
  AlertTriangle,
  ShieldCheck,
} from "lucide-react";
import { useWorkspace } from "@/components/layout/workspace";
import { PageTitle, Panel, Badge, Empty } from "@/components/common/ui";
import { startInvestigation, saveSettings } from "@/lib/api";
import type { Investigation } from "@/lib/types";
import { money, dateTime } from "@/lib/utils";
export function Investigator({ transaction = "" }: { transaction?: string }) {
  const { data, refresh, notify } = useWorkspace();
  const [selected, setSelected] = useState(
    transaction || data.transactions[0].id,
  );
  const [question, setQuestion] = useState(
    "Money was deducted, but the order failed. What happened?",
  );
  const [result, setResult] = useState<Investigation | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const tx = data.transactions.find((t) => t.id === selected);
  const policy = data.documents.find((d) => d.id === result?.policyId);
  async function run() {
    setError("");
    setRunning(true);
    try {
      await startInvestigation(selected, question, setResult);
      await refresh();
      notify("Investigation finished. Review the evidence below.");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setRunning(false);
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="EVIDENCE BEFORE ACTION"
        title="AI Investigator"
        description="Follow every check. Understand the evidence behind each recommendation."
      >
        <span className="demo-tag">
          <Sparkles size={15} />
          Simulated agent workflow
        </span>
      </PageTitle>
      <div className="investigator-layout">
        <div>
          <Panel
            title="Start an investigation"
            subtitle="Select a transaction and describe the issue"
          >
            <label className="field">
              Transaction
              <select
                aria-label="Transaction"
                value={selected}
                disabled={running}
                onChange={(e) => {
                  setSelected(e.target.value);
                  setResult(null);
                }}
              >
                {data.transactions.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.id} · {t.customer.name} · {money(t.amount)}
                  </option>
                ))}
              </select>
            </label>
            {tx && (
              <div className="selected-tx">
                <div>
                  <strong>{tx.orderId}</strong>
                  <Badge value={tx.status} />
                </div>
                <p>{tx.issue}</p>
                <Link className="text-link" href={`/transactions/${tx.id}`}>
                  View transaction details →
                </Link>
              </div>
            )}
            <label className="field">
              What would you like to investigate?
              <textarea
                aria-label="Investigation question"
                rows={4}
                maxLength={1000}
                value={question}
                disabled={running}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Describe the payment issue…"
              />
            </label>
            <button
              className="button full-width"
              disabled={running || !question.trim() || !tx}
              onClick={run}
            >
              {running ? (
                <LoaderCircle size={17} className="spin" />
              ) : (
                <Sparkles size={17} />
              )}{" "}
              {running ? "Investigating…" : "Start investigation"}
              <ArrowRight size={16} />
            </button>
            {error && (
              <p className="error-text" role="alert">
                {error}
              </p>
            )}
            <p className="microcopy">
              Uses fictional evidence and deterministic demo rules. No live LLM,
              bank, or payment API is connected.
            </p>
          </Panel>
          <Panel
            title="Recent runs"
            subtitle="Select a completed run to inspect it"
          >
            <div className="run-list">
              {data.investigations.slice(0, 5).map((i) => (
                <button
                  key={i.id}
                  disabled={running}
                  onClick={() => {
                    setResult(i);
                    setSelected(i.transactionId);
                    setQuestion(i.question);
                  }}
                >
                  <span>
                    <strong>{i.transactionId}</strong>
                    <small>{dateTime(i.createdAt)}</small>
                  </span>
                  <Badge value={i.status} />
                </button>
              ))}
            </div>
          </Panel>
        </div>
        <div>
          <Panel
            title="Investigation workflow"
            subtitle={
              result
                ? `${result.id} · ${result.transactionId}`
                : "Every agent step will appear here"
            }
            action={result ? <Badge value={result.status} /> : undefined}
          >
            {!result ? (
              <Empty
                title="Ready when you are"
                detail="Start an investigation to trace the payment, retrieve a demo policy, and review a proposed resolution."
              />
            ) : (
              <div className="agent-steps">
                {result.steps.map((s, i) => (
                  <div className={`agent-step ${s.status}`} key={s.id}>
                    <div className="agent-step-icon">
                      {s.status === "completed" ? (
                        <CheckCircle2 size={21} />
                      ) : s.status === "running" ? (
                        <LoaderCircle className="spin" size={21} />
                      ) : s.status === "failed" ? (
                        <AlertTriangle size={21} />
                      ) : (
                        <Circle size={21} />
                      )}
                    </div>
                    <div>
                      <small>
                        STEP {i + 1} · {s.agent}
                      </small>
                      <strong>{s.action}</strong>
                    </div>
                    <span>
                      {s.status === "completed" ? (
                        `${s.duration}ms`
                      ) : (
                        <Badge value={s.status} />
                      )}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </Panel>
          {result?.status === "failed" && (
            <div className="error-box">
              <h3>Evidence source unavailable</h3>
              <p>
                The simulated failure setting interrupted this run. No action
                was proposed.
              </p>
              <button
                className="button"
                onClick={async () => {
                  await saveSettings({
                    ...data.settings,
                    simulateFailure: false,
                  });
                  await refresh();
                  await run();
                }}
              >
                Disable simulated failure & retry
              </button>
            </div>
          )}
          {result?.status === "completed" && (
            <Panel
              title="Investigation findings"
              subtitle="Reviewable evidence, not a final payment decision"
            >
              <h3>{result.summary}</h3>
              <p>{result.cause}</p>
              <ul className="evidence-list">
                {result.evidence.map((e) => (
                  <li key={e}>
                    <CheckCircle2 size={16} />
                    {e}
                  </li>
                ))}
              </ul>
              <div className="policy-source">
                <small>RETRIEVED DEMO POLICY</small>
                <h3>{policy?.name}</h3>
                <p>{policy?.content}</p>
                <Link className="text-link" href="/knowledge">
                  View knowledge base →
                </Link>
              </div>
              <div className="callout">
                <ShieldCheck size={22} />
                <div>
                  <strong>{result.recommendation}</strong>
                  <p>
                    {result.requiresApproval
                      ? "Human approval is required before any simulated payment action."
                      : "No payment action has been proposed."}
                  </p>
                  {result.requiresApproval && (
                    <Link href="/approvals" className="text-link">
                      Open approval queue →
                    </Link>
                  )}
                </div>
              </div>
              <p className="microcopy">{result.uncertainty}</p>
            </Panel>
          )}
        </div>
      </div>
    </>
  );
}

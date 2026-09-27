"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AlertTriangle, Clock3, CreditCard, LoaderCircle } from "lucide-react";

import { Panel } from "@/components/common/ui";
import { useWorkspace } from "@/components/layout/workspace";
import { runPaymentUseCase } from "@/lib/api";

const cases = [
  {
    id: "charged-order-failed",
    title: "Money deducted, order failed",
    problem: "Bank debit succeeds, but merchant/order confirmation fails.",
    result: "PayResolve investigates automatically and recommends reconciliation.",
    Icon: AlertTriangle,
  },
  {
    id: "payment-pending",
    title: "Payment stuck pending",
    problem: "UPI payment has no final success or failure confirmation.",
    result: "PayResolve recommends waiting and rechecking instead of refunding too early.",
    Icon: Clock3,
  },
  {
    id: "duplicate-charge",
    title: "Customer charged twice",
    problem: "Two successful charges are detected for the same order.",
    result: "PayResolve proposes a refund and sends it to human approval.",
    Icon: CreditCard,
  },
] as const;

export function IngestTransactionPanel() {
  const { refresh, notify } = useWorkspace();
  const router = useRouter();
  const [busy, setBusy] = useState("");

  async function run(useCase: (typeof cases)[number]["id"]) {
    setBusy(useCase);
    try {
      const result = await runPaymentUseCase(useCase);
      await refresh();
      notify(`${result.message}: ${result.recommendation}`);
      router.push(`/transactions/${result.transaction.id}`);
    } finally {
      setBusy("");
    }
  }

  return (
    <Panel
      title="Run a real payment use case"
      subtitle="No customer entry or manual payment-state editing. Each scenario simulates upstream systems and automatically runs the investigation."
    >
      <div className="issue-grid">
        {cases.map(({ id, title, problem, result, Icon }) => (
          <div key={id}>
            <span className="item-icon">
              <Icon size={18} />
            </span>
            <strong>{title}</strong>
            <p>{problem}</p>
            <small>{result}</small>
            <button className="button" disabled={Boolean(busy)} onClick={() => run(id)}>
              {busy === id && <LoaderCircle className="spin" size={16} />}
              {busy === id ? "Running…" : "Run use case"}
            </button>
          </div>
        ))}
      </div>
      <p className="microcopy">
        In production these records would arrive from gateway webhooks, bank events,
        merchant services, and the order service. These buttons reproduce that integration
        for the portfolio deployment.
      </p>
    </Panel>
  );
}

"use client";

import { useState } from "react";
import Link from "next/link";
import { Activity, LoaderCircle, Plus } from "lucide-react";

import { Panel, Badge } from "@/components/common/ui";
import { useWorkspace } from "@/components/layout/workspace";
import { createTransaction, pushPaymentEvent } from "@/lib/api";
import type { Transaction } from "@/lib/types";

export function IngestTransactionPanel() {
  const { refresh, notify } = useWorkspace();
  const [name, setName] = useState("New Customer");
  const [amount, setAmount] = useState("1499");
  const [method, setMethod] = useState("UPI");
  const [scenario, setScenario] = useState("PENDING");
  const [busy, setBusy] = useState(false);
  const [created, setCreated] = useState<Transaction | null>(null);

  async function create() {
    setBusy(true);
    try {
      const tx = await createTransaction({
        customer_name: name,
        payment_method: method,
        amount: Number(amount),
        scenario,
        source_system: "PAYMENT_EVENT_INGESTION",
      });
      setCreated(tx);
      await refresh();
      notify(`${tx.id} entered the transaction pipeline.`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Panel
      title="Payment event ingestion"
      subtitle="Create a transaction exactly where an upstream payment system would enter PayResolve"
    >
      <div className="filters">
        <input
          aria-label="Customer name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Customer name"
        />
        <input
          aria-label="Amount"
          type="number"
          min="1"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          placeholder="Amount"
        />
        <select
          aria-label="Payment method"
          value={method}
          onChange={(e) => setMethod(e.target.value)}
        >
          <option value="UPI">UPI</option>
          <option value="CREDIT_CARD">Credit card</option>
          <option value="DEBIT_CARD">Debit card</option>
        </select>
        <select
          aria-label="Initial payment state"
          value={scenario}
          onChange={(e) => setScenario(e.target.value)}
        >
          <option value="PENDING">Pending</option>
          <option value="FAILED">Failed</option>
          <option value="SUCCESS">Successful</option>
          <option value="DISPUTED">Disputed</option>
        </select>
        <button className="button" disabled={busy || !Number(amount)} onClick={create}>
          {busy ? <LoaderCircle className="spin" size={17} /> : <Plus size={17} />}
          {busy ? "Ingesting…" : "Ingest transaction"}
        </button>
      </div>
      {created && (
        <p className="microcopy">
          Created <strong>{created.id}</strong> · <Badge value={created.status} />{" "}
          <Link className="text-link" href={`/transactions/${created.id}`}>
            Open transaction →
          </Link>
        </p>
      )}
    </Panel>
  );
}

export function PaymentEventPanel({ transaction }: { transaction: Transaction }) {
  const { refresh, notify } = useWorkspace();
  const [busy, setBusy] = useState("");

  const events = [
    ["BANK", "DEBITED", "Bank debit confirmed"],
    ["GATEWAY", "SUCCESS", "Gateway processing succeeded"],
    ["MERCHANT", "FAILED", "Merchant confirmation failed"],
    ["ORDER", "PAYMENT_FAILED", "Order marked payment failed"],
  ] as const;

  async function apply(source: string, status: string, issue: string) {
    setBusy(`${source}-${status}`);
    try {
      await pushPaymentEvent(transaction.id, source, status, issue);
      await refresh();
      notify(`${source} event applied to ${transaction.id}.`);
    } finally {
      setBusy("");
    }
  }

  return (
    <Panel
      title="Incoming payment events"
      subtitle="Apply upstream bank, gateway, merchant, and order updates to this transaction"
    >
      <div className="compact-list">
        {events.map(([source, status, issue]) => (
          <button
            className="compact-row"
            key={`${source}-${status}`}
            disabled={Boolean(busy)}
            onClick={() => apply(source, status, issue)}
          >
            <span>
              <Activity size={15} /> {source}
            </span>
            <Badge value={status} />
          </button>
        ))}
      </div>
      <p className="microcopy">
        Each event is persisted and appears in the transaction audit timeline.
      </p>
    </Panel>
  );
}

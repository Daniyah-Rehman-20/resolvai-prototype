"use client";

import { useState } from "react";
import Link from "next/link";
import { LoaderCircle, RadioTower } from "lucide-react";

import { Panel, Badge } from "@/components/common/ui";
import { useWorkspace } from "@/components/layout/workspace";
import { generateIncomingTransaction, pushPaymentEvent } from "@/lib/api";
import type { Transaction } from "@/lib/types";

export function IngestTransactionPanel() {
  const { refresh, notify } = useWorkspace();
  const [busy, setBusy] = useState(false);
  const [created, setCreated] = useState<Transaction | null>(null);

  async function generate() {
    setBusy(true);
    try {
      const tx = await generateIncomingTransaction();
      setCreated(tx);
      await refresh();
      notify(`${tx.id} received from the payment event stream.`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Panel
      title="Incoming transaction stream"
      subtitle="Receive a new payment record without manually entering customer or payment details"
    >
      <div className="review-banner">
        <div className="banner-icon">
          <RadioTower size={22} />
        </div>
        <div>
          <strong>Automated transaction ingestion</strong>
          <p>
            PayResolve generates the transaction, customer, order, amount and
            payment method as an upstream payment system would provide them.
          </p>
        </div>
        <button className="button" disabled={busy} onClick={generate}>
          {busy ? <LoaderCircle className="spin" size={17} /> : <RadioTower size={17} />}
          {busy ? "Receiving…" : "Generate incoming transaction"}
        </button>
      </div>
      {created && (
        <p className="microcopy">
          Received <strong>{created.id}</strong> · {created.customer.name} ·{" "}
          ₹{created.amount.toLocaleString("en-IN")} · <Badge value={created.method} /> ·{" "}
          <Badge value={created.status} />{" "}
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
            <span>{source}</span>
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

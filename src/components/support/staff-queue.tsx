"use client";

import { useEffect, useState, type FormEvent } from "react";
import { RefreshCw } from "lucide-react";
import * as api from "@/lib/support-api";
import styles from "./support.module.css";

export default function StaffQueue() {
  const [items, setItems] = useState<api.StaffQuery[]>([]);
  const [selected, setSelected] = useState<api.StaffQuery | null>(null);
  const [status, setStatus] = useState("in_review");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState("");
  const [filter, setFilter] = useState("all");
  useEffect(() => {
    let cancelled = false;
    api.listQueue().then((rows) => { if (!cancelled) setItems(rows); }).catch((e) => { if (!cancelled) setError(e instanceof Error ? e.message : "Could not load queue."); }).finally(() => { if (!cancelled) setBusy(false); });
    return () => { cancelled = true; };
  }, []);
  async function refresh() {
    setBusy(true); setError("");
    try {
      const rows = await api.listQueue();
      setItems(rows);
      if (selected) {
        const updated = rows.find((row) => row.id === selected.id) || null;
        setSelected(updated);
        setStatus(updated?.status || "in_review");
        setNote(updated?.reviewer_note || "");
      }
      setSaved("");
    }
    catch(e) { setError(e instanceof Error ? e.message : "Could not load queue."); }
    finally { setBusy(false); }
  }
  async function review(event: FormEvent) {
    event.preventDefault(); if (!selected || !note.trim()) return;
    setBusy(true); setError(""); setSaved("");
    try {
      const updated = await api.reviewQuery(selected.id, status, note.trim());
      setItems((rows) => rows.map((row) => row.id === updated.id ? updated : row));
      setSelected(updated); setSaved("Review saved. No financial action was executed.");
    } catch(e) { setError(e instanceof Error ? e.message : "Could not save review."); }
    finally { setBusy(false); }
  }
  const visible = items.filter((item) => filter === "all" || item.status === filter);
  return <section className={styles.staffSpace} aria-label="Staff review queue">
    <div className={styles.queueHeader}><div><span className={styles.eyebrow}>HUMAN REVIEW</span><h1>Customer query queue</h1><p className={styles.muted}>Review concerns and document follow-up. Resolving a query updates support workflow only.</p></div><button className={styles.textButton} disabled={busy} onClick={() => void refresh()}><RefreshCw size={16}/>Refresh</button></div>
    {error && <p className={styles.error} role="alert">{error}</p>}{saved && <p className={styles.success} role="status">{saved}</p>}
    <label className={styles.queueFilter}>Filter by status<select value={filter} onChange={(e) => setFilter(e.target.value)}><option value="all">All queries</option><option value="intake">Intake</option><option value="needs_human_review">Needs human review</option><option value="in_review">In review</option><option value="resolved">Resolved</option></select></label>
    <div className={styles.queueLayout}><div className={styles.queueList} aria-busy={busy}>{busy && <p role="status">Loading…</p>}{!busy && !visible.length && <p className={styles.empty}>No queries match this status.</p>}{visible.map((item) => <button className={styles.queueItem} key={item.id} disabled={busy} aria-pressed={selected?.id === item.id} onClick={() => { setSelected(item); setStatus(item.status); setNote(item.reviewer_note || ""); setSaved(""); }}><span className={styles.eyebrow}>{item.status.replaceAll("_", " ")}</span><strong>{item.summary}</strong><small>{new Date(item.created_at).toLocaleString()}</small></button>)}</div>
    {selected ? <form className={styles.reviewCard} onSubmit={review}><h2>{selected.summary}</h2><p className={styles.muted}>Query {selected.id}</p><dl>{Object.entries(selected.facts || {}).map(([key,value]) => <div key={key}><dt>{key.replaceAll("_", " ")}</dt><dd>{typeof value === "object" ? JSON.stringify(value) : String(value)}</dd></div>)}</dl><label>Review status<select value={status} disabled={busy} onChange={(e) => setStatus(e.target.value)}><option value="intake">Intake</option><option value="needs_human_review">Needs human review</option><option value="in_review">In review</option><option value="resolved">Resolved</option></select></label><label>Reviewer note<textarea required minLength={1} maxLength={2000} value={note} disabled={busy} onChange={(e) => setNote(e.target.value)} placeholder="Document findings and the next action. Do not include payment credentials."/></label><button className={styles.primary} disabled={busy || !note.trim()}>Save review</button></form> : <div className={styles.reviewCard}><h2>Select a query to review</h2><p className={styles.muted}>Customer-reported facts and previous reviewer notes will appear here.</p></div>}</div>
  </section>;
}

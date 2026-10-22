"use client";

import { useEffect, useState } from "react";
import { Phone } from "lucide-react";
import { supportRequest } from "@/lib/support-api";
import styles from "./support.module.css";

type ConnectionCode = { code: string; expires_at: string; phone_number: string };

export default function PhoneCallCard({ disabled }: { disabled: boolean }) {
  const [capabilities, setCapabilities] = useState<{configured: boolean; phone_number: string | null} | null>(null);
  const [code, setCode] = useState<ConnectionCode | null>(null);
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    supportRequest<{configured: boolean; phone_number: string | null}>("/telephony/capabilities")
      .then((value) => { if (active) setCapabilities(value); })
      .catch((e) => { if (active) setError(e instanceof Error ? e.message : "Could not check phone availability."); });
    return () => { active = false; };
  }, []);
  async function connect() {
    if (!consent || disabled || busy || !capabilities?.configured) return;
    setBusy(true); setError(""); setCode(null);
    try {
      setCode(await supportRequest<ConnectionCode>("/telephony/connection-code", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({consent: true}) }));
    } catch (e) { setError(e instanceof Error ? e.message : "Phone support is unavailable. You can still use chat or browser voice."); }
    finally { setBusy(false); }
  }
  return <details className={styles.phoneCard}>
    <summary><Phone size={15}/>Prefer to call by phone?</summary>
    {capabilities?.configured === false ? <p>Phone calls are not available yet on this deployment. You can use chat or record a browser voice message above.</p> : <>
    {capabilities?.phone_number && <p>Support number: <strong>{capabilities.phone_number}</strong></p>}
    <p>Connect a phone call to your account with a one-time code. Record one message after the prompt. The call then ends while we transcribe it and capture your concerns in your conversation history.</p>
    <label className={styles.checkbox}><input type="checkbox" checked={consent} disabled={disabled || busy} onChange={(e) => { setConsent(e.target.checked); setCode(null); }}/>I agree to call recording, storage and AI transcription. The phone assistant will also ask for consent before recording.</label>
    <button className={styles.textButton} disabled={disabled || busy || !consent || !capabilities?.configured} onClick={() => void connect()}>{busy ? "Preparing connection…" : code ? "Generate a new connection code" : "Get phone connection code"}</button>

    {code && <div className={styles.phoneInstructions} role="status"><strong>Call <a href={`tel:${code.phone_number.replace(/[^+\d]/g, "")}`}>{code.phone_number}</a></strong><p>When prompted, enter <b className={styles.connectionCode}>{code.code}</b>, then press 1 to consent to recording.</p><small>Code expires {new Date(code.expires_at).toLocaleString()}. Keep it private; it connects a single call to your account.</small><p>After your call, refresh your conversations to see the transcript and captured queries.</p></div>}
    </>}
    {error && <p className={styles.error} role="alert">{error}</p>}
    <small>Phone support requires this deployment’s calling provider to be configured. Your carrier’s call charges may apply.</small>
  </details>;
}

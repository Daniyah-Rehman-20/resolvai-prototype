"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { ArrowUp, Download, RefreshCw, CheckCircle2, Headphones, LogOut, MessageCircle, Mic, Plus, ShieldCheck, Square, Trash2 } from "lucide-react";
import * as api from "@/lib/support-api";
import styles from "./support.module.css";
import StaffQueue from "./staff-queue";
import PhoneCallCard from "./phone-call-card";

const errorText = (error: unknown) => error instanceof Error ? error.message : "Something went wrong. Please try again.";
const date = (value: string) => new Date(value).toLocaleString();
function sourceUrl(value?: string) { try { const url = new URL(value || ""); return url.protocol === "https:" ? url.href : undefined; } catch { return undefined; } }

export default function SupportWorkspace() {
  const [user, setUser] = useState<api.User | null>(null);
  const [staffView, setStaffView] = useState(false);
  const [ready, setReady] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [history, setHistory] = useState<api.Conversation[]>([]);
  const [active, setActive] = useState<api.Detail | null>(null);
  const [channel, setChannel] = useState<"chat" | "voice">("chat");
  const [consent, setConsent] = useState(false);
  const [speak, setSpeak] = useState(false);
  const speakEnabled = useRef(false);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [recording, setRecording] = useState(false);
  const [recordings, setRecordings] = useState<api.Recording[]>([]);
  const recorder = useRef<MediaRecorder | null>(null);
  const stream = useRef<MediaStream | null>(null);
  const stopTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const end = useRef<HTMLDivElement>(null);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    if (!api.sessionToken()) { queueMicrotask(() => { if (mounted.current) setReady(true); }); } else
    api.supportRequest<api.User>("/auth/me").then(async (value) => {
      if (!mounted.current) return;
      setUser(value);
      const conversations = await api.listConversations();
      if (mounted.current) setHistory(conversations);
    }).catch((e) => { if (e instanceof api.ApiError && e.status === 401) api.clearSession(); if (mounted.current) setError(errorText(e)); }).finally(() => { if (mounted.current) setReady(true); });
    return () => {
      mounted.current = false;
      if (stopTimer.current) clearTimeout(stopTimer.current);
      if (recorder.current) recorder.current.onstop = null;
      stream.current?.getTracks().forEach((track) => track.stop());
      window.speechSynthesis?.cancel();
    };
  }, []);
  useEffect(() => { end.current?.scrollIntoView({ behavior: "auto", block: "nearest" }); }, [active?.messages.length, busy]);

  async function run(task: () => Promise<void>) { setBusy(true); setError(""); try { await task(); } catch (e) { setError(errorText(e)); } finally { setBusy(false); } }
  async function login(event: FormEvent) { event.preventDefault(); await run(async () => { const value = await api.authenticate(authMode, email, password); setUser(value); setPassword(""); setHistory(await api.listConversations()); }); }
  async function load(id: string) {
    const detail = await api.getConversation(id);
    setRecordings([]);
    if (active?.id !== id) { setConsent(false); setDraft(""); window.speechSynthesis?.cancel(); }
    setActive(detail); setChannel(detail.channel);
    if (detail.channel === "voice") setRecordings(await api.listRecordings(id)); else setRecordings([]);
  }
  async function ensureConversation() {
    if (active) return active.id;
    const created = await api.createConversation(channel, channel === "voice" && consent);
    setHistory((items) => [created, ...items]);
    setActive({ ...created, messages: [], queries: [] });
    return created.id;
  }
  async function send(event: FormEvent) {
    event.preventDefault(); if (!draft.trim() || busy) return;
    const content = draft.trim();
    await run(async () => { const id = await ensureConversation(); await api.sendMessage(id, content); setDraft(""); await load(id); });
  }
  function say(text: string) { if (speakEnabled.current && "speechSynthesis" in window) { window.speechSynthesis.cancel(); window.speechSynthesis.speak(new SpeechSynthesisUtterance(text)); } }
  async function startRecording() {
    if (!consent) { setError("Please consent to recording before using voice support."); return; }
    await run(async () => {
      if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) throw new Error("Voice recording needs a supported browser and HTTPS (or localhost). You can still use chat.");
      window.speechSynthesis?.cancel();
      const media = await navigator.mediaDevices.getUserMedia({audio:true});
      if (!mounted.current) { media.getTracks().forEach((track) => track.stop()); return; }
      stream.current = media;
      try {
        const id = await ensureConversation();
        if (!mounted.current) { media.getTracks().forEach((track) => track.stop()); return; }
        const type = ["audio/webm;codecs=opus", "audio/mp4", "audio/webm"].find((mime) => MediaRecorder.isTypeSupported(mime));
        const device = new MediaRecorder(media, type ? {mimeType:type} : undefined);
        recorder.current = device;
        const chunks: Blob[] = [];
        device.ondataavailable = (event) => { if (event.data.size) chunks.push(event.data); };
        device.onstop = () => {
          media.getTracks().forEach((track) => track.stop());
          if (stopTimer.current) clearTimeout(stopTimer.current);
          if (!mounted.current) return;
          setRecording(false);
          recorder.current = null; stream.current = null;
          void run(async () => { const result = await api.uploadAudio(id, new Blob(chunks, {type:device.mimeType})); await load(id); say(result.message.content); });
        };
        device.onerror = () => {
          device.onstop = null;
          media.getTracks().forEach((track) => track.stop());
          if (stopTimer.current) clearTimeout(stopTimer.current);
          if (mounted.current) { setRecording(false); setError("Recording failed. Please try again or use chat."); }
        };
        device.start(); setRecording(true);
        stopTimer.current = setTimeout(() => { if (device.state === "recording") device.stop(); }, 60000);
      } catch (e) { media.getTracks().forEach((track) => track.stop()); throw e; }
    });
  }
  function discardRecording() {
    if (stopTimer.current) clearTimeout(stopTimer.current);
    const device = recorder.current;
    if (device) { device.onstop = null; if (device.state !== "inactive") device.stop(); }
    stream.current?.getTracks().forEach((track) => track.stop());
    setRecording(false);
  }
  function newConversation(mode: "chat" | "voice") { setActive(null); setChannel(mode); setConsent(false); setDraft(""); setRecordings([]); setError(""); window.speechSynthesis?.cancel(); }

  return <main className={styles.root}>
    <header className={styles.header}><a href="/support" className={styles.brand}><span className={styles.logo}><Headphones size={22}/></span>Resolve<span className={styles.brandAccent}>AI</span></a><span className={styles.headerLabel}>PAYMENT SUPPORT</span>{user && ["analyst", "approver", "admin"].includes(user.role) && <button className={styles.textButton} disabled={busy || recording} onClick={() => setStaffView(!staffView)}>{staffView ? "My support space" : "Staff queue"}</button>}{user && <button className={styles.textButton} disabled={busy || recording} onClick={() => void run(async () => { await api.supportRequest("/auth/logout", {method:"POST"}); api.clearSession(); setUser(null); setStaffView(false); setActive(null); setHistory([]); setRecordings([]); setDraft(""); setConsent(false); setSpeak(false); speakEnabled.current = false; setChannel("chat"); window.speechSynthesis?.cancel(); })}><LogOut size={16}/>Sign out</button>}</header>
    {!ready ? <p className={styles.loading} role="status">Restoring your secure session…</p> : !user ? <section className={styles.authLayout}>
      <div className={styles.intro}><span className={styles.eyebrow}>LET’S MAKE SENSE OF IT</span><h1>A payment problem.<br/>A clear next step.</h1><p>Tell us what happened by chat or voice. Your AI support assistant organizes your concerns and helps you understand what to do next.</p><div className={styles.promise}><ShieldCheck size={24}/><span>Your own support history.<br/>No PINs, passwords or OTPs needed.</span></div><div className={styles.featureRow}><span><MessageCircle size={19}/>Chat at your pace</span><span><Mic size={19}/>Talk it through</span></div></div>
      <form className={styles.authCard} onSubmit={login}><span className={styles.eyebrow}>YOUR SUPPORT SPACE</span><h2>{authMode === "login" ? "Welcome back" : "Create your account"}</h2><p>{authMode === "login" ? "Sign in to continue your conversation." : "Keep your conversations and queries together."}</p><label>Email address<input type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com"/></label><label>Password<input type="password" autoComplete={authMode === "login" ? "current-password" : "new-password"} minLength={authMode === "register" ? 12 : undefined} maxLength={128} required value={password} onChange={(e) => setPassword(e.target.value)}/></label>{authMode === "register" && <small>Use at least 12 characters.</small>}{error && <p className={styles.error} role="alert">{error}</p>}<button className={styles.primary} disabled={busy}>{busy ? "Please wait…" : authMode === "login" ? "Sign in" : "Create account"}</button><button className={styles.textButton} type="button" disabled={busy} onClick={() => {setAuthMode(authMode === "login" ? "register" : "login");setError("");}}>{authMode === "login" ? "New here? Create an account" : "Already registered? Sign in"}</button><small>Support guidance does not confirm bank balances or execute refunds.</small></form>
    </section> : staffView ? <StaffQueue/> : <div className={styles.workspace}>
      <aside className={styles.sidebar}><div className={styles.sidebarHeading}><h2>Your conversations</h2><button aria-label="Refresh conversations" disabled={busy || recording} onClick={() => void run(async () => {setHistory(await api.listConversations()); if (active) await load(active.id);})}><RefreshCw size={16}/></button><button aria-label="New conversation" disabled={busy || recording} onClick={() => newConversation("chat")}><Plus size={21}/></button></div><p className={styles.muted}>{user.email}</p><nav aria-label="Conversation history" className={styles.history}>{history.length === 0 && <p className={styles.empty}>Your conversations will appear here.</p>}{history.map((item) => <button key={item.id} aria-current={active?.id === item.id ? "true" : undefined} disabled={busy || recording} onClick={() => void run(() => load(item.id))}>{item.channel === "voice" ? <Mic size={17}/> : <MessageCircle size={17}/>}<span>{item.channel === "voice" ? "Voice conversation" : "Chat conversation"}<small>{date(item.created_at)}</small></span></button>)}</nav><div className={styles.sidebarNote}><ShieldCheck size={20}/><p>Never share an OTP, UPI PIN, CVV, password or full card number.</p></div></aside>
      <section className={styles.chat}><div className={styles.chatHeader}><div><span className={styles.eyebrow}>HERE TO HELP</span><h1>Let’s work through it.</h1></div><div className={styles.tabs} role="group" aria-label="Conversation mode"><button aria-pressed={channel === "chat"} disabled={busy || recording} onClick={() => newConversation("chat")}><MessageCircle size={16}/>Chat</button><button aria-pressed={channel === "voice"} disabled={busy || recording} onClick={() => newConversation("voice")}><Mic size={16}/>Voice</button></div></div>
      <div className={styles.messages} role="log" aria-label="Messages" aria-live="polite">{!active?.messages.length && <div className={styles.welcome}><span className={styles.welcomeIcon}><Headphones size={30}/></span><h2>What happened with your payment?</h2><p>Describe the issue, payment method and when it happened. We’ll capture each concern and suggest next steps.</p><div className={styles.suggestions}>{["Money debited, but payment failed", "My payment is still pending", "I was charged twice"].map((text) => <button key={text} disabled={busy || recording} onClick={() => setDraft(text)}>{text}<ArrowUp size={15}/></button>)}</div></div>}{active?.messages.map((message) => <article key={message.id} className={`${styles.message} ${message.role === "user" ? styles.userMessage : styles.assistantMessage}`}><small>{message.role === "user" ? "You" : "ResolveAI"}</small><p>{message.content}</p>{message.sources?.map((source, i) => <span key={i} className={styles.source}>{sourceUrl(source.url) ? <a href={sourceUrl(source.url)} target="_blank" rel="noopener noreferrer">{source.title || "Policy source"} ↗</a> : source.title}</span>)}</article>)}{busy && <p className={styles.muted} role="status">Working on your request…</p>}<div ref={end}/></div>
      <div className={styles.composer}>{error && <p className={styles.error} role="alert">{error}</p>}{channel === "voice" && <div className={styles.voicePanel}><label className={styles.checkbox}><input type="checkbox" checked={consent} disabled={recording || busy} onChange={(e) => setConsent(e.target.checked)}/>I consent to recording, storage and AI transcription of my voice. Recordings can be deleted below.</label><div className={styles.voiceActions}><button className={recording ? styles.stop : styles.primary} disabled={busy || (!recording && !consent)} onClick={() => recording ? recorder.current?.stop() : void startRecording()}>{recording ? <Square size={17}/> : <Mic size={17}/>} {recording ? "Stop & send recording" : "Record voice message"}</button>{recording && <button className={styles.textButton} onClick={discardRecording}>Discard recording</button>}<label className={styles.checkbox}><input type="checkbox" checked={speak} onChange={(e) => {setSpeak(e.target.checked); speakEnabled.current = e.target.checked; if (!e.target.checked) window.speechSynthesis?.cancel();}}/>Read replies aloud</label></div><small>{recording ? "Microphone is recording. Stops automatically after 60 seconds." : "Browser voice support · Up to 60 seconds per message · Stop to send"}</small><PhoneCallCard key={`${user.id}:${active?.id || "new"}`} disabled={busy || recording}/></div>}<form onSubmit={send} className={styles.messageForm}><textarea aria-label="Your payment query" placeholder="Tell us about your payment issue…" value={draft} maxLength={4000} disabled={busy || recording} onChange={(e) => setDraft(e.target.value)}/><button type="submit" aria-label="Send message" disabled={busy || recording || !draft.trim() || (channel === "voice" && !active && !consent)}><ArrowUp size={21}/></button></form><small className={styles.disclaimer}>AI guidance can be incomplete. Your bank or payment provider confirms payment status and handles refunds.</small></div></section>
      <aside className={styles.queries}><span className={styles.eyebrow}>NOTHING GETS LOST</span><h2>Your query list <span>{active?.queries.length || 0}</span></h2><p className={styles.muted}>Concerns captured from this conversation. Transaction details are user-reported.</p>{!active?.queries.length && <div className={styles.queryEmpty}><CheckCircle2 size={28}/><p>Your concerns will appear here as we talk.</p></div>}{active?.queries.map((query, index) => <article className={styles.query} key={query.id}><small>QUERY {String(index + 1).padStart(2,"0")} · {query.status.replaceAll("_", " ")}</small><h3>{query.summary}</h3>{query.reviewer_note && <p><strong>Support update: </strong>{query.reviewer_note}</p>}{Object.entries(query.facts || {}).map(([key,value]) => <p key={key}><strong>{key.replaceAll("_"," ")}: </strong>{typeof value === "object" ? JSON.stringify(value) : String(value)}</p>)}</article>)}{recordings.length > 0 && <section className={styles.recordings}><h3>Saved recordings</h3>{recordings.map((item) => <div key={item.id}><span>{date(item.created_at)}<small>Expires {date(item.expires_at)}</small></span><button disabled={busy || recording} aria-label={`Download recording from ${date(item.created_at)}`} onClick={() => void run(async () => {if(active) await api.downloadRecording(active.id, item);})}><Download size={16}/></button><button disabled={busy || recording} aria-label={`Delete recording from ${date(item.created_at)}`} onClick={() => void run(async () => {if(active) {await api.deleteRecording(active.id,item.id); setRecordings(await api.listRecordings(active.id));}})}><Trash2 size={16}/></button></div>)}</section>}<div className={styles.helpNote}><strong>Need immediate help?</strong><p>For suspected fraud, contact your bank immediately using its official app or verified support number.</p></div></aside>
    </div>}
  </main>;
}

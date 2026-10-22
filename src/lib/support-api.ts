export const SESSION_TOKEN_KEY = "payresolve-session-token";
const rawBase = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
const base = (/^https?:\/\//i.test(rawBase) ? rawBase : `https://${rawBase}`).replace(/\/$/, "");
export type User = { id: string; email: string; role: string };
export type Conversation = { id: string; channel: "chat" | "voice"; status: string; recording_consent: boolean; created_at: string };
export type Message = { id: string; role: string; content: string; created_at: string; sources?: { title?: string; url?: string }[]; mode?: string };
export type Query = { id: string; summary: string; status: string; facts: Record<string, unknown>; created_at: string; reviewer_note?: string; reviewed_at?: string };
export type Detail = Conversation & { messages: Message[]; queries: Query[] };
export type Recording = { id: string; created_at: string; expires_at: string; content_type: string; size_bytes: number };
export class ApiError extends Error { constructor(message: string, public status: number) { super(message); } }
export function sessionToken() { return typeof window === "undefined" ? null : sessionStorage.getItem(SESSION_TOKEN_KEY); }
export function clearSession() { sessionStorage.removeItem(SESSION_TOKEN_KEY); }
export async function supportRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  const token = sessionToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  let response: Response;
  try { response = await fetch(`${base}${path}`, { ...init, headers, cache: "no-store" }); }
  catch { throw new Error("Cannot reach support right now. Check your connection and try again."); }
  if (!response.ok) {
    let message = `Request failed (${response.status}). Please try again.`;
    try { const body = await response.json(); if (typeof body.detail === "string") message = body.detail; else if (Array.isArray(body.detail)) message = body.detail.map((e: {msg:string}) => e.msg).join("; "); } catch {}
    throw new ApiError(message, response.status);
  }
  return response.status === 204 ? undefined as T : response.json();
}
const json = (body: unknown): RequestInit => ({ method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
export async function authenticate(mode: "login" | "register", email: string, password: string) {
  const result = await supportRequest<{access_token:string;user:User}>(`/auth/${mode}`, json({email,password}));
  sessionStorage.setItem(SESSION_TOKEN_KEY, result.access_token);
  return result.user;
}
export const listConversations = () => supportRequest<Conversation[]>("/support/conversations");
export const getConversation = (id: string) => supportRequest<Detail>(`/support/conversations/${encodeURIComponent(id)}`);
export const createConversation = (channel: Conversation["channel"], consent: boolean) => supportRequest<Conversation>("/support/conversations", json({ channel, recording_consent: consent }));
export const sendMessage = (id: string, content: string) => supportRequest<{message:Message;queries:Query[]}>(`/support/conversations/${encodeURIComponent(id)}/messages`, json({content}));
export const listRecordings = async (id:string) => (await supportRequest<{recordings: Recording[]}>(`/support/conversations/${encodeURIComponent(id)}/recordings`)).recordings;
export const deleteRecording = (id:string, recordingId:string) => supportRequest<void>(`/support/conversations/${encodeURIComponent(id)}/recordings/${encodeURIComponent(recordingId)}`, {method:"DELETE"});
export function uploadAudio(id: string, blob: Blob) {
  const form = new FormData();
  form.append("file", blob, blob.type.includes("mp4") ? "recording.m4a" : "recording.webm");
  form.append("consent", "true");
  return supportRequest<{transcript:string;message:Message;queries:Query[];recording:Recording}>(`/support/conversations/${encodeURIComponent(id)}/audio`, { method: "POST", body: form });
}

export type StaffQuery = Query & { conversation_id: string };
export const listQueue = () => supportRequest<StaffQuery[]>("/support/queue");
export const reviewQuery = (id: string, status: string, reviewer_note: string) => supportRequest<StaffQuery>(`/support/queries/${encodeURIComponent(id)}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({status, reviewer_note}) });
export async function downloadRecording(conversationId: string, recording: Recording) {
  const response = await fetch(`${base}/support/conversations/${encodeURIComponent(conversationId)}/recordings/${encodeURIComponent(recording.id)}`, { headers: { Authorization: `Bearer ${sessionToken() || ""}` }, cache: "no-store" });
  if (!response.ok) throw new ApiError("Could not download this recording. It may have expired.", response.status);
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement("a");
  link.href = url;
  link.download = `recording-${recording.id}.${recording.content_type.includes("mp4") ? "m4a" : "webm"}`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

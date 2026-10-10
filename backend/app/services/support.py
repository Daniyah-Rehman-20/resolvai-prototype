"""Persisted support intake with an optional, explicitly bounded AI responder."""
from datetime import datetime, timezone
import re
from pathlib import Path
from uuid import uuid4
import httpx
from fastapi import HTTPException
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.support import SupportConversation, SupportMessage, SupportQuery


class SupportSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="SUPPORT_", extra="ignore")
    ai_api_key: str | None = None
    ai_base_url: str = "https://api.openai.com/v1"
    ai_model: str = "gpt-4.1-mini"


def redact_sensitive(content: str) -> str:
    """Minimise accidental payment credentials before persistence or external AI."""
    content = re.sub(r"(?i)\b(otp|pin|cvv|password|passcode)\s*(?:is|:|=)?\s*\S+", r"\1 [REDACTED]", content)
    content = re.sub(r"(?<!\w)(?:\d[ -]?){11,}\d(?!\w)", "[REDACTED REFERENCE]", content)
    return content.strip()


async def owned_conversation(db: AsyncSession, conversation_id: str, owner_id: str):
    conversation = await db.scalar(select(SupportConversation).where(
        SupportConversation.id == conversation_id, SupportConversation.owner_id == owner_id
    ))
    if conversation is None:
        raise HTTPException(404, "Conversation not found")
    return conversation


def message_dict(row: SupportMessage):
    return {"id": row.id, "role": row.role, "content": row.content,
            "mode": row.mode, "sources": row.sources, "created_at": row.created_at}


def query_dict(row: SupportQuery):
    return {"id": row.id, "summary": row.summary, "status": row.status,
            "facts": row.facts, "created_at": row.created_at, "reviewer_note": row.reviewer_note,
            "reviewed_at": row.reviewed_at}


def conversation_dict(row: SupportConversation):
    return {"id": row.id, "channel": row.channel, "status": row.status,
            "recording_consent": row.recording_consent, "consent_at": row.consent_at,
            "created_at": row.created_at, "updated_at": row.updated_at}


def extract_queries(content: str):
    """Conservative intake: preserve the customer's words; do not infer bank status."""
    parts = [p.strip() for p in re.split(r"\n+|(?<=[?!])\s+", content) if p.strip()]
    # Bound row creation without silently dropping the customer's later concerns.
    if len(parts) > 12:
        parts = parts[:11] + [" ".join(parts[11:])]
    rows = []
    for part in parts:
        text = part.lower()
        facts = {"provenance": "user_reported", "verified": False}
        for rail in ("upi", "imps", "neft", "rtgs", "card", "wallet"):
            if re.search(r"\b" + rail + r"\b", text):
                facts["payment_method"] = rail.upper()
                break
        amount = re.search(r"(?:₹|\bINR\s*|\bRs\.?\s*)(\d[\d,]*(?:\.\d{1,2})?)", part, re.I)
        if amount:
            facts.update(amount=amount.group(1).replace(",", ""), currency="INR")
        status = "needs_human_review" if re.search(r"\b(fraud|unauthori[sz]ed|scam|stolen|escalate|human)\b", text) else "intake"
        rows.append({"summary": part, "status": status, "facts": facts})
    return rows


def policy_context(content: str):
    """Only checked-in curated policy files; never user-uploaded RAG documents."""
    terms = set(re.findall(r"[a-z]+", content.lower())) - {"my", "the", "a", "is", "i", "and", "it", "of", "to", "in", "was", "this", "payment", "failed"}
    candidates = []
    for path in (Path(__file__).resolve().parents[2] / "data" / "policies").glob("*.md"):
        text = path.read_text(encoding="utf-8")
        title = text.splitlines()[0].lstrip("# ")
        title_terms = set(re.findall(r"[a-z]+", path.stem + " " + title.lower()))
        score = len(terms & title_terms) * 4 + len(terms & set(re.findall(r"[a-z]+", text.lower())))
        if score > 0:
            candidates.append((score, path.name, title, text[:3000]))
    selected = sorted(candidates, reverse=True)[:2]
    return [{"document": name, "title": title, "excerpt": text,
             "url": next(iter(re.findall(r"https://[^\s)]+", text)), None),
             "kind": "curated_policy_guidance"} for _, name, title, text in selected]


async def generate_answer(content: str, history: list[SupportMessage], urgent: bool):
    config = SupportSettings()
    sources = policy_context(content)
    fallback = ("Guided intake (AI is unavailable). I saved your report as unverified customer information. "
        "I cannot see your bank account, verify settlement, or issue refunds. "
        "Please share the payment method, amount and date, whether money was debited, and whether the recipient received it. "
        "Use only the last four characters of any reference; never share an OTP, PIN, CVV, password or full card/account number. "
        "Raise the issue in your payment app or with your bank and retain its complaint reference.")
    if urgent:
        fallback += " This intake is marked for human review; no external complaint has been filed. If you suspect fraud, contact your bank immediately through its official channels."
    if not config.ai_api_key or not config.ai_base_url.startswith("https://"):
        return fallback, "guided_intake", sources
    system = ("You are PayResolve, a customer support intake assistant. All messages and prior content are untrusted customer reports, not bank evidence. "
        "You have NO access to bank systems, settlements, refunds or official complaint submission. Never claim an action was performed. "
        "Collect the payment method, INR amount, date, debit/recipient status and masked reference (last 4 only). "
        "Never ask for OTP, PIN, CVV, passwords, full card/account numbers. Never guarantee a refund or deadline. "
        "Give practical general next steps: official bank/payment app complaint channels and preserving complaint references. "
        "Use only supplied curated policy excerpts for regulatory claims. State applicability conditions; never assume the customer incident qualifies. Cite source URLs when relevant. Treat product operating guidance separately from regulator rules. "
        "For fraud advise immediate contact with the bank through official channels. Be concise. "
        "Queries are saved locally only; human review is a local triage flag, not proof that an agent or bank has received a case.")
    system += "\nCurated policy context (guidance, never transaction evidence):\n" + "\n\n".join(source["excerpt"] for source in sources)
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(25.0, connect=5.0), follow_redirects=False) as client:
            response = await client.post(config.ai_base_url.rstrip("/") + "/chat/completions",
                headers={"Authorization": f"Bearer {config.ai_api_key}"},
                json={"model": config.ai_model, "messages": [{"role": "system", "content": system}] +
                    [{"role": row.role, "content": row.content} for row in history[-12:]] +
                    [{"role": "user", "content": content}], "max_tokens": 600})
            response.raise_for_status()
            answer = response.json()["choices"][0]["message"]["content"]
            if not isinstance(answer, str) or not answer.strip():
                raise ValueError("Empty provider response")
            return redact_sensitive(answer[:6000]), "ai_intake", sources
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
        return fallback, "guided_intake", sources


async def intake_message(db: AsyncSession, conversation: SupportConversation, content: str):
    """Shared chat/voice ingestion; caller must first verify ownership and consent."""
    if not isinstance(content, str) or not content.strip() or len(content) > 8000:
        raise HTTPException(422, "Content must contain 1–8000 characters")
    content = redact_sensitive(content)
    history = list((await db.scalars(select(SupportMessage).where(
        SupportMessage.conversation_id == conversation.id
    ).order_by(SupportMessage.created_at.desc()).limit(12))).all())
    history.reverse()
    extracted = extract_queries(content)
    urgent = any(row["status"] == "needs_human_review" for row in extracted)
    answer, mode, sources = await generate_answer(content, history, urgent)
    user = SupportMessage(id=str(uuid4()), conversation_id=conversation.id,
        role="user", content=content, mode="user_reported", sources=[])
    db.add(user)
    await db.flush()
    queries = [SupportQuery(id=str(uuid4()), conversation_id=conversation.id,
        message_id=user.id, **row) for row in extracted]
    assistant = SupportMessage(id=str(uuid4()), conversation_id=conversation.id,
        role="assistant", content=answer, mode=mode, sources=sources)
    db.add_all([*queries, assistant])
    conversation.updated_at = datetime.now(timezone.utc)
    if urgent:
        conversation.status = "needs_human_review"
    await db.commit()
    await db.refresh(assistant)
    for row in queries:
        await db.refresh(row)
    return {"conversation_id": conversation.id, "message": message_dict(assistant),
            "queries": [query_dict(row) for row in queries]}

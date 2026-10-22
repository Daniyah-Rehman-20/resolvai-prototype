from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import Principal, current_principal, require
from app.db.session import get_db
from app.models.domain import AuditEvent
from app.models.support import SupportConversation, SupportMessage, SupportQuery
from app.services.support import redact_sensitive, conversation_dict, intake_message, message_dict, owned_conversation, query_dict

router = APIRouter(prefix="/support", tags=["customer support"])


class ConversationCreate(BaseModel):
    channel: Literal["chat", "voice"] = "chat"
    recording_consent: bool = False


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=8000)

    @field_validator("content")
    @classmethod
    def nonempty(cls, value):
        if not value.strip():
            raise ValueError("Message cannot be blank")
        return value.strip()


@router.get("/conversations")
async def list_conversations(db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(current_principal), limit: int = Query(50, ge=1, le=100)):
    rows = await db.scalars(select(SupportConversation).where(
        SupportConversation.owner_id == principal.subject
    ).order_by(SupportConversation.updated_at.desc()).limit(limit))
    return [conversation_dict(row) for row in rows]


@router.post("/conversations", status_code=201)
async def create_conversation(body: ConversationCreate, db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(current_principal)):
    if body.channel == "voice" and not body.recording_consent:
        raise HTTPException(422, "Explicit recording consent is required for voice")
    row = SupportConversation(id=str(uuid4()), owner_id=principal.subject,
        channel=body.channel, status="collecting", recording_consent=body.recording_consent,
        consent_at=datetime.now(timezone.utc) if body.recording_consent else None)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return conversation_dict(row)


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(current_principal)):
    row = await owned_conversation(db, conversation_id, principal.subject)
    messages = await db.scalars(select(SupportMessage).where(
        SupportMessage.conversation_id == row.id).order_by(SupportMessage.created_at))
    queries = await db.scalars(select(SupportQuery).where(
        SupportQuery.conversation_id == row.id).order_by(SupportQuery.created_at))
    return {**conversation_dict(row), "messages": [message_dict(x) for x in messages],
            "queries": [query_dict(x) for x in queries]}


@router.post("/conversations/{conversation_id}/messages")
async def post_message(conversation_id: str, body: MessageCreate,
    db: AsyncSession = Depends(get_db), principal: Principal = Depends(current_principal)):
    row = await owned_conversation(db, conversation_id, principal.subject)
    return await intake_message(db, row, body.content)


class QueryReview(BaseModel):
    status: Literal["intake", "needs_human_review", "in_review", "resolved"]
    reviewer_note: str = Field(min_length=1, max_length=2000)

    @field_validator("reviewer_note")
    @classmethod
    def nonempty(cls, value):
        if not value.strip():
            raise ValueError("A review note is required")
        return redact_sensitive(value.strip())


@router.get("/queue")
async def staff_queue(db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require("analyst")), limit: int = Query(100, ge=1, le=200)):
    rows = await db.scalars(select(SupportQuery).order_by(SupportQuery.created_at.desc()).limit(limit))
    return [{**query_dict(row), "conversation_id": row.conversation_id} for row in rows]


@router.patch("/queries/{query_id}")
async def review_query(query_id: str, body: QueryReview, db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require("analyst"))):
    row = await db.scalar(select(SupportQuery).where(SupportQuery.id == query_id).with_for_update())
    if row is None:
        raise HTTPException(404, "Query not found")
    previous = row.status
    row.status, row.reviewer_note = body.status, body.reviewer_note
    row.reviewed_by, row.reviewed_at = principal.subject, datetime.now(timezone.utc)
    db.add(AuditEvent(id=str(uuid4()), actor=principal.subject, action="support.query.reviewed",
        resource_type="support_query", resource_id=row.id, correlation_id=str(uuid4()),
        metadata_json={"previous_status": previous, "status": row.status,
                       "scope": "support_workflow_only_no_financial_action"}))
    await db.commit()
    await db.refresh(row)
    return {**query_dict(row), "conversation_id": row.conversation_id}

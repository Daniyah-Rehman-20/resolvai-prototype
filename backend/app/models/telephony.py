"""Durable phone linkage and recording work; no caller phone numbers stored."""
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TimestampMixin

class PhoneLink(Base, TimestampMixin):
    __tablename__ = 'phone_links'
    code_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(36), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used: Mapped[bool] = mapped_column(Boolean, default=False)

class PhoneCall(Base, TimestampMixin):
    __tablename__ = 'phone_calls'
    call_sid: Mapped[str] = mapped_column(String(34), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(36))
    conversation_id: Mapped[str | None] = mapped_column(ForeignKey('support_conversations.id', ondelete='CASCADE'), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class PhoneRecording(Base, TimestampMixin):
    __tablename__ = 'phone_recordings'
    __table_args__ = (UniqueConstraint('call_sid', name='uq_phone_call_recording'),)
    recording_sid: Mapped[str] = mapped_column(String(34), primary_key=True)
    call_sid: Mapped[str] = mapped_column(ForeignKey('phone_calls.call_sid', ondelete='CASCADE'))
    status: Mapped[str] = mapped_column(String(20), default='queued')
    response: Mapped[str | None] = mapped_column(Text, nullable=True)

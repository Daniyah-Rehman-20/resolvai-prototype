"""Audit records for real support review actions."""
from datetime import datetime, timezone
from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class AuditEvent(Base):
    __tablename__="audit_events"; id:Mapped[str]=mapped_column(String,primary_key=True); actor:Mapped[str]=mapped_column(String); action:Mapped[str]=mapped_column(String,index=True); resource_type:Mapped[str]=mapped_column(String); resource_id:Mapped[str]=mapped_column(String,index=True); timestamp:Mapped[datetime]=mapped_column(default=lambda: datetime.now(timezone.utc)); metadata_json:Mapped[dict]=mapped_column("metadata",JSON,default=dict); correlation_id:Mapped[str]=mapped_column(String,index=True)

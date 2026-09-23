from pathlib import Path
from fastapi import APIRouter,Depends
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models import AuditEvent,ApprovalRequest,Investigation,Dispute,Document

router=APIRouter(prefix="/demo",tags=["demo"])

@router.post("/reset")
async def reset_demo(db:AsyncSession=Depends(get_db)):
    for model in [AuditEvent,ApprovalRequest,Investigation,Dispute,Document]:
        await db.execute(delete(model))
    await db.commit()

    uploads=Path("./uploads")
    if uploads.exists():
        for p in uploads.iterdir():
            if p.is_file():
                try:
                    p.unlink()
                except OSError:
                    pass

    return {"ok":True}

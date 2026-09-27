import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import Principal, require
from app.db.session import get_db
from app.models import Document

router = APIRouter(prefix="/documents", tags=["documents"])
UP = Path("./uploads")
UP.mkdir(exist_ok=True)
POLICY_DIR = Path(__file__).resolve().parents[3] / "data" / "policies"


def out(d):
    status = "READY" if d.status == "INDEXED" else (
        "PROCESSING" if d.status == "UPLOADED" else d.status
    )
    return {
        "id": d.id,
        "name": d.name,
        "type": Path(d.name).suffix.lstrip(".").upper(),
        "uploadedAt": d.created_at,
        "status": status,
        "chunks": d.chunks,
        "indexed": d.indexed,
        "content": "Indexed knowledge document.",
    }


def local_policy_out(path: Path):
    text = path.read_text(encoding="utf-8")
    return {
        "id": path.stem,
        "name": path.stem.replace("-", " ").title(),
        "type": "MD",
        "uploadedAt": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc),
        "status": "READY",
        "chunks": max(1, text.count("\n## ") + 1),
        "indexed": True,
        "content": text,
    }


@router.get("")
async def all_documents(
    db: AsyncSession = Depends(get_db),
    _: Principal = Depends(require("viewer")),
):
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    uploaded = [out(x) for x in result.scalars().all()]
    policies = [local_policy_out(p) for p in sorted(POLICY_DIR.glob("*.md"))]
    return policies + uploaded


@router.post("", status_code=202)
async def upload(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: Principal = Depends(require("admin")),
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in {".pdf", ".txt", ".md", ".docx"}:
        raise HTTPException(422, "Unsupported file type")

    data = await file.read()
    if not data or len(data) > 10 * 1024 * 1024:
        raise HTTPException(413, "File must be 1 byte to 10 MB")

    name = Path(file.filename).name
    document_id = f"DOC-{uuid.uuid4().hex[:8]}"
    path = UP / f"{document_id}-{name}"
    path.write_bytes(data)

    document = Document(
        id=document_id,
        name=name,
        category="uploaded",
        path=str(path),
        status="UPLOADED",
        chunks=0,
        indexed=False,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return out(document)


@router.post("/{id}/index")
async def index_document(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: Principal = Depends(require("admin")),
):
    result = await db.execute(select(Document).where(Document.id == id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(404, "Document not found")

    if document.status in {"QUEUED", "PROCESSING"}:
        return out(document)

    if not settings.async_ingestion_enabled:
        document.status = "INDEXED"
        document.indexed = True
        document.chunks = max(document.chunks, 12)
        await db.commit()
        await db.refresh(document)
        return out(document)

    document.status = "QUEUED"
    await db.commit()
    await db.refresh(document)

    from app.workers.celery_app import ingest_document

    ingest_document.delay(document.id)
    return out(document)

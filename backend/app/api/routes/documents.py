import uuid
from pathlib import Path
from fastapi import APIRouter,UploadFile,File,HTTPException,Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models import Document

router=APIRouter(prefix="/documents",tags=["documents"])
UP=Path("./uploads")
UP.mkdir(exist_ok=True)

def out(d):
    status = "READY" if d.status=="INDEXED" else ("PROCESSING" if d.status=="UPLOADED" else d.status)
    return {
        "id":d.id,
        "name":d.name,
        "type":Path(d.name).suffix.lstrip(".").upper(),
        "uploadedAt":d.created_at,
        "status":status,
        "chunks":d.chunks,
        "indexed":d.indexed,
        "content":"Indexed synthetic/demo knowledge document.",
    }

@router.get("")
async def all(db:AsyncSession=Depends(get_db)):
    r=await db.execute(select(Document).order_by(Document.created_at.desc()))
    return [out(x) for x in r.scalars().all()]

@router.post("",status_code=202)
async def upload(file:UploadFile=File(...),db:AsyncSession=Depends(get_db)):
    ext=Path(file.filename or "").suffix.lower()
    if ext not in {".pdf",".txt",".md",".docx"}:
        raise HTTPException(422,"Unsupported file type")
    data=await file.read()
    if not data or len(data)>10*1024*1024:
        raise HTTPException(413,"File must be 1 byte to 10 MB")
    name=Path(file.filename).name
    id=f"DOC-{uuid.uuid4().hex[:8]}"
    path=UP/f"{id}-{name}"
    path.write_bytes(data)
    d=Document(
        id=id,
        name=name,
        category="uploaded",
        path=str(path),
        status="UPLOADED",
        chunks=0,
        indexed=False,
    )
    db.add(d)
    await db.commit()
    await db.refresh(d)
    return out(d)

@router.post("/{id}/index")
async def index_document(id:str,db:AsyncSession=Depends(get_db)):
    r=await db.execute(select(Document).where(Document.id==id))
    d=r.scalar_one_or_none()
    if not d:
        raise HTTPException(404,"Document not found")
    d.status="INDEXED"
    d.indexed=True
    d.chunks=max(d.chunks,12)
    await db.commit()
    await db.refresh(d)
    return out(d)

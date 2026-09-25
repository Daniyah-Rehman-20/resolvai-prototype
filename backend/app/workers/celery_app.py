import asyncio
from pathlib import Path
from celery import Celery
from docx import Document as DocxDocument
from pypdf import PdfReader
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from app.core.config import settings
from app.db.session import SessionLocal
from app.models import Document

celery_app = Celery("payresolve", broker=settings.rabbitmq_url, backend=settings.redis_url)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf":
        return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
    if suffix == ".docx":
        doc = DocxDocument(str(path))
        return "\n".join(p.text for p in doc.paragraphs)
    raise ValueError(f"Unsupported document type: {suffix}")

def chunk_text(text: str, size: int = 900, overlap: int = 120) -> list[str]:
    clean = " ".join(text.split())
    if not clean:
        return []
    chunks, start = [], 0
    while start < len(clean):
        chunks.append(clean[start:start + size])
        start += max(1, size - overlap)
    return chunks

async def _document(document_id: str):
    async with SessionLocal() as db:
        row = (await db.execute(select(Document).where(Document.id == document_id))).scalar_one_or_none()
        if not row:
            raise ValueError(f"Document {document_id} not found")
        return row.path, row.name

async def _set_status(document_id: str, status: str, chunks: int = 0, indexed: bool = False):
    async with SessionLocal() as db:
        row = (await db.execute(select(Document).where(Document.id == document_id))).scalar_one()
        row.status, row.chunks, row.indexed = status, chunks, indexed
        await db.commit()

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True, max_retries=3)
def ingest_document(self, document_id: str):
    path_str, name = asyncio.run(_document(document_id))
    asyncio.run(_set_status(document_id, "PROCESSING"))
    chunks = chunk_text(extract_text(Path(path_str)))
    if not chunks:
        asyncio.run(_set_status(document_id, "FAILED"))
        raise ValueError("Document contains no extractable text")

    model = SentenceTransformer(settings.embedding_model)
    vectors = model.encode(chunks, normalize_embeddings=True).tolist()
    client = QdrantClient(url=settings.qdrant_url)
    dim = len(vectors[0])
    if not client.collection_exists(settings.qdrant_collection):
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
        )
    points = [
        models.PointStruct(
            id=f"{document_id}-{i}",
            vector=vector,
            payload={"document": document_id, "name": name, "chunk_id": f"{document_id}-{i}", "text": text},
        )
        for i, (text, vector) in enumerate(zip(chunks, vectors))
    ]
    client.upsert(collection_name=settings.qdrant_collection, points=points, wait=True)
    asyncio.run(_set_status(document_id, "INDEXED", len(chunks), True))
    return {"document_id": document_id, "status": "INDEXED", "chunks": len(chunks)}

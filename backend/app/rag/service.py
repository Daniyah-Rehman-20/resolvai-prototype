from dataclasses import dataclass
from pathlib import Path
import re
from rank_bm25 import BM25Okapi
from app.core.config import settings

@dataclass
class Chunk:
    document: str
    section: str
    chunk_id: str
    text: str

def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())

class RAGService:
    def __init__(self):
        self.chunks: list[Chunk] = []
        self._bm25: BM25Okapi | None = None
        self._embedding_model = None
        self.reload()

    def reload(self):
        self.chunks.clear()
        base = Path(__file__).resolve().parents[2] / "data" / "policies"
        for path in sorted(base.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            parts = [x.strip() for x in re.split(r"\n## ", text) if x.strip()]
            for i, part in enumerate(parts):
                self.chunks.append(Chunk(path.stem, part.splitlines()[0][:80], f"{path.stem}-{i}", part))
        corpus = [tokenize(c.text) for c in self.chunks]
        self._bm25 = BM25Okapi(corpus) if corpus else None

    def _bm25_search(self, query: str, k: int) -> list[dict]:
        if not self._bm25:
            return []
        scores = self._bm25.get_scores(tokenize(query))
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        result = []
        for idx, score in ranked:
            if score <= 0:
                continue
            c = self.chunks[idx]
            result.append({"document":c.document,"section":c.section,"chunk_id":c.chunk_id,"relevance":float(score),"text":c.text,"retriever":"bm25"})
            if len(result) >= k:
                break
        return result

    def _semantic_search(self, query: str, k: int) -> list[dict]:
        if not settings.semantic_rag_enabled:
            return []
        try:
            from qdrant_client import QdrantClient
            from sentence_transformers import SentenceTransformer
            if self._embedding_model is None:
                self._embedding_model = SentenceTransformer(settings.embedding_model)
            vector = self._embedding_model.encode(query, normalize_embeddings=True).tolist()
            client = QdrantClient(url=settings.qdrant_url)
            response = client.query_points(
                collection_name=settings.qdrant_collection, query=vector, limit=k
            ).points
            return [{
                "document": p.payload.get("document", "uploaded"),
                "section": p.payload.get("name", "Uploaded policy"),
                "chunk_id": p.payload.get("chunk_id", str(p.id)),
                "relevance": float(p.score),
                "text": p.payload.get("text", ""),
                "retriever": "semantic",
            } for p in response]
        except Exception:
            return []

    def search(self, query: str, k: int = 5):
        lexical = self._bm25_search(query, max(k * 2, 10))
        semantic = self._semantic_search(query, max(k * 2, 10))
        if not semantic:
            return [{**x, "relevance": round(x["relevance"], 4)} for x in lexical[:k]]

        # Reciprocal Rank Fusion: robustly combines lexical and semantic rankings
        fused: dict[str, dict] = {}
        for ranking in (lexical, semantic):
            for rank, item in enumerate(ranking, start=1):
                key = item["chunk_id"]
                if key not in fused:
                    fused[key] = {**item, "rrf_score": 0.0, "retriever": "hybrid"}
                fused[key]["rrf_score"] += 1.0 / (60 + rank)
        ranked = sorted(fused.values(), key=lambda x: x["rrf_score"], reverse=True)[:k]
        return [{**x, "relevance": round(x.pop("rrf_score"), 6)} for x in ranked]

rag_service = RAGService()

from dataclasses import dataclass
from pathlib import Path
import re
from rank_bm25 import BM25Okapi

@dataclass
class Chunk:
    document: str
    section: str
    chunk_id: str
    text: str

def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())

class RAGService:
    """Local BM25 retriever used as the reliable baseline.

    Production semantic retrieval can be added behind the same interface without
    changing agents or API routes. Keeping the baseline deterministic makes tests
    and degraded operation predictable.
    """
    def __init__(self):
        self.chunks: list[Chunk] = []
        self._bm25: BM25Okapi | None = None
        self.reload()

    def reload(self):
        self.chunks.clear()
        base = Path(__file__).resolve().parents[2] / "data" / "policies"
        for path in sorted(base.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            parts = [x.strip() for x in re.split(r"\n## ", text) if x.strip()]
            for i, part in enumerate(parts):
                self.chunks.append(Chunk(
                    document=path.stem,
                    section=part.splitlines()[0][:80],
                    chunk_id=f"{path.stem}-{i}",
                    text=part,
                ))
        corpus = [tokenize(c.text) for c in self.chunks]
        self._bm25 = BM25Okapi(corpus) if corpus else None

    def search(self, query: str, k: int = 5):
        if not self._bm25 or not self.chunks:
            return []
        scores = self._bm25.get_scores(tokenize(query))
        ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)
        results = []
        for idx, score in ranked:
            if score <= 0:
                continue
            c = self.chunks[idx]
            results.append({
                "document": c.document,
                "section": c.section,
                "chunk_id": c.chunk_id,
                "relevance": round(float(score), 4),
                "text": c.text,
                "retriever": "bm25",
            })
            if len(results) >= k:
                break
        return results

rag_service = RAGService()

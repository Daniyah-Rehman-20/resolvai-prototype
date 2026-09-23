from dataclasses import dataclass
from pathlib import Path
import re, math
@dataclass
class Chunk: document:str; section:str; chunk_id:str; text:str
class RAGService:
    def __init__(self): self.chunks:list[Chunk]=[]; self._load_local()
    def _load_local(self):
        base=Path(__file__).resolve().parents[2]/"data"/"policies"
        for p in sorted(base.glob("*.md")):
            txt=p.read_text(encoding="utf-8"); parts=[x.strip() for x in re.split(r"\n## ",txt) if x.strip()]
            for i,part in enumerate(parts): self.chunks.append(Chunk(p.stem,part.splitlines()[0][:80],f"{p.stem}-{i}",part))
    def search(self,query:str,k:int=5):
        q=set(re.findall(r"[a-z0-9]+",query.lower())); scored=[]
        for c in self.chunks:
            terms=re.findall(r"[a-z0-9]+",c.text.lower()); overlap=sum(1 for x in q if x in terms); score=overlap/(math.sqrt(len(terms))+1)
            if overlap: scored.append((score,c))
        scored.sort(key=lambda x:x[0],reverse=True)
        return [{"document":c.document,"section":c.section,"chunk_id":c.chunk_id,"relevance":round(s,4),"text":c.text} for s,c in scored[:k]]
rag_service=RAGService()

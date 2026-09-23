import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.rag.service import rag_service
def main():
    data=json.loads((Path(__file__).parents[1]/"data/evaluation/questions.json").read_text()); hits={1:0,3:0,5:0}; rr=[]
    for q in data:
        r=rag_service.search(q["question"],5); names=[x["document"] for x in r]; rank=next((i+1 for i,n in enumerate(names) if q["expected_policy"] in n),None)
        for k in hits: hits[k]+=int(rank is not None and rank<=k)
        rr.append(0 if rank is None else 1/rank)
    n=len(data); print({f"Recall@{k}":round(v/n,3) for k,v in hits.items()}|{"MRR":round(sum(rr)/n,3)})
if __name__=="__main__": main()

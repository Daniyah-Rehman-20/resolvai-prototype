from app.rag.service import rag_service
def test_policy_search_has_real_chunk_ids():
    r=rag_service.search("gateway success merchant failed reconciliation",3); assert r; assert all(x["chunk_id"] for x in r)

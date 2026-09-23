from app.rag.service import rag_service
class RAGAgent:
    name = "RAG Agent"
    async def run(self, query: str) -> list[dict]:
        return rag_service.search(query, 5)

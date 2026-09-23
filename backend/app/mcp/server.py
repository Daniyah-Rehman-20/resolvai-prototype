"""MCP-facing service registry. Sensitive tools delegate to the same approval-gated domain services."""
from app.rag.service import rag_service
TOOLS={"search_policy":lambda query:rag_service.search(query,5)}
def list_tools(): return sorted(TOOLS)

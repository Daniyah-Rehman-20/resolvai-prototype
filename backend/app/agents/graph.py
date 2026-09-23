"""LangGraph-compatible orchestration facade with a dependency-free fallback.

If langgraph is installed, this module can be replaced with a compiled StateGraph
without changing the agent interfaces. The fallback is intentionally explicit for
local/offline demo execution.
"""
from app.agents.transaction_agent import TransactionAgent
from app.agents.rag_agent import RAGAgent
from app.agents.resolution_agent import ResolutionAgent
from app.agents.risk import evaluate
from app.core.constants import Action

class InvestigationGraph:
    def __init__(self):
        self.transaction = TransactionAgent(); self.rag = RAGAgent(); self.resolution = ResolutionAgent()
    async def run(self, tx, question: str) -> dict:
        t = await self.transaction.run(tx)
        query = f"{tx.payment_method} {tx.overall_status} {tx.issue} {question}"
        policies = await self.rag.run(query)
        resolution = await self.resolution.run(tx, t["issue_type"])
        risk, approval = evaluate(Action(resolution["recommended_action"]), tx.amount)
        return {**t, **resolution, "policy_evidence": policies, "risk_level": risk, "approval_required": approval}

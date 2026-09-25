from typing import Any, TypedDict
from langgraph.graph import END, StateGraph
from app.agents.transaction_agent import TransactionAgent
from app.agents.rag_agent import RAGAgent
from app.agents.resolution_agent import ResolutionAgent
from app.agents.risk import evaluate
from app.core.constants import Action

class InvestigationState(TypedDict, total=False):
    tx: Any
    question: str
    issue_type: str
    evidence: list[str]
    policy_evidence: list[dict]
    recommended_action: str
    risk_level: str
    approval_required: bool

class InvestigationGraph:
    def __init__(self):
        self.transaction = TransactionAgent()
        self.rag = RAGAgent()
        self.resolution = ResolutionAgent()

        workflow = StateGraph(InvestigationState)
        workflow.add_node("transaction", self._transaction_node)
        workflow.add_node("rag", self._rag_node)
        workflow.add_node("resolution", self._resolution_node)
        workflow.add_node("risk", self._risk_node)
        workflow.set_entry_point("transaction")
        workflow.add_edge("transaction", "rag")
        workflow.add_edge("rag", "resolution")
        workflow.add_edge("resolution", "risk")
        workflow.add_edge("risk", END)
        self.app = workflow.compile()

    async def _transaction_node(self, state: InvestigationState):
        return await self.transaction.run(state["tx"])

    async def _rag_node(self, state: InvestigationState):
        tx = state["tx"]
        query = f'{tx.payment_method} {tx.overall_status} {tx.issue} {state["question"]}'
        return {"policy_evidence": await self.rag.run(query)}

    async def _resolution_node(self, state: InvestigationState):
        return await self.resolution.run(state["tx"], state["issue_type"])

    async def _risk_node(self, state: InvestigationState):
        risk, approval = evaluate(
            Action(state["recommended_action"]), state["tx"].amount
        )
        return {"risk_level": risk, "approval_required": approval}

    async def run(self, tx, question: str) -> dict:
        state = await self.app.ainvoke({"tx": tx, "question": question})
        state.pop("tx", None)
        state.pop("question", None)
        return state

investigation_graph = InvestigationGraph()

from typing import TypedDict

class InvestigationState(TypedDict, total=False):
    transaction_id: str
    question: str
    transaction_evidence: list[str]
    policy_evidence: list[dict]
    issue_type: str
    recommended_action: str
    risk_level: str
    approval_required: bool
    summary: str
    likely_cause: str

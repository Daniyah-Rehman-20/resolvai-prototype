from app.core.constants import Action
class ResolutionAgent:
    name = "Resolution Agent"
    async def run(self, tx, issue_type: str) -> dict:
        if tx.payment_method == "UPI" and tx.overall_status == "PENDING": action = Action.WAIT_AND_RECHECK
        elif issue_type == "STATE_MISMATCH": action = Action.RECONCILE
        elif "duplicate" in tx.issue.lower(): action = Action.SIMULATED_REFUND
        elif tx.overall_status == "DISPUTED": action = Action.CREATE_DISPUTE
        elif tx.overall_status in {"SUCCESS", "REFUNDED"}: action = Action.NO_ACTION
        else: action = Action.ESCALATE
        return {"recommended_action": action.value}

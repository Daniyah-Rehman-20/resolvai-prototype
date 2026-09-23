from app.core.constants import Action, SENSITIVE_ACTIONS
def evaluate(action:Action, amount:float|None=None)->tuple[str,bool]:
    if action in SENSITIVE_ACTIONS: return ("HIGH" if (amount or 0)>=5000 else "MEDIUM", True)
    if action==Action.ESCALATE: return "LOW", False
    return "LOW", False

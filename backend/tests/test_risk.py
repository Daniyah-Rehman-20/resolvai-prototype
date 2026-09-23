from app.agents.risk import evaluate
from app.core.constants import Action
def test_refund_requires_approval(): assert evaluate(Action.SIMULATED_REFUND,2000)[1] is True
def test_readlike_no_action_no_approval(): assert evaluate(Action.NO_ACTION)[1] is False

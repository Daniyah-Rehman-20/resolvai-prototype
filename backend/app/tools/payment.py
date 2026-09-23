from typing import Literal
class MockPaymentGateway:
    async def get_status(self,transaction_id:str): return {"transaction_id":transaction_id,"status":"DEMO_ONLY"}
    async def request_refund(self,transaction_id:str,amount:float): return {"action":"SIMULATED_REFUND","transaction_id":transaction_id,"amount":amount,"status":"SIMULATED_SUCCESS"}
    async def request_reversal(self,transaction_id:str): return {"action":"SIMULATED_REVERSAL","transaction_id":transaction_id,"status":"SIMULATED_SUCCESS"}
gateway=MockPaymentGateway()

class TransactionAgent:
    name = "Transaction Agent"
    async def run(self, tx) -> dict:
        mismatch = tx.bank_status == "DEBITED" and tx.gateway_status == "SUCCESS" and tx.merchant_status == "FAILED"
        return {
            "issue_type": "STATE_MISMATCH" if mismatch else tx.overall_status,
            "evidence": [
                f"Bank: {tx.bank_status}", f"Gateway: {tx.gateway_status}",
                f"Merchant: {tx.merchant_status}", f"Order: {tx.order.status}",
            ],
        }

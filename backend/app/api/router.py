from fastapi import APIRouter
from app.api.routes import (
    health,
    transactions,
    investigations,
    approvals,
    disputes,
    documents,
    analytics,
    chat,
    audit,
    demo,
    metrics,
    auth,
    support,
    voice,
    telephony,
)

router=APIRouter()

for r in [
    health.router,
    transactions.router,
    investigations.router,
    approvals.router,
    disputes.router,
    documents.router,
    analytics.router,
    chat.router,
    audit.router,
    demo.router,
    metrics.router,
    auth.router,
    support.router,
    voice.router,
    telephony.router,
]:
    router.include_router(r)

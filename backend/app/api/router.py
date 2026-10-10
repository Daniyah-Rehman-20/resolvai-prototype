from fastapi import APIRouter

from app.api.routes import audit, auth, health, metrics, support, telephony, voice

router = APIRouter()

for route in (
    health.router,
    metrics.router,
    auth.router,
    support.router,
    voice.router,
    telephony.router,
    audit.router,
):
    router.include_router(route)

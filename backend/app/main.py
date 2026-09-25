import time
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.exceptions import DomainError, domain_exception_handler
from app.api.router import router
from app.core.rate_limit import enforce_rate_limit

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url="/redoc" if settings.app_env != "production" else None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Correlation-ID", "X-Demo-Role", "X-Demo-User", "Idempotency-Key"],
)
app.add_exception_handler(DomainError, domain_exception_handler)

@app.middleware("http")
async def correlation(request: Request, call_next):
    await enforce_rate_limit(request)
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["X-Process-Time-Ms"] = str(int((time.perf_counter() - started) * 1000))
    return response

# Database schema creation is intentionally NOT performed here.
# Run `alembic upgrade head` before starting the API.
app.include_router(router)

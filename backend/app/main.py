import uuid,time
from fastapi import FastAPI,Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.exceptions import DomainError,domain_exception_handler
from app.api.router import router
from app.db.base import Base
from app.db.session import engine
app=FastAPI(title=settings.app_name,version=settings.version,docs_url="/docs",redoc_url="/redoc")
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origins,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
app.add_exception_handler(DomainError,domain_exception_handler)
@app.middleware("http")
async def correlation(request:Request,call_next):
    request.state.correlation_id=request.headers.get("X-Correlation-ID",str(uuid.uuid4())); started=time.perf_counter(); response=await call_next(request); response.headers["X-Correlation-ID"]=request.state.correlation_id; response.headers["X-Content-Type-Options"]="nosniff"; response.headers["X-Frame-Options"]="DENY"; response.headers["X-Process-Time-Ms"]=str(int((time.perf_counter()-started)*1000)); return response
@app.on_event("startup")
async def startup():
    async with engine.begin() as c: await c.run_sync(Base.metadata.create_all)
app.include_router(router)

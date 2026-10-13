from contextlib import asynccontextmanager
import asyncio
import json
import logging
from time import perf_counter
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import api_router, api_v1_router
from app.api.auctions import websocket_router
from app.core.config import settings
from app.core.database import Base, engine, get_db
from app.models import AuditLog, Auction, Bid, Motorcycle, Notification, RefreshToken, User
from app.services.lifecycle import auction_lifecycle
from app.services.seed import seed_demo_data

logger = logging.getLogger("bikebid.request")


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.AUTO_CREATE_SCHEMA:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    await seed_demo_data()
    lifecycle_task = auction_lifecycle.start()
    try:
        yield
    finally:
        lifecycle_task.cancel()
        try:
            await lifecycle_task
        except asyncio.CancelledError:
            pass
        await engine.dispose()

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def request_context_middleware(request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    started_at = perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        json.dumps(
            {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round((perf_counter() - started_at) * 1000, 2),
            },
            separators=(",", ":"),
        )
    )
    return response

app.include_router(api_router, prefix="/api")
app.include_router(api_v1_router, prefix="/api/v1")
app.include_router(websocket_router)


@app.get("/api/health", tags=["health"])
@app.get("/api/v1/health", tags=["health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.exception("Database readiness check failed")
        raise HTTPException(status_code=503, detail="Database is unavailable") from exc
    return {"status": "ok", "database": "ready"}


@app.get("/health/live", tags=["health"])
async def liveness_check():
    return {"status": "ok"}

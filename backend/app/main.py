from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from .config import settings
from .db import engine
from .api.competitors import router as competitors_router
from .api.articles import router as articles_router
from .api.analytics import router as analytics_router
from .api.auth import router as auth_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()

app = FastAPI(title="Signalwatch API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_url], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(competitors_router)
app.include_router(articles_router)
app.include_router(analytics_router)
app.include_router(auth_router)

@app.get("/api/health")
async def health():
    database = "ok"
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:
        database = "unavailable"
    return {"status": "ok", "database": database, "redis": "configured" if settings.redis_url else "unavailable"}

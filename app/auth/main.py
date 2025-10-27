# app/auth/main.py
from fastapi import FastAPI
from .api.routers import router as auth_router
from contextlib import asynccontextmanager
from common.clients.redis_manager import init_redis, close_redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_redis()
    yield
    # Shutdown
    await close_redis()

app = FastAPI(title="Auth Service", version="1.0.0", lifespan=lifespan)
app.include_router(auth_router, prefix="/auth", tags=["Auth"])

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "message": "Auth service is running!"}

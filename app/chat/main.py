from fastapi import FastAPI
from .api.routers import router as chat_router
from contextlib import asynccontextmanager
from common.clients.redis_manager import init_redis, close_redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_redis()
    yield
    # Shutdown
    await close_redis()

app = FastAPI(title="Chat Service", version="1.0.0", lifespan=lifespan)
app.include_router(chat_router, prefix="/chat", tags=["Chat"])

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "message": "Chat service is running!"}

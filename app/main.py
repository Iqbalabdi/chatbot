from app.chat import init_chat
from app.auth import init_auth
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from common.clients.redis_manager import init_redis, close_redis
from app.chat.api.routers import router as chat_router
from common.exceptions.exception_handlers import register_exception_handlers
from common.logging.logger import init_logging, get_logger

init_logging()
logger = get_logger(__name__)
logger.info("Starting Chatbot API...")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_redis()
    yield
    # Shutdown
    await close_redis()

app = FastAPI(
    title="Chatbot Backend API",
    version="1.1.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
init_chat(app)
init_auth(app)

# Common exception handlers
register_exception_handlers(app)

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "message": "Chatbot API is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=9000, reload=True)
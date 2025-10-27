from fastapi import FastAPI
from .api.routers import router as chat_router

def init_chat(app: FastAPI):
    app.include_router(chat_router, prefix="/chat", tags=["Chat"])
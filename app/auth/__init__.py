from fastapi import FastAPI
from .api.routers import router as auth_router

def init_auth(app: FastAPI):
    app.include_router(auth_router, prefix="/auth", tags=["Auth"])
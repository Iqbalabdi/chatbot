#/common/exceptions/excetpion_handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse
from common.exceptions.exceptions import AppError
import logging

logger = logging.getLogger(__name__)

def register_exception_handlers(app):
    """Register global exception handlers for FastAPI app."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        logger.error(f"[AppError] {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"[Unhandled Exception] {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"},
        )
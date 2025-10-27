#/common/exceptions/exceptions.py
class AppError(Exception):
    """Base class for all custom application exceptions."""
    def __init__(self, detail: str = "An application error occurred", status_code: int = 500):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)

# Domain-agnostic or reusable service errors
class ServiceError(AppError):
    """Errors from external services (like LLM, database, etc.)"""
    def __init__(self, detail: str = "Service unavailable", status_code: int = 503):
        super().__init__(detail, status_code)

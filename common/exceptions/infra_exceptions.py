from common.exceptions.exceptions import AppError

class InfraError(AppError):
    """Base class for infrastructure-related errors."""
    pass

class RedisError(InfraError):
    """Redis client failure."""
    def __init__(self, detail: str = "Redis client error"):
        super().__init__(detail=detail, status_code=500)

class RateLimitError(AppError):
    """Raised when a user exceeds rate limit"""
    def __init__(self, detail: str = "Too many requests"):
        super().__init__(detail=detail, status_code=429)
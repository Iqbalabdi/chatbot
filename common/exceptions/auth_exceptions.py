#/common/exceptions/auth_exceptions.py
from common.exceptions.exceptions import AppError

class AuthError(AppError):
    """Base class for authentication/authorization errors."""
    def __init__(self, detail: str = "Authentication failed", status_code: int = 401):
        super().__init__(detail=detail, status_code=status_code)


class TokenExpiredError(AuthError):
    """JWT token expired or invalid."""
    def __init__(self, detail: str = "Token expired or invalid"):
        super().__init__(detail=detail, status_code=401)


class PermissionDeniedError(AuthError):
    """User does not have permission to access the resource."""
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(detail=detail, status_code=403)
#/common/exceptions/chat_exceptions.py
from common.exceptions.exceptions import AppError

class ChatError(AppError):
    """Base class for chat domain errors."""
    pass

class LLMError(ChatError):
    """LLM service failure."""
    def __init__(self, detail: str = "LLM service unavailable"):
        super().__init__(detail=detail, status_code=503)

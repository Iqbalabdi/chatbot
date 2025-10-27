from app.auth.service.auth_service import get_current_user
from fastapi import APIRouter, WebSocket, Query, Depends
from fastapi.responses import StreamingResponse
from typing import Optional
from app.chat.service.chat_service import ChatService
from app.chat.models.chat_models import ChatRequest
from app.chat.service.rate_limiter_service import rate_limiter

router = APIRouter()
chat_service = ChatService()

# REST API - Non-streaming / Streaming
@router.post("/message")
async def send_message(
    request: ChatRequest, 
    stream: Optional[bool] = False,
    user_id: str = Depends(get_current_user),  
    _ = Depends(rate_limiter)
):
    if stream:
        generator = chat_service.stream_message(user_id=request.user_id, message=request.message)
        return StreamingResponse(generator, media_type="application/json")
    else:
        return await chat_service.handle_message(user_id=request.user_id, message=request.message)

# WebSocket API
@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    """Real-time chat via WebSocket."""
    await chat_service.handle_websocket(websocket)
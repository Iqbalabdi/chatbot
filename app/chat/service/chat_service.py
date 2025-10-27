from app.chat.repository.chat_repository import ChatRepository
from app.chat.adapters.llm_adapter import LLMAdapter
from app.chat.models.chat_models import ChatMessage, ChatResponse, StreamChunk, ChatRequest
from fastapi import WebSocket, WebSocketDisconnect
from typing import AsyncGenerator
import json
import logging
from common.exceptions.chat_exceptions import ChatError, LLMError
from common.exceptions.infra_exceptions import RedisError

logger = logging.getLogger(__name__)

class ChatService:

    def __init__(self):
        self.repo = ChatRepository()
        self.llm = LLMAdapter()

    async def handle_message(self, user_id: str, message: str) -> ChatResponse:
        try:
            await self.repo.append_message(user_id, ChatMessage(role="user", content=message))
            session = await self.repo.get_session(user_id)
            reply = await self.llm.generate(message, session.history)
            await self.repo.append_message(user_id, ChatMessage(role="assistant", content=reply))
            return ChatResponse(user_id=user_id, reply=reply)
        except (RedisError, LLMError, ChatError) as e:
            logger.error(f"[handle_message] {e}")
            raise e

    async def stream_message(self, user_id: str, message: str) -> AsyncGenerator[str, None]:
        try:
            await self.repo.append_message(user_id, ChatMessage(role="user", content=message))
            session = await self.repo.get_session(user_id)
            async for token in self.llm.stream_generate(message, session.history):
                yield json.dumps(StreamChunk(token=token).model_dump()) + "\n"
            await self.repo.append_message(user_id, ChatMessage(role="assistant", content="[streamed response]"))
        except (RedisError, LLMError, ChatError) as e:
            logger.error(f"[stream_message] {e}")
            raise e

    async def handle_websocket(self, websocket: WebSocket):
        await websocket.accept()
        user_id = None
        try:
            while True:
                data = await websocket.receive_json()
                req = ChatRequest(**data)
                user_id = req.user_id
                await self.repo.append_message(user_id, ChatMessage(role="user", content=req.message))
                session = await self.repo.get_session(user_id)
                async for token in self.llm.stream_generate(req.message, session.history):
                    await websocket.send_json(StreamChunk(token=token).model_dump())
                await websocket.send_json(StreamChunk(token="", is_final=True).model_dump())
                await self.repo.append_message(user_id, ChatMessage(role="assistant", content="[streamed response]"))
        except WebSocketDisconnect:
            logger.info(f"User {user_id or 'unknown'} disconnected")
        except (RedisError, LLMError, ChatError) as e:
            logger.error(f"[WebSocket] {e}")
            await websocket.send_json({"error": str(e)})

import json
from typing import List
from app.chat.models.chat_models import ChatMessage, ChatSession
from common.clients.redis_manager import get_redis
from common.exceptions.chat_exceptions import ChatError
from common.exceptions.infra_exceptions import RedisError
import logging

logger = logging.getLogger(__name__)

MAX_HISTORY = 50  # Keep last 50 messages per session

class ChatRepository:
    def __init__(self):
        self.prefix = "chat_session:"

    def _key(self, user_id: str) -> str:
        return f"{self.prefix}{user_id}"

    async def get_session(self, user_id: str) -> ChatSession:
        try:
            redis = await get_redis()
        except RedisError as e:
            raise e

        try:
            # get all messages in list
            messages_json: List[str] = await redis.lrange(self._key(user_id), 0, -1)
            messages = [ChatMessage(**json.loads(msg)) for msg in messages_json]
            return ChatSession(user_id=user_id, history=messages)
        except json.JSONDecodeError:
            # session data corrupted
            await redis.delete(self._key(user_id))
            raise ChatError("Corrupted session data cleared.")
        except Exception as e:
            logger.error(f"[ChatRepository] Unexpected error in get_session: {e}")
            raise ChatError(str(e))

    async def append_message(self, user_id: str, message: ChatMessage):
        try:
            redis = await get_redis()
        except RedisError as e:
            raise e

        key = self._key(user_id)
        try:
            await redis.rpush(key, json.dumps(message.model_dump()))
            # keep only last MAX_HISTORY messages
            await redis.ltrim(key, -MAX_HISTORY, -1)
        except Exception as e:
            logger.error(f"[ChatRepository] Failed to append message: {e}")
            raise ChatError("Failed to append message to session.")
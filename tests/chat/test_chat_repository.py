import pytest
import json
from unittest.mock import AsyncMock, patch
from app.chat.repository.chat_repository import ChatRepository, MAX_HISTORY
from app.chat.models.chat_models import ChatMessage, ChatSession
from common.exceptions.chat_exceptions import ChatError
from common.exceptions.infra_exceptions import RedisError

@pytest.mark.asyncio
class TestChatRepository:

    @patch("app.chat.repository.chat_repository.get_redis")
    async def test_getSession_WhenDataExists_ReturnsChatSession(self, mock_get_redis):
        # Arrange
        fake_redis = AsyncMock()
        mock_get_redis.return_value = fake_redis
        fake_redis.lrange.return_value = [
            json.dumps({"role": "user", "content": "hi"}),
            json.dumps({"role": "assistant", "content": "hello!"}),
        ]
        repo = ChatRepository()

        # Act
        session = await repo.get_session("u1")

        # Assert
        mock_get_redis.assert_awaited_once()
        fake_redis.lrange.assert_awaited_once_with("chat_session:u1", 0, -1)
        assert isinstance(session, ChatSession)
        assert session.user_id == "u1"
        assert len(session.history) == 2
        assert session.history[0].content == "hi"


    @patch("app.chat.repository.chat_repository.get_redis")
    async def test_getSession_WhenRedisRaisesRedisError_RaisesSame(self, mock_get_redis):
        # Arrange
        mock_get_redis.side_effect = RedisError("redis down")
        repo = ChatRepository()

        # Act & Assert
        with pytest.raises(RedisError):
            await repo.get_session("u1")


    @patch("app.chat.repository.chat_repository.get_redis")
    async def test_getSession_WhenCorruptedJson_DeletesKeyAndRaisesChatError(self, mock_get_redis):
        # Arrange
        fake_redis = AsyncMock()
        mock_get_redis.return_value = fake_redis
        fake_redis.lrange.return_value = ["{bad json"]
        repo = ChatRepository()

        # Act
        with pytest.raises(ChatError) as exc:
            await repo.get_session("u1")
        
        # Assert
        fake_redis.delete.assert_awaited_once_with("chat_session:u1")
        assert "Corrupted session data" in str(exc.value)


    @patch("app.chat.repository.chat_repository.get_redis")
    async def test_getSession_WhenUnexpectedError_RaisesChatError(self, mock_get_redis):
        # Arrange
        fake_redis = AsyncMock()
        mock_get_redis.return_value = fake_redis
        fake_redis.lrange.side_effect = RuntimeError("boom")
        repo = ChatRepository()

        # Act & Assert
        with pytest.raises(ChatError):
            await repo.get_session("u1")


    @patch("app.chat.repository.chat_repository.get_redis")
    async def test_appendMessage_WhenValid_CallsRedisWithCorrectArgs(self, mock_get_redis):
        # Arrange
        fake_redis = AsyncMock()
        mock_get_redis.return_value = fake_redis
        repo = ChatRepository()
        msg = ChatMessage(role="user", content="hello")

        # Act
        await repo.append_message("u1", msg)

        # Assert
        key = "chat_session:u1"
        fake_redis.rpush.assert_awaited_once_with(key, json.dumps(msg.model_dump()))
        fake_redis.ltrim.assert_awaited_once_with(key, -MAX_HISTORY, -1)


    @patch("app.chat.repository.chat_repository.get_redis")
    async def test_appendMessage_WhenRedisRaisesRedisError_RaisesSame(self, mock_get_redis):
        # Arrange
        mock_get_redis.side_effect = RedisError("redis fail")
        repo = ChatRepository()

        # Act & Assert
        with pytest.raises(RedisError):
            await repo.append_message("u1", ChatMessage(role="user", content="hi"))


    @patch("app.chat.repository.chat_repository.get_redis")
    async def test_appendMessage_WhenRedisFailsDuringPush_RaisesChatError(self, mock_get_redis):
        # Arrange
        fake_redis = AsyncMock()
        mock_get_redis.return_value = fake_redis
        fake_redis.rpush.side_effect = Exception("rpush fail")
        repo = ChatRepository()

        # Act & Assert
        with pytest.raises(ChatError) as exc:
            await repo.append_message("u1", ChatMessage(role="user", content="hi"))

        assert "Failed to append message" in str(exc.value)

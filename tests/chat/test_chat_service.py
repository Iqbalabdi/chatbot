import pytest
import json
from unittest.mock import AsyncMock, Mock, patch
from app.chat.service.chat_service import ChatService
from app.chat.models.chat_models import ChatMessage, ChatResponse
from common.exceptions.chat_exceptions import ChatError, LLMError
from common.exceptions.infra_exceptions import RedisError
from fastapi import WebSocketDisconnect

@pytest.mark.asyncio
class TestChatService:
    @patch("app.chat.service.chat_service.ChatRepository")
    @patch("app.chat.service.chat_service.LLMAdapter")
    async def test_handleMessage_WhenValidInput_ReturnsExpectedResponse(self, mock_llm_cls, mock_repo_cls):
        # Arrange
        mock_repo = mock_repo_cls.return_value
        mock_llm = mock_llm_cls.return_value

        # ✅ Make async mocks for awaited methods
        mock_repo.append_message = AsyncMock()
        mock_repo.get_session = AsyncMock(return_value=Mock(history=["prev"]))
        mock_llm.generate = AsyncMock(return_value="hi there")

        service = ChatService()

        # Act
        result = await service.handle_message("u1", "hello")

        # Assert
        mock_repo.append_message.assert_any_await("u1", ChatMessage(role="user", content="hello"))
        mock_repo.append_message.assert_any_await("u1", ChatMessage(role="assistant", content="hi there"))
        mock_llm.generate.assert_awaited_once_with("hello", ["prev"])

        assert isinstance(result, ChatResponse)
        assert result.reply == "hi there"

    @pytest.mark.parametrize("error", [RedisError("redis fail"), LLMError("llm fail"), ChatError("chat fail")])
    @patch("app.chat.service.chat_service.ChatRepository")
    @patch("app.chat.service.chat_service.LLMAdapter")
    async def test_handleMessage_WhenDependencyThrowsError_RaisesSameException(self, mock_llm_cls, mock_repo_cls, error):
        # Arrange
        mock_repo = mock_repo_cls.return_value
        mock_repo.append_message = AsyncMock(side_effect=error)
        mock_repo.get_session = AsyncMock()
        service = ChatService()

        # Act & Assert
        with pytest.raises(type(error)):
            await service.handle_message("u1", "msg")

    @patch("app.chat.service.chat_service.ChatRepository")
    @patch("app.chat.service.chat_service.LLMAdapter")
    async def test_streamMessage_WhenValidInput_YieldsExpectedChunks(self, mock_llm_cls, mock_repo_cls):
        # Arrange
        mock_repo = mock_repo_cls.return_value
        mock_llm = mock_llm_cls.return_value

        mock_repo.append_message = AsyncMock()
        mock_repo.get_session = AsyncMock(return_value=Mock(history=["prev"]))
        mock_llm.stream_generate = self.async_mock_gen(["hi", "there"])

        service = ChatService()

        # Act
        gen = service.stream_message("u1", "hello")
        chunks = [json.loads(c) for c in [x async for x in gen]]

        # Assert
        assert chunks == [
            {"token": "hi", "is_final": False},
            {"token": "there", "is_final": False},
        ]
        mock_repo.append_message.assert_any_await("u1", ChatMessage(role="user", content="hello"))
        mock_repo.append_message.assert_any_await("u1", ChatMessage(role="assistant", content="[streamed response]"))

    @pytest.mark.parametrize("error", [RedisError("redis fail"), LLMError("llm fail"), ChatError("chat fail")])
    @patch("app.chat.service.chat_service.ChatRepository")
    @patch("app.chat.service.chat_service.LLMAdapter")
    async def test_streamMessage_WhenDependencyThrowsError_RaisesSameException(self, mock_llm_cls, mock_repo_cls, error):
        # Arrange
        mock_repo = mock_repo_cls.return_value
        mock_repo.append_message = AsyncMock(side_effect=error)
        mock_repo.get_session = AsyncMock()
        service = ChatService()

        # Act & Assert
        with pytest.raises(type(error)):
            async for _ in service.stream_message("u1", "msg"):
                pass

    @patch("app.chat.service.chat_service.ChatRepository")
    @patch("app.chat.service.chat_service.LLMAdapter")
    async def test_handleWebSocket_WhenClientSendsMessage_SendsStreamAndFinalResponse(self, mock_llm_cls, mock_repo_cls):
        # Arrange
        mock_repo = mock_repo_cls.return_value
        mock_llm = mock_llm_cls.return_value

        mock_repo.append_message = AsyncMock()
        mock_repo.get_session = AsyncMock(return_value=Mock(history=["prev"]))
        mock_llm.stream_generate = self.async_mock_gen(["hi", "there"])

        mock_ws = AsyncMock()
        # Simulate one message, then disconnect
        mock_ws.receive_json.side_effect = [
            {"user_id": "u1", "message": "hi"},
            WebSocketDisconnect(),
        ]

        service = ChatService()

        # Act
        await service.handle_websocket(mock_ws)

        # Assert
        mock_ws.accept.assert_awaited_once()
        mock_ws.send_json.assert_any_await({"token": "hi", "is_final": False})
        mock_ws.send_json.assert_any_await({"token": "there", "is_final": False})
        mock_ws.send_json.assert_any_await({"token": "", "is_final": True})

    @patch("app.chat.service.chat_service.ChatRepository")
    @patch("app.chat.service.chat_service.LLMAdapter")
    async def test_handleWebSocket_WhenClientDisconnects_HandlesGracefully(self, mock_llm_cls, mock_repo_cls):
        # Arrange
        mock_repo = mock_repo_cls.return_value
        mock_repo.append_message = AsyncMock()
        mock_repo.get_session = AsyncMock()

        mock_ws = AsyncMock()
        mock_ws.receive_json.side_effect = WebSocketDisconnect()

        service = ChatService()

        # Act
        await service.handle_websocket(mock_ws)

        # Assert
        mock_ws.accept.assert_awaited_once()

    @patch("app.chat.service.chat_service.ChatRepository")
    @patch("app.chat.service.chat_service.LLMAdapter")
    async def test_handleWebSocket_WhenErrorOccurs_SendsErrorMessage(self, mock_llm_cls, mock_repo_cls):
        # Arrange
        mock_repo = mock_repo_cls.return_value
        mock_repo.append_message = AsyncMock(side_effect=RedisError("boom"))
        mock_repo.get_session = AsyncMock()

        mock_ws = AsyncMock()
        mock_ws.receive_json.side_effect = [{"user_id": "u1", "message": "hi"}]

        service = ChatService()

        # Act
        await service.handle_websocket(mock_ws)

        # Assert
        mock_ws.send_json.assert_any_await({"error": "boom"})
    
    def async_mock_gen(self, values):
        """Return a callable async generator for mocking stream_generate()."""
        async def gen_func(*args, **kwargs):
            for v in values:
                yield v
        return lambda *a, **kw: gen_func(*a, **kw)

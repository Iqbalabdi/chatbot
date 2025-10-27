import pytest
from unittest.mock import AsyncMock, patch
from fastapi.responses import StreamingResponse
from app.chat.api.routers import send_message
from app.chat.models.chat_models import ChatRequest

@pytest.mark.asyncio
class TestChatApi:
    @patch("app.chat.api.routers.get_current_user", return_value="mock_user")
    @patch("app.chat.api.routers.chat_service")
    async def test_sendMessage_WhenNonStreaming_ReturnsExpectedResponse(self, mock_service, mock_user):
        # Arrange
        mock_service.handle_message = AsyncMock(return_value={"response": "Hello, user!"})
        request = type("obj", (object,), {"user_id": "mock_user", "message": "Hello!"})()

        # Act
        response = await send_message(request=request, stream=False)

        # Assert
        assert response == {"response": "Hello, user!"}

    @patch("app.chat.api.routers.get_current_user", return_value="mock_user")
    @patch("app.chat.api.routers.chat_service")
    async def test_sendMessage_WhenStreaming_ReturnsStreamingResponse(self, mock_service, mock_user):
        # Arrange
        async def fake_stream():
            yield '{"response": "Hello!"}'
        mock_service.stream_message.return_value = fake_stream()
        request = ChatRequest(user_id="mock_user", message="Hi")

        # Act
        response = await send_message(request=request, stream=True)

        # Assert
        assert isinstance(response, StreamingResponse)
        mock_service.stream_message.assert_called_once_with(user_id="mock_user", message="Hi")


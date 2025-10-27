import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from app.chat.adapters.llm_adapter import LLMAdapter
from app.chat.models.chat_models import ChatMessage
from common.exceptions.chat_exceptions import LLMError

@pytest.mark.asyncio
class TestLLMAdapter:

    @patch("app.chat.adapters.llm_adapter.httpx.AsyncClient", autospec=True)
    async def test_generate_WhenValidResponse_ReturnsMessageContent(self, mock_client_cls):
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Hello!"}}
        mock_response.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        llm = LLMAdapter()
        history = [ChatMessage(role="user", content="hi")]

        # Act
        result = await llm.generate("how are you?", history)

        # Assert
        assert result == "Hello!"
        mock_client.post.assert_awaited_once()

    @patch("app.chat.adapters.llm_adapter.httpx.AsyncClient")
    @patch("app.chat.adapters.llm_adapter.asyncio.sleep", new_callable=AsyncMock)
    async def test_generate_WhenAllRetriesFail_RaisesLLMError(self, mock_sleep, mock_client_cls):
        # Arrange
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.post.side_effect = Exception("network fail")

        adapter = LLMAdapter(retries=2)

        # Act & Assert
        with pytest.raises(LLMError) as exc:
            await adapter.generate("msg", [])

        assert "LLM service unavailable" in str(exc.value)
        assert mock_client.post.await_count == 2

    @patch("app.chat.adapters.llm_adapter.httpx.AsyncClient", autospec=True)
    async def test_streamGenerate_WhenValidStream_YieldsTokens(self, mock_client_cls):
        # Arrange
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.aiter_lines = MagicMock(return_value=_aiter([
            json.dumps({"message": {"content": "hi"}}),
            json.dumps({"message": {"content": "there"}}),
            json.dumps({"done": True}),
        ]))

        class AsyncStreamCM:
            async def __aenter__(self):
                return mock_response

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        mock_client = MagicMock()
        mock_client.stream = MagicMock(return_value=AsyncStreamCM())

        mock_client_cls.return_value.__aenter__.return_value = mock_client

        llm = LLMAdapter()
        history = [ChatMessage(role="user", content="hi")]

        # Act
        tokens = [t async for t in llm.stream_generate("how are you?", history)]

        # Assert
        assert tokens == ["hi", "there"]
        mock_client.stream.assert_called_once_with(
            "POST",
            llm.base_url,
            json={
                "model": llm.model,
                "messages": [{"role": "user", "content": "hi"}, {"role": "user", "content": "how are you?"}],
                "stream": True
            }
        )

    @patch("app.chat.adapters.llm_adapter.httpx.AsyncClient")
    async def test_streamGenerate_WhenHttpError_RaisesLLMError(self, mock_client_cls):
        # Arrange
        mock_response = AsyncMock(status_code=500)
        mock_response.aread.return_value = b"server fail"

        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_response)
        mock_stream_ctx.__aexit__ = AsyncMock(return_value=None)

        mock_client = MagicMock()
        mock_client.stream = MagicMock(return_value=mock_stream_ctx)  # ✅ FIXED
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        adapter = LLMAdapter()

        # Act & Assert
        with pytest.raises(LLMError) as exc:
            async for _ in adapter.stream_generate("msg", []):
                pass

        assert "HTTP 500" in str(exc.value)

    @patch("app.chat.adapters.llm_adapter.httpx.AsyncClient")
    async def test_streamGenerate_WhenUnexpectedError_RaisesLLMError(self, mock_client_cls):
        # Arrange
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.stream.side_effect = Exception("boom")

        adapter = LLMAdapter()

        # Act & Assert
        with pytest.raises(LLMError) as exc:
            async for _ in adapter.stream_generate("msg", []):
                pass

        assert "LLM streaming failed" in str(exc.value)

    def test_buildMessages_ReturnsExpectedList(self):
        # Arrange
        adapter = LLMAdapter()
        history = [
            ChatMessage(role="user", content="hi"),
            ChatMessage(role="assistant", content="hello"),
        ]

        # Act
        result = adapter._build_messages(history, "new message")

        # Assert
        assert result[-1] == {"role": "user", "content": "new message"}
        assert len(result) == 3

def _aiter(items):
    async def gen():
        for i in items:
            yield i
    return gen()
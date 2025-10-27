# tests/common/test_rate_limiter.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request
from app.chat.service.rate_limiter_service import rate_limiter
from common.exceptions.infra_exceptions import RateLimitError
from common.config.config import settings

@pytest.mark.asyncio
class TestRateLimiter:

    @patch("app.chat.service.rate_limiter_service.get_redis", new_callable=AsyncMock)
    async def test_rate_limiter_WhenUnderLimit_AllowsRequest(self, mock_get_redis):
        # Arrange
        mock_redis = AsyncMock()
        mock_redis.incr.return_value = 1
        mock_get_redis.return_value = mock_redis

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-User-ID": "user123"}

        # Act
        await rate_limiter(mock_request)

        # Assert
        mock_redis.incr.assert_awaited_once_with("rate_limit:user123")
        mock_redis.expire.assert_awaited_once_with("rate_limit:user123", settings.RATE_LIMIT_PERIOD)

    @patch("app.chat.service.rate_limiter_service.get_redis")
    async def test_rate_limiter_WhenExceedsLimit_RaisesRateLimitError(self, mock_get_redis):
        # Arrange
        mock_redis = AsyncMock()
        mock_redis.incr.return_value = settings.RATE_LIMIT_REQUESTS + 1
        mock_redis.expire = AsyncMock()
        
        mock_get_redis.return_value = mock_redis

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-User-ID": "user123"}

        # Act & Assert
        with pytest.raises(RateLimitError):
            await rate_limiter(mock_request)

        mock_redis.incr.assert_awaited_once_with("rate_limit:user123")

    @patch("app.chat.service.rate_limiter_service.get_redis", new_callable=AsyncMock)
    async def test_rate_limiter_WhenRedisFails_AllowsRequest(self, mock_get_redis):
        # Arrange
        mock_get_redis.side_effect = Exception("Redis down")

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-User-ID": "user123"}

        # Act & Assert
        await rate_limiter(mock_request)

    @patch("app.chat.service.rate_limiter_service.get_redis", new_callable=AsyncMock)
    async def test_rate_limiter_WhenNoUserHeader_UsesAnonymous(self, mock_get_redis):
        # Arrange
        mock_redis = AsyncMock()
        mock_redis.incr.return_value = 1
        mock_get_redis.return_value = mock_redis

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}

        # Act
        await rate_limiter(mock_request)

        # Assert
        mock_redis.incr.assert_awaited_once_with("rate_limit:anonymous")
        mock_redis.expire.assert_awaited_once_with("rate_limit:anonymous", settings.RATE_LIMIT_PERIOD)

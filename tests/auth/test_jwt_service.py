import pytest
import jwt
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from app.auth.service.jwt_service import JWTService, jwt_service
from common.config.config import settings
from common.exceptions.auth_exceptions import AuthError, TokenExpiredError

@pytest.mark.asyncio
class TestJWTService:

    def setup_method(self):
        self.service = JWTService()

    def test_create_token_WhenValidUserId_ReturnsToken(self):
        # Arrange
        user_id = "user123"

        # Act
        token = self.service.create_token(user_id)

        # Assert
        assert isinstance(token, str)
        decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert decoded.get("sub") == user_id
        
        # Check that the expiration is roughly now + expire_minutes
        exp = decoded.get("exp")
        expected_exp = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        assert abs(datetime.fromtimestamp(exp, tz=timezone.utc) - expected_exp).total_seconds() < 5

    def test_decode_token_WhenValidToken_ReturnsUserId(self):
        # Arrange
        user_id = "user123"
        token = self.service.create_token(user_id)

        # Act
        result = self.service.decode_token(token)

        # Assert
        assert result == user_id

    def test_decode_token_WhenTokenExpired_RaisesTokenExpiredError(self):
        # Arrange
        user_id = "user123"
        expired_time = datetime.now(timezone.utc) - timedelta(minutes=10)
        payload = {"sub": user_id, "exp": expired_time}
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

        # Act & Assert
        with pytest.raises(TokenExpiredError):
            self.service.decode_token(token)

    def test_decode_token_WhenTokenInvalid_RaisesAuthError(self):
        # Arrange
        invalid_token = "this.is.not.a.valid.token"

        # Act & Assert
        with pytest.raises(AuthError):
            self.service.decode_token(invalid_token)

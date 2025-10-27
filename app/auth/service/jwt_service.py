import jwt
from datetime import datetime, timedelta, timezone
from common.config.config import settings
from common.exceptions.auth_exceptions import AuthError, TokenExpiredError

class JWTService:
    def __init__(self):
        self.secret = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.expire_minutes = settings.JWT_EXPIRE_MINUTES

    def create_token(self, user_id: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.expire_minutes)
        payload = {"sub": user_id, "exp": expire}
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def decode_token(self, token: str) -> str:
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            return payload.get("sub")
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token expired")
        except jwt.PyJWTError:
            raise AuthError("Invalid authentication token")

jwt_service = JWTService()
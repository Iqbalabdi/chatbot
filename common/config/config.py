import os
import logging
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # env
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")  # dev | staging | production

    # app info
    APP_NAME: str = "Chatbot Backend API"
    APP_VERSION: str = "1.0.0"

    # redis
    REDIS_URL: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    REDIS_MAX_CONNECTIONS: int = Field(10, env="REDIS_MAX_CONNECTIONS")

    # jwt
    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field("HS256", env="JWT_ALGORITHM")
    JWT_EXPIRE_MINUTES: int = Field(60, env="JWT_EXPIRE_MINUTES")

    # rate-limiter
    RATE_LIMIT_REQUESTS: int = Field(10, env="RATE_LIMIT_REQUESTS")  # requests per period
    RATE_LIMIT_PERIOD: int = Field(1, env="RATE_LIMIT_PERIOD")       # seconds
    
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore"
    )

# env loader
def get_env_file() -> Path:
    project_root = Path(__file__).resolve().parent.parent.parent  # project root
    env = os.getenv("ENVIRONMENT", "dev").lower()  # default to dev
    env_file_path = project_root / f"env/.env.{env}"
    logger.info(f"Loading environment file: {env_file_path} (exists: {env_file_path.exists()})")
    return env_file_path

settings = Settings(_env_file=get_env_file())
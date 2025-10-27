#common/clients/redis_manager.py
import redis.asyncio as aioredis
from common.config.config import settings
from common.exceptions.infra_exceptions import RedisError

_redis = None  # internal global — private, module-level cache  

async def init_redis():
    global _redis
    if _redis is None:
        _redis = await aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            encoding="utf-8",
            max_connections=10,
        )
    return _redis

async def get_redis():
    if _redis is None:
        raise RedisError("Redis not initialized. Did you call init_redis()?") 
    return _redis

async def close_redis():
    global _redis
    if _redis:
        await _redis.close()
        _redis = None
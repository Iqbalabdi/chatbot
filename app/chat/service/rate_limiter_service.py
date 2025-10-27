from fastapi import Request
from common.clients.redis_manager import get_redis
from common.config.config import settings
from common.exceptions.infra_exceptions import RateLimitError
from common.logging.logger import get_logger

logger = get_logger(__name__)

async def rate_limiter(request: Request):
    user_id = request.headers.get("X-User-ID") or "anonymous"
    key = f"rate_limit:{user_id}"

    try:
        redis = await get_redis()
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, settings.RATE_LIMIT_PERIOD)
    except Exception as e:
        logger.error(f"[RateLimiter] Redis failure for user '{user_id}': {e}")
        return

    if count > settings.RATE_LIMIT_REQUESTS:
        logger.warning(f"[RateLimiter] User '{user_id}' exceeded rate limit")
        raise RateLimitError("Too many requests. Try again later.")

    logger.debug(f"[RateLimiter] User '{user_id}' request count: {count}")
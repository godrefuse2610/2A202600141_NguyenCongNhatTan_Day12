import redis
import time
from fastapi import HTTPException, status
from .config import settings

r = redis.from_url(settings.REDIS_URL, decode_responses=True)

async def check_rate_limit(user_id: str):
    key = f"rate_limit:{user_id}"
    now = time.time()
    window_start = now - 60
    
    # Sử dụng pipeline để đảm bảo tính nguyên tử
    pipe = r.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)
    pipe.zadd(key, {str(now): now})
    pipe.zcard(key)
    pipe.expire(key, 60)
    results = pipe.execute()
    
    request_count = results[2]
    if request_count > settings.RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again later."
        )

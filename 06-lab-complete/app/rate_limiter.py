"""
Stateless Rate Limiter using Redis
"""
import time
import redis
import logging
from collections import defaultdict, deque
from fastapi import HTTPException
from app.config import settings

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.use_redis = False
        
        if settings.redis_url:
            try:
                self.r = redis.from_url(settings.redis_url, decode_responses=True)
                self.r.ping()
                self.use_redis = True
                logger.info("RateLimiter: Using Redis")
            except Exception as e:
                logger.warning(f"RateLimiter: Redis failed, using in-memory: {e}")
        
        if not self.use_redis:
            self._windows: dict[str, deque] = defaultdict(deque)

    def check(self, key: str):
        now = time.time()
        
        if self.use_redis:
            redis_key = f"rl:{key}"
            try:
                # Use Redis pipeline for atomic operations
                pipe = self.r.pipeline()
                # Remove old timestamps
                pipe.zremrangebyscore(redis_key, 0, now - self.window_seconds)
                # Count current timestamps
                pipe.zcard(redis_key)
                # Add current timestamp
                pipe.zadd(redis_key, {str(now): now})
                # Set expiry
                pipe.expire(redis_key, self.window_seconds)
                
                results = pipe.execute()
                count = results[1]
                
                if count >= self.max_requests:
                    raise HTTPException(
                        status_code=429,
                        detail=f"Rate limit exceeded: {self.max_requests} req/min",
                        headers={"Retry-After": str(self.window_seconds)},
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Redis RateLimiter error: {e}")
                # Fallback logic could be added here if needed
        else:
            window = self._windows[key]
            while window and window[0] < now - self.window_seconds:
                window.popleft()
            
            if len(window) >= self.max_requests:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded: {self.max_requests} req/min",
                    headers={"Retry-After": str(self.window_seconds)},
                )
            window.append(now)

# Singleton
rate_limiter = RateLimiter(
    max_requests=settings.rate_limit_per_minute,
    window_seconds=60
)

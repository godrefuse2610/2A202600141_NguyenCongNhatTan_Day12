import time
import os
import redis

class RedisRateLimiter:
    def __init__(self, limit=10, window=60):
        self.limit = limit
        self.window = window
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            self.r = redis.from_url(redis_url, decode_responses=True)
            self.use_redis = True
        except Exception:
            self.use_redis = False

    def is_allowed(self, user_id):
        if not self.use_redis: return True
        key = f"vinlex:ratelimit:{user_id}"
        now = time.time()
        try:
            pipe = self.r.pipeline()
            pipe.zremrangebyscore(key, 0, now - self.window)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, self.window)
            results = pipe.execute()
            return results[1] < self.limit
        except Exception:
            return True

rate_limiter = RedisRateLimiter(limit=10, window=60)

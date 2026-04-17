import time
import os
import redis

class CostGuard:
    def __init__(self, monthly_budget=10.0):
        self.monthly_budget = monthly_budget
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            self.r = redis.from_url(redis_url, decode_responses=True)
            self.use_redis = True
        except Exception:
            self.use_redis = False

    def check_budget(self, user_id):
        if not self.use_redis: return True
        month_key = time.strftime("%Y-%m")
        key = f"vinlex:cost:{user_id}:{month_key}"
        try:
            current_cost = float(self.r.get(key) or 0.0)
            return current_cost < self.monthly_budget
        except Exception:
            return True

    def record_usage(self, user_id, cost):
        if not self.use_redis: return
        month_key = time.strftime("%Y-%m")
        key = f"vinlex:cost:{user_id}:{month_key}"
        try:
            self.r.incrbyfloat(key, cost)
            self.r.expire(key, 32 * 24 * 3600)
        except Exception:
            pass

cost_guard = CostGuard(monthly_budget=10.0)

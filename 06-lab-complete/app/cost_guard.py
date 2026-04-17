"""
Cost Guard — Stateless version using Redis
"""
import time
import redis
import logging
from fastapi import HTTPException
from app.config import settings

logger = logging.getLogger(__name__)

# Prices
PRICE_PER_1K_INPUT_TOKENS = 0.00015
PRICE_PER_1K_OUTPUT_TOKENS = 0.0006

class CostGuard:
    def __init__(self):
        self.use_redis = False
        if settings.redis_url:
            try:
                self.r = redis.from_url(settings.redis_url, decode_responses=True)
                self.r.ping()
                self.use_redis = True
                logger.info("CostGuard: Using Redis")
            except Exception as e:
                logger.warning(f"CostGuard: Redis failed, using in-memory: {e}")
        
        if not self.use_redis:
            self._daily_cost = 0.0
            self._cost_reset_day = time.strftime("%Y-%m-%d")

    def _get_keys(self, user_id: str):
        today = time.strftime("%Y-%m-%d")
        return f"cost:{user_id}:{today}", f"cost:global:{today}"

    def check_budget(self, user_id: str):
        if self.use_redis:
            user_key, global_key = self._get_keys(user_id)
            user_cost = float(self.r.get(user_key) or 0.0)
            global_cost = float(self.r.get(global_key) or 0.0)
            
            # Global limit (example $10)
            if global_cost >= 10.0:
                raise HTTPException(503, "Global budget exhausted")
            
            if user_cost >= settings.daily_budget_usd:
                raise HTTPException(402, f"User budget exceeded: ${user_cost:.4f}")
        else:
            today = time.strftime("%Y-%m-%d")
            if today != self._cost_reset_day:
                self._daily_cost = 0.0
                self._cost_reset_day = today
            
            if self._daily_cost >= settings.daily_budget_usd:
                raise HTTPException(402, "Daily budget exhausted")

    def record_usage(self, user_id: str, input_tokens: int, output_tokens: int):
        cost = (input_tokens / 1000 * PRICE_PER_1K_INPUT_TOKENS +
                output_tokens / 1000 * PRICE_PER_1K_OUTPUT_TOKENS)
        
        if self.use_redis:
            user_key, global_key = self._get_keys(user_id)
            self.r.incrbyfloat(user_key, cost)
            self.r.incrbyfloat(global_key, cost)
            self.r.expire(user_key, 32 * 3600)
            self.r.expire(global_key, 32 * 3600)
        else:
            self._daily_cost += cost
        
        return cost

# Singleton
cost_guard = CostGuard()

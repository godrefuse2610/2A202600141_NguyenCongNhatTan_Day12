"""
Cost Guard — Bảo Vệ Budget LLM

Mục tiêu: Tránh bill bất ngờ từ LLM API.
- Đếm tokens đã dùng mỗi ngày
- Cảnh báo khi gần hết budget
- Block khi vượt budget

Trong production: lưu trong Redis/DB, không phải in-memory.
"""
import time
import logging
import os
import redis
import json
from dataclasses import dataclass, field
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Giá token (tham khảo, thay đổi theo model)
PRICE_PER_1K_INPUT_TOKENS = 0.00015   # GPT-4o-mini: $0.15/1M input
PRICE_PER_1K_OUTPUT_TOKENS = 0.0006   # GPT-4o-mini: $0.60/1M output

class CostGuard:
    def __init__(
        self,
        daily_budget_usd: float = 1.0,       # $1/ngày per user
        global_daily_budget_usd: float = 10.0, # $10/ngày tổng cộng
        warn_at_pct: float = 0.8,              # Cảnh báo khi dùng 80%
    ):
        self.daily_budget_usd = daily_budget_usd
        self.global_daily_budget_usd = global_daily_budget_usd
        self.warn_at_pct = warn_at_pct
        
        # Redis connection
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.r = redis.from_url(redis_url, decode_responses=True)

    def _get_user_key(self, user_id: str) -> str:
        today = time.strftime("%Y-%m-%d")
        return f"cost:{user_id}:{today}"

    def _get_global_key(self) -> str:
        today = time.strftime("%Y-%m-%d")
        return f"cost:global:{today}"

    def _get_cost(self, key: str) -> float:
        return float(self.r.get(key) or 0.0)

    def check_budget(self, user_id: str) -> None:
        """
        Kiểm tra budget từ Redis trước khi gọi LLM.
        Raise 402 nếu vượt budget.
        """
        user_cost = self._get_cost(self._get_user_key(user_id))
        global_cost = self._get_cost(self._get_global_key())

        # Global budget check
        if global_cost >= self.global_daily_budget_usd:
            logger.critical(f"GLOBAL BUDGET EXCEEDED: ${global_cost:.4f}")
            raise HTTPException(
                status_code=503,
                detail="Service temporarily unavailable due to budget limits. Try again tomorrow.",
            )

        # Per-user budget check
        if user_cost >= self.daily_budget_usd:
            raise HTTPException(
                status_code=402,  # Payment Required
                detail={
                    "error": "Daily budget exceeded",
                    "used_usd": round(user_cost, 6),
                    "budget_usd": self.daily_budget_usd,
                    "resets_at": "midnight UTC",
                },
            )

        # Warning khi gần hết budget
        if user_cost >= self.daily_budget_usd * self.warn_at_pct:
            logger.warning(
                f"User {user_id} at {user_cost/self.daily_budget_usd*100:.0f}% budget"
            )

    def record_usage(
        self, user_id: str, input_tokens: int, output_tokens: int
    ) -> dict:
        """Ghi nhận usage vào Redis sau khi gọi LLM xong."""
        cost = (input_tokens / 1000 * PRICE_PER_1K_INPUT_TOKENS +
                output_tokens / 1000 * PRICE_PER_1K_OUTPUT_TOKENS)
        
        user_key = self._get_user_key(user_id)
        global_key = self._get_global_key()

        # Update Redis (atomic increment)
        new_user_cost = self.r.incrbyfloat(user_key, cost)
        new_global_cost = self.r.incrbyfloat(global_key, cost)
        
        # Set expiry for cleanup (32 hours to cover the next day's start)
        self.r.expire(user_key, 32 * 3600)
        self.r.expire(global_key, 32 * 3600)

        logger.info(
            f"Usage: user={user_id} added_cost=${cost:.6f} "
            f"total_user_cost=${new_user_cost:.4f}/{self.daily_budget_usd}"
        )
        
        return {
            "user_id": user_id,
            "cost_added": cost,
            "total_user_cost": new_user_cost,
            "total_global_cost": new_global_cost
        }

    def get_usage(self, user_id: str) -> dict:
        user_cost = self._get_cost(self._get_user_key(user_id))
        return {
            "user_id": user_id,
            "date": time.strftime("%Y-%m-%d"),
            "cost_usd": round(user_cost, 6),
            "budget_usd": self.daily_budget_usd,
            "budget_remaining_usd": max(0, round(self.daily_budget_usd - user_cost, 6)),
            "budget_used_pct": round(user_cost / self.daily_budget_usd * 100, 1),
        }


# Singleton
cost_guard = CostGuard(daily_budget_usd=1.0, global_daily_budget_usd=10.0)

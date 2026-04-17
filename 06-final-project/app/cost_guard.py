import redis
from fastapi import HTTPException, status
from .config import settings

r = redis.from_url(settings.REDIS_URL, decode_responses=True)

async def check_budget(user_id: str):
    key = f"budget:{user_id}"
    current_cost = float(r.get(key) or 0.0)
    
    if current_cost >= settings.MONTHLY_BUDGET_USD:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Monthly budget exceeded."
        )

def record_usage(user_id: str, cost: float):
    key = f"budget:{user_id}"
    r.incrbyfloat(key, cost)
    # Hết hạn sau 30 ngày (giả lập tháng)
    r.expire(key, 30 * 24 * 3600)

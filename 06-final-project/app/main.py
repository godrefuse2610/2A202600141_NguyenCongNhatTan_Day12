import logging
import json
import redis
import signal
import sys
from fastapi import FastAPI, Depends, HTTPException, Body
from .config import settings
from .auth import verify_api_key
from .rate_limiter import check_rate_limit
from .cost_guard import check_budget, record_usage
from utils import mock_llm

# Cấu hình Structured JSON Logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Production AI Agent")
r = redis.from_url(settings.REDIS_URL, decode_responses=True)

# ─────────────────────────────────────────────
# Lifecycle & Graceful Shutdown
# ─────────────────────────────────────────────

def shutdown_handler(signum, frame):
    logger.info("SIGTERM received. Cleaning up...")
    # Thực hiện các bước cleanup nếu cần (đóng kết nối db, v.v.)
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

# ─────────────────────────────────────────────
# Health & Readiness
# ─────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ready")
def ready():
    try:
        r.ping()
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")

# ─────────────────────────────────────────────
# Main Agent Endpoint
# ─────────────────────────────────────────────

@app.post("/ask")
async def ask(
    question: str = Body(..., embed=True),
    user_id: str = Depends(verify_api_key)
):
    # 1. Kiểm tra giới hạn (Rate limit & Budget)
    await check_rate_limit(user_id)
    await check_budget(user_id)
    
    # 2. Lấy lịch sử hội thoại từ Redis (Stateless)
    history_key = f"history:{user_id}"
    history = r.lrange(history_key, -10, -1) # Lấy 10 tin nhắn gần nhất
    
    # 3. Gọi LLM
    logger.info(json.dumps({
        "event": "llm_call",
        "user_id": user_id,
        "question": question
    }))
    
    answer = mock_llm.ask(question)
    
    # 4. Lưu vào Redis và Ghi nhận chi phí
    r.rpush(history_key, f"user: {question}", f"assistant: {answer}")
    r.expire(history_key, 3600) # Lưu 1 tiếng
    
    record_usage(user_id, 0.01) # Giả lập chi phí 0.01 USD
    
    return {
        "question": question,
        "answer": answer,
        "user_id": user_id
    }

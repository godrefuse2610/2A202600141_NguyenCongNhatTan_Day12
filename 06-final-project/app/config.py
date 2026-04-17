from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    PORT: int = int(os.getenv("PORT", 8000))
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    AGENT_API_KEY: str = os.getenv("AGENT_API_KEY", "demo-secret-key")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Requirements from Lab
    RATE_LIMIT_PER_MINUTE: int = 10
    MONTHLY_BUDGET_USD: float = 10.0

settings = Settings()

import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Agentic Dating Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite:///./dating.db"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    
    # LLM Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini" if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") else "deterministic")
    
    # Dating Simulation Parameters
    MAX_CONVERSATION_TURNS: int = 8
    DEFAULT_TOKEN_BUDGET: int = 4000
    REQUEST_TIMEOUT_SECONDS: int = 30
    
    # Ranking Weights (Provisional & Configurable)
    WEIGHT_PREFERENCES: float = 0.25
    WEIGHT_SHARED_INTERESTS: float = 0.25
    WEIGHT_LIFESTYLE_FIT: float = 0.20
    WEIGHT_DATE_ENGAGEMENT: float = 0.20
    WEIGHT_VALUES_PRIORITIES: float = 0.10
    
    # Operational & Security
    DEMO_RUN_ID: str = "demo-run-25-participants"
    RATE_LIMIT_PER_MINUTE: int = 120
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

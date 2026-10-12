import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "AuraMatch AI — Agentic Dating Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./dating.db")
    
    # Admin Security
    ADMIN_API_KEY: str = os.getenv("ADMIN_API_KEY", "dev-admin-secret-key")

    @field_validator("ADMIN_API_KEY")
    @classmethod
    def validate_admin_key(cls, v: str) -> str:
        env = os.getenv("ENVIRONMENT", "development").lower()
        if env == "production":
            if not v or v.strip() in ("dev-admin-secret-key", "dev-admin-secret-change-in-prod"):
                raise ValueError(
                    "In production environment, a secure ADMIN_API_KEY must be explicitly set and cannot use default development keys."
                )
        return v
    
    # CORS: Explicit allowed origins (never wildcard in production)
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://ai-agents-autonomous-dating-site-h6.vercel.app",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        return [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "https://ai-agents-autonomous-dating-site-h6.vercel.app",
        ]
    
    # LLM Configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    # "groq" for Groq cloud inference; "gemini" for Google Gemini; "offline_mock" strictly for offline tests
    LLM_PROVIDER: str = os.getenv(
        "LLM_PROVIDER",
        "groq" if os.getenv("GROQ_API_KEY") else ("gemini" if (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")) else "offline_mock")
    )
    
    # Dating Simulation Parameters
    MAX_CONVERSATION_TURNS: int = 8
    DEFAULT_TOKEN_BUDGET: int = 4000
    REQUEST_TIMEOUT_SECONDS: int = 30
    MODEL_TIMEOUT_SECONDS: int = 25
    
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

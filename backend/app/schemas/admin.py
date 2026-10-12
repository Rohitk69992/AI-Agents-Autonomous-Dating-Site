from typing import Dict, Any, Optional
from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    llm_provider: str
    llm_model: str
    active_background_jobs: int

class AdminConfigResponse(BaseModel):
    llm_provider: str
    gemini_model: str
    api_key_configured: bool
    database_url_masked: str
    max_turns: int
    ranking_weights: Dict[str, float]
    demo_run_id: str

class UpdateConfigAdminRequest(BaseModel):
    llm_provider: Optional[str] = None
    gemini_model: Optional[str] = None
    max_turns: Optional[int] = None
    ranking_weights: Optional[Dict[str, float]] = None

class ObservabilityMetricsResponse(BaseModel):
    total_participants: int
    analyzed_participants: int
    total_dating_sessions: int
    completed_sessions: int
    failed_sessions: int
    total_tokens_consumed: int
    estimated_total_cost_usd: float
    average_session_latency_ms: float

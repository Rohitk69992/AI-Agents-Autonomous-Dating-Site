import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class DemonstrationRunResponse(BaseModel):
    id: str
    name: str
    status: str
    total_participants: int
    total_eligible_pairs: int
    simulated_pairs: int
    completed_sessions: int
    failed_sessions: int
    model_used: str
    started_at: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None
    execution_summary: Dict[str, Any] = {}

    class Config:
        from_attributes = True

class StartRunRequest(BaseModel):
    run_id: Optional[str] = "demo-run-25-participants"
    name: Optional[str] = "Official 25-Participant Consenting Simulation"
    concurrency: int = Field(default=2, ge=1, le=10)

class RunProgressResponse(BaseModel):
    run_id: str
    status: str
    percent_complete: float
    total_pairs: int
    completed_pairs: int
    failed_pairs: int
    pending_pairs: int
    active_pair: Optional[Dict[str, str]] = None

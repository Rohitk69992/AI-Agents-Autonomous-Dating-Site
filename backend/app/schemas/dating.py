import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class ConversationMessageResponse(BaseModel):
    id: str
    turn_number: int
    sender_participant_id: str
    sender_name: Optional[str] = None
    sender_agent_role: str
    content: str
    internal_thought: Optional[str] = None
    question_asked: Optional[str] = None
    interest_referenced: Optional[str] = None
    timestamp: datetime.datetime
    tokens: int = 0

    class Config:
        from_attributes = True

class AgentEvaluationResponse(BaseModel):
    id: str
    evaluator_participant_id: str
    evaluator_name: Optional[str] = None
    target_participant_id: str
    target_name: Optional[str] = None
    chemistry_score: float
    communication_comfort: float
    shared_values_alignment: float
    would_date_again: bool
    evaluation_rationale: str
    perceived_green_flags: List[str] = []
    perceived_red_flags: List[str] = []
    unanswered_questions: List[str] = []
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class StartDatingSessionRequest(BaseModel):
    participant_a_id: str
    participant_b_id: str
    run_id: Optional[str] = None
    max_turns: Optional[int] = Field(default=8, ge=2, le=16)

class DatingSessionResponse(BaseModel):
    id: str
    run_id: Optional[str] = None
    participant_a_id: str
    participant_a_name: Optional[str] = None
    participant_b_id: str
    participant_b_name: Optional[str] = None
    status: str
    current_turn: int
    total_turns: int
    agent_a_objective: Optional[str] = None
    agent_b_objective: Optional[str] = None
    outcome_status: Optional[str] = None
    outcome_summary: Optional[str] = None
    shared_interests_found: List[str] = []
    friction_points: List[str] = []
    mutual_engagement_score: float = 0.0
    total_tokens_used: int = 0
    approx_cost_usd: float = 0.0
    latency_ms: int = 0
    error_detail: Optional[str] = None
    started_at: datetime.datetime
    completed_at: Optional[datetime.datetime] = None
    messages: List[ConversationMessageResponse] = []
    evaluations: List[AgentEvaluationResponse] = []

    class Config:
        from_attributes = True

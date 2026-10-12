import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class CandidateRankingResponse(BaseModel):
    id: str
    rank: int
    source_participant_id: str
    target_participant_id: str
    target_name: str
    individual_score: float
    reciprocal_score: float
    preference_score: float
    interest_score: float
    lifestyle_score: float
    engagement_score: float
    values_score: float
    confidence_score: float
    shared_interests: List[str] = []
    potential_incompatibilities: List[str] = []
    supporting_evidence_summary: Optional[str] = None
    ranking_explanation: str
    session_id: Optional[str] = None
    calculated_at: datetime.datetime

    class Config:
        from_attributes = True

class ParticipantRankingsListResponse(BaseModel):
    source_participant_id: str
    source_participant_name: str
    rankings: List[CandidateRankingResponse]
    weights_used: dict
    deterministic_rule: str

class UpdateWeightsRequest(BaseModel):
    weight_preferences: float = Field(0.25, ge=0.0, le=1.0)
    weight_shared_interests: float = Field(0.25, ge=0.0, le=1.0)
    weight_lifestyle_fit: float = Field(0.20, ge=0.0, le=1.0)
    weight_date_engagement: float = Field(0.20, ge=0.0, le=1.0)
    weight_values_priorities: float = Field(0.10, ge=0.0, le=1.0)

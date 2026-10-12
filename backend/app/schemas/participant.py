import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl, ConfigDict

class EvidenceItemResponse(BaseModel):
    id: str
    source_platform: str
    source_url: str
    category: str
    evidence_type: str
    raw_quote: str
    confidence: float
    retrieved_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class AnalyzedProfileResponse(BaseModel):
    id: str
    participant_id: str
    summary: str
    career_interests: List[str] = []
    demonstrated_hobbies: List[str] = []
    stated_interests: List[str] = []
    lifestyle_preferences: List[str] = []
    communication_preferences: List[str] = []
    relationship_preferences: List[str] = []
    explicit_facts: List[str] = []
    inferences_with_confidence: List[dict] = []
    uncertainties_and_unknowns: List[str] = []
    model_version: str
    analyzed_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class ParticipantCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    linkedin_url: str = Field(..., description="Valid public LinkedIn profile URL")
    instagram_url: str = Field(..., description="Valid public Instagram profile URL")
    consent_confirmed: bool = Field(..., description="Explicit consent confirmation to agent representation and simulated dating")
    age: Optional[int] = Field(None, ge=18, le=100)
    gender: Optional[str] = None
    target_gender: Optional[str] = None
    location: Optional[str] = None

class ParticipantBatchItem(ParticipantCreate):
    pass

class ParticipantBatchCreate(BaseModel):
    participants: List[ParticipantBatchItem]

class ParticipantResponse(BaseModel):
    id: str
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    target_gender: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: str
    linkedin_handle: str
    instagram_url: str
    instagram_handle: str
    consent_status: str
    consent_timestamp: datetime.datetime
    status: str
    created_at: datetime.datetime
    analyzed_profile: Optional[AnalyzedProfileResponse] = None
    evidence_count: int = 0

    model_config = ConfigDict(from_attributes=True)

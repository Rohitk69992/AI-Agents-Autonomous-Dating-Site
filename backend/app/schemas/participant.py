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
    is_synthetic: bool = False
    processing_version: str = "1.0.0"
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

class ManifestEvidenceItem(BaseModel):
    platform: str
    category: str
    type: str
    quote: str
    confidence: float = 1.0

class ManifestParticipantItem(BaseModel):
    id: Optional[str] = None
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    target_gender: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: str
    instagram_url: str
    consent_verified: bool = True
    source_verified: bool = True
    evidence: List[ManifestEvidenceItem] = []

class ManifestImportRequest(BaseModel):
    manifest_id: Optional[str] = "real-consenting-participants-v1"
    run_immediate_analysis: bool = True
    participants: List[ManifestParticipantItem]

class ManifestImportResponse(BaseModel):
    imported_count: int
    skipped_count: int
    errors: List[str] = []
    imported_participant_ids: List[str] = []

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
    consent_verified: bool = False
    source_verified: bool = False
    is_synthetic: bool = False
    simulation_eligible: bool = True
    status: str
    analysis_status: str = "pending"
    created_at: datetime.datetime
    analyzed_profile: Optional[AnalyzedProfileResponse] = None
    evidence_count: int = 0

    model_config = ConfigDict(from_attributes=True)

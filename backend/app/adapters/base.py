import datetime
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class ExtractedEvidence(BaseModel):
    category: str  # professional, hobby, interest, lifestyle, communication, relationship_preference
    evidence_type: str  # explicit_statement, observed_activity, model_interpretation
    raw_quote: str
    confidence: float = 1.0

class AcquisitionResult(BaseModel):
    is_success: bool
    platform: str
    profile_url: str
    handle: str
    evidence_items: List[ExtractedEvidence] = []
    blocker_reason: Optional[str] = None
    http_status: Optional[int] = None
    retrieval_timestamp: datetime.datetime = datetime.datetime.utcnow()
    provenance_metadata: Dict[str, Any] = {}

class BaseAcquisitionAdapter(ABC):
    @abstractmethod
    def acquire(self, profile_url: str, participant_handle: str) -> AcquisitionResult:
        pass

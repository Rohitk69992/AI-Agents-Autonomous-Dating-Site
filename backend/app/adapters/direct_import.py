import datetime
from typing import Any, Dict, List
from app.adapters.base import BaseAcquisitionAdapter, AcquisitionResult, ExtractedEvidence
from app.core.security import validate_and_normalize_linkedin_url, validate_and_normalize_instagram_url

class AuthorizedParticipantImportAdapter(BaseAcquisitionAdapter):
    """
    Compliant acquisition adapter for consented participants who provide authorized
    exports of their public LinkedIn and Instagram profiles.
    Preserves strict provenance, source URLs, and quote-level traceability.
    """
    def __init__(self, raw_export_data: Dict[str, Any]):
        self.raw_export_data = raw_export_data

    def acquire(self, profile_url: str, participant_handle: str) -> AcquisitionResult:
        is_linkedin = "linkedin.com" in profile_url.lower()
        platform = "linkedin" if is_linkedin else "instagram"
        
        evidence_list: List[ExtractedEvidence] = []
        raw_items = self.raw_export_data.get(platform, {}).get("evidence_items", [])
        
        for item in raw_items:
            evidence_list.append(
                ExtractedEvidence(
                    category=item.get("category", "interest"),
                    evidence_type=item.get("evidence_type", "explicit_statement"),
                    raw_quote=item.get("raw_quote", ""),
                    confidence=float(item.get("confidence", 1.0))
                )
            )

        return AcquisitionResult(
            is_success=True,
            platform=platform,
            profile_url=profile_url,
            handle=participant_handle,
            evidence_items=evidence_list,
            http_status=200,
            retrieval_timestamp=datetime.datetime.utcnow(),
            provenance_metadata={
                "adapter": "AuthorizedParticipantImportAdapter",
                "method": "consented_participant_data_export",
                "evidence_count": len(evidence_list),
                "verified_by_user": True
            }
        )

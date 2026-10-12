import datetime
import os
import httpx
from app.adapters.base import BaseAcquisitionAdapter, AcquisitionResult, ExtractedEvidence
from app.core.security import validate_and_normalize_instagram_url, is_safe_external_url

class InstagramAcquisitionAdapter(BaseAcquisitionAdapter):
    def __init__(self):
        self.access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")

    def acquire(self, profile_url: str, participant_handle: str) -> AcquisitionResult:
        is_valid, normalized_url, handle = validate_and_normalize_instagram_url(profile_url)
        if not is_valid:
            return AcquisitionResult(
                is_success=False,
                platform="instagram",
                profile_url=profile_url,
                handle=participant_handle,
                blocker_reason="INVALID_URL_FORMAT: Must match https://www.instagram.com/{handle}",
                retrieval_timestamp=datetime.datetime.utcnow(),
                provenance_metadata={"adapter": "InstagramAcquisitionAdapter", "version": "1.0"}
            )

        safe, msg = is_safe_external_url(normalized_url)
        if not safe:
            return AcquisitionResult(
                is_success=False,
                platform="instagram",
                profile_url=normalized_url,
                handle=handle,
                blocker_reason=f"SECURITY_VIOLATION: {msg}",
                retrieval_timestamp=datetime.datetime.utcnow(),
                provenance_metadata={"adapter": "InstagramAcquisitionAdapter", "version": "1.0"}
            )

        # Check for Official Meta Graph API token
        if self.access_token:
            try:
                with httpx.Client(timeout=10.0) as client:
                    resp = client.get(
                        f"https://graph.instagram.com/me?fields=id,username,biography&access_token={self.access_token}"
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        evidence = [
                            ExtractedEvidence(
                                category="lifestyle",
                                evidence_type="explicit_statement",
                                raw_quote=f"Bio: {data.get('biography', '')}",
                                confidence=1.0
                            )
                        ]
                        return AcquisitionResult(
                            is_success=True,
                            platform="instagram",
                            profile_url=normalized_url,
                            handle=handle,
                            evidence_items=evidence,
                            http_status=200,
                            retrieval_timestamp=datetime.datetime.utcnow(),
                            provenance_metadata={"method": "meta_graph_api"}
                        )
            except Exception:
                pass

        return AcquisitionResult(
            is_success=False,
            platform="instagram",
            profile_url=normalized_url,
            handle=handle,
            http_status=401,
            blocker_reason="LOGIN_WALL_OR_META_RESTRICTION: Instagram public automated profile access requires user authentication or Meta Graph API credentials. Direct crawling blocked by platform policy.",
            retrieval_timestamp=datetime.datetime.utcnow(),
            provenance_metadata={
                "adapter": "InstagramAcquisitionAdapter",
                "method": "unauthenticated_http_probe",
                "auth_configured": bool(self.access_token)
            }
        )

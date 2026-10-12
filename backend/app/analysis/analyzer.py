import datetime
import json
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.db.models import Participant, EvidenceItem, AnalyzedProfile
from app.llm.provider import get_llm_provider
from app.schemas.participant import AnalyzedProfileResponse

logger = logging.getLogger(__name__)

PROFILE_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "career_interests": {"type": "array", "items": {"type": "string"}},
        "demonstrated_hobbies": {"type": "array", "items": {"type": "string"}},
        "stated_interests": {"type": "array", "items": {"type": "string"}},
        "lifestyle_preferences": {"type": "array", "items": {"type": "string"}},
        "communication_preferences": {"type": "array", "items": {"type": "string"}},
        "relationship_preferences": {"type": "array", "items": {"type": "string"}},
        "explicit_facts": {"type": "array", "items": {"type": "string"}},
        "inferences_with_confidence": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim": {"type": "string"},
                    "confidence": {"type": "number"},
                    "basis": {"type": "string"}
                },
                "required": ["claim", "confidence", "basis"]
            }
        },
        "uncertainties_and_unknowns": {"type": "array", "items": {"type": "string"}}
    },
    "required": [
        "summary", "career_interests", "demonstrated_hobbies", "stated_interests",
        "lifestyle_preferences", "communication_preferences", "relationship_preferences",
        "explicit_facts", "inferences_with_confidence", "uncertainties_and_unknowns"
    ]
}

SYSTEM_PROMPT = """You are a rigorous, privacy-preserving Profile Analysis Agent for an Agentic Dating Platform.
Your mission is to extract ONLY voluntary dating-relevant characteristics supported by the provided evidence from LinkedIn and Instagram profiles.

NON-NEGOTIABLE SAFETY AND INTEGRITY RULES:
1. DISTINGUISH:
   - Explicitly stated facts (direct quotes/statements)
   - Observed public professional or hobby information
   - Model-generated probabilistic interpretations (with numerical confidence 0.0-1.0 and supporting basis)
   - Unknown or insufficiently supported characteristics (label as "unknown" in uncertainties_and_unknowns)
2. PROHIBITED INFERENCES:
   - Do NOT infer sensitive personal attributes (sexual orientation unless stated, religion, political beliefs, health/medical status, financial wealth).
   - Do NOT judge or infer romantic worth based on physical appearance, facial attributes, follower counts, or job prestige.
3. If evidence for a category is absent, output an empty list or explicitly record it in uncertainties_and_unknowns. Do NOT invent claims.
"""

def analyze_participant_profile(db: Session, participant_id: str) -> Optional[AnalyzedProfile]:
    participant = db.query(Participant).filter(Participant.id == participant_id).first()
    if not participant:
        logger.error(f"Participant {participant_id} not found.")
        return None

    evidence_items = db.query(EvidenceItem).filter(EvidenceItem.participant_id == participant_id).all()
    if not evidence_items:
        # Create minimal fallback analysis marking fields as unknown
        analyzed = AnalyzedProfile(
            participant_id=participant_id,
            summary=f"Profile for {participant.name}. Insufficient public evidence retrieved to date.",
            career_interests=[],
            demonstrated_hobbies=[],
            stated_interests=[],
            lifestyle_preferences=[],
            communication_preferences=[],
            relationship_preferences=[],
            explicit_facts=[],
            inferences_with_confidence=[],
            uncertainties_and_unknowns=[
                "Professional focus unknown",
                "Personal hobbies unknown",
                "Communication style unverified"
            ],
            model_version="rule-based-sparse",
            analyzed_at=datetime.datetime.utcnow()
        )
        db.merge(analyzed)
        participant.status = "analyzed"
        db.commit()
        return analyzed

    evidence_text = "\n".join([
        f"- [{item.source_platform.upper()}] ({item.category} / {item.evidence_type}): \"{item.raw_quote}\" (Confidence: {item.confidence})"
        for item in evidence_items
    ])

    user_prompt = f"""Participant: {participant.name}
LinkedIn: {participant.linkedin_url}
Instagram: {participant.instagram_url}

SOURCE EVIDENCE GATHERED:
{evidence_text}

Perform structured analysis according to the schema. Categorize all findings accurately."""

    provider = get_llm_provider()
    response = provider.generate(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.3,
        response_schema=PROFILE_ANALYSIS_SCHEMA
    )

    data = response.structured_data
    if not data or not isinstance(data, dict):
        # Fallback parsing
        try:
            data = json.loads(response.content)
        except Exception:
            data = {}

    analyzed = db.query(AnalyzedProfile).filter(AnalyzedProfile.participant_id == participant_id).first()
    if not analyzed:
        analyzed = AnalyzedProfile(participant_id=participant_id)

    analyzed.summary = data.get("summary", f"Profile summary for {participant.name}.")
    analyzed.career_interests = data.get("career_interests", [])
    analyzed.demonstrated_hobbies = data.get("demonstrated_hobbies", [])
    analyzed.stated_interests = data.get("stated_interests", [])
    analyzed.lifestyle_preferences = data.get("lifestyle_preferences", [])
    analyzed.communication_preferences = data.get("communication_preferences", [])
    analyzed.relationship_preferences = data.get("relationship_preferences", [])
    analyzed.explicit_facts = data.get("explicit_facts", [])
    analyzed.inferences_with_confidence = data.get("inferences_with_confidence", [])
    analyzed.uncertainties_and_unknowns = data.get("uncertainties_and_unknowns", [])
    analyzed.model_version = response.model or "gemini-2.5-flash"
    analyzed.analyzed_at = datetime.datetime.utcnow()

    db.add(analyzed)
    participant.status = "analyzed"
    db.commit()
    db.refresh(analyzed)
    return analyzed

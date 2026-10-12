from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Participant, CompatibilityRanking
from app.schemas.ranking import (
    CandidateRankingResponse, ParticipantRankingsListResponse, UpdateWeightsRequest
)
from app.ranking.engine import calculate_rankings_for_participant
from app.core.config import settings

router = APIRouter(tags=["Compatibility & Rankings"])

@router.get("/participants/{participant_id}/rankings", response_model=ParticipantRankingsListResponse)
def get_participant_rankings(
    participant_id: str,
    run_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    p = db.query(Participant).filter(Participant.id == participant_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Participant not found")

    rankings = db.query(CompatibilityRanking).filter(
        CompatibilityRanking.source_participant_id == participant_id
    )
    if run_id:
        rankings = rankings.filter(CompatibilityRanking.run_id == run_id)
    
    ranking_records = rankings.order_by(CompatibilityRanking.rank.asc()).all()

    # If no rankings calculated yet, calculate on-the-fly
    if not ranking_records:
        ranking_records = calculate_rankings_for_participant(db, participant_id, run_id=run_id)

    results = []
    for r in ranking_records:
        target = r.target_participant
        results.append(CandidateRankingResponse(
            id=r.id,
            rank=r.rank,
            source_participant_id=r.source_participant_id,
            target_participant_id=r.target_participant_id,
            target_name=target.name if target else "Unknown",
            is_synthetic=bool(r.is_synthetic),
            individual_score=r.individual_score,
            reciprocal_score=r.reciprocal_score,
            preference_score=r.preference_score,
            interest_score=r.interest_score,
            lifestyle_score=r.lifestyle_score,
            engagement_score=r.engagement_score,
            values_score=r.values_score,
            confidence_score=r.confidence_score,
            shared_interests=r.shared_interests or [],
            potential_incompatibilities=r.potential_incompatibilities or [],
            supporting_evidence_summary=r.supporting_evidence_summary,
            ranking_explanation=r.ranking_explanation,
            session_id=r.session_id,
            calculated_at=r.calculated_at
        ))

    return ParticipantRankingsListResponse(
        source_participant_id=p.id,
        source_participant_name=p.name,
        rankings=results,
        weights_used={
            "weight_preferences": settings.WEIGHT_PREFERENCES,
            "weight_shared_interests": settings.WEIGHT_SHARED_INTERESTS,
            "weight_lifestyle_fit": settings.WEIGHT_LIFESTYLE_FIT,
            "weight_date_engagement": settings.WEIGHT_DATE_ENGAGEMENT,
            "weight_values_priorities": settings.WEIGHT_VALUES_PRIORITIES,
        },
        deterministic_rule="Harmonic Reciprocal Score desc -> Confidence desc -> Individual Score desc -> Target ID asc"
    )

@router.post("/participants/{participant_id}/rankings/recalculate", response_model=ParticipantRankingsListResponse)
def recalculate_participant_rankings(
    participant_id: str,
    weights_req: UpdateWeightsRequest,
    run_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    weights = weights_req.model_dump()
    records = calculate_rankings_for_participant(db, participant_id, run_id=run_id, weights_override=weights)
    p = db.query(Participant).filter(Participant.id == participant_id).first()

    results = []
    for r in records:
        target = r.target_participant
        results.append(CandidateRankingResponse(
            id=r.id,
            rank=r.rank,
            source_participant_id=r.source_participant_id,
            target_participant_id=r.target_participant_id,
            target_name=target.name if target else "Unknown",
            is_synthetic=bool(r.is_synthetic),
            individual_score=r.individual_score,
            reciprocal_score=r.reciprocal_score,
            preference_score=r.preference_score,
            interest_score=r.interest_score,
            lifestyle_score=r.lifestyle_score,
            engagement_score=r.engagement_score,
            values_score=r.values_score,
            confidence_score=r.confidence_score,
            shared_interests=r.shared_interests or [],
            potential_incompatibilities=r.potential_incompatibilities or [],
            supporting_evidence_summary=r.supporting_evidence_summary,
            ranking_explanation=r.ranking_explanation,
            session_id=r.session_id,
            calculated_at=r.calculated_at
        ))

    return ParticipantRankingsListResponse(
        source_participant_id=p.id,
        source_participant_name=p.name,
        rankings=results,
        weights_used=weights,
        deterministic_rule="Harmonic Reciprocal Score desc -> Confidence desc -> Individual Score desc -> Target ID asc"
    )

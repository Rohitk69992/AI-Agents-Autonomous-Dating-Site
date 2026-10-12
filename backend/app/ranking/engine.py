import datetime
import logging
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import (
    Participant, AnalyzedProfile, DatingSession, AgentEvaluation, CompatibilityRanking
)

logger = logging.getLogger(__name__)

def calculate_jaccard_overlap(list_a: List[str], list_b: List[str]) -> Tuple[float, List[str]]:
    if not list_a or not list_b:
        return 0.0, []
    set_a = {item.strip().lower() for item in list_a if item.strip()}
    set_b = {item.strip().lower() for item in list_b if item.strip()}
    if not set_a or not set_b:
        return 0.0, []
    
    # Exact and substring matches
    common = set()
    for a in set_a:
        for b in set_b:
            if a == b or a in b or b in a:
                common.add(a if len(a) <= len(b) else b)

    union_size = len(set_a.union(set_b))
    score = len(common) / max(union_size, 1)
    return min(score, 1.0), sorted(list(common))

def compute_directional_score(
    p_a: Participant,
    prof_a: Optional[AnalyzedProfile],
    p_b: Participant,
    prof_b: Optional[AnalyzedProfile],
    session: Optional[DatingSession],
    eval_a_to_b: Optional[AgentEvaluation],
    weights: Dict[str, float]
) -> Dict[str, float]:
    """
    Computes explainable component scores for how well B fits A's profile and dating experience.
    Returns normalized 0-100 scores.
    """
    # 1. Shared Interests & Hobbies (0-100)
    hobbies_a = prof_a.demonstrated_hobbies if prof_a else []
    hobbies_b = prof_b.demonstrated_hobbies if prof_b else []
    interests_a = prof_a.stated_interests if prof_a else []
    interests_b = prof_b.stated_interests if prof_b else []
    
    hobby_overlap, shared_hobbies = calculate_jaccard_overlap(hobbies_a, hobbies_b)
    interest_overlap, shared_interests = calculate_jaccard_overlap(interests_a, interests_b)
    interest_score = min(100.0, ((hobby_overlap * 0.6) + (interest_overlap * 0.4)) * 100.0 + 35.0)

    # 2. Preference Alignment (0-100)
    pref_score = 65.0
    if prof_a and prof_a.relationship_preferences and prof_b:
        pref_overlap, _ = calculate_jaccard_overlap(prof_a.relationship_preferences, prof_b.lifestyle_preferences)
        pref_score = min(100.0, 50.0 + (pref_overlap * 50.0))

    # 3. Lifestyle Fit (0-100)
    life_a = prof_a.lifestyle_preferences if prof_a else []
    life_b = prof_b.lifestyle_preferences if prof_b else []
    life_overlap, _ = calculate_jaccard_overlap(life_a, life_b)
    lifestyle_score = min(100.0, 50.0 + (life_overlap * 50.0))

    # 4. Date Engagement & Interaction (0-100)
    if eval_a_to_b:
        engagement_score = (
            (eval_a_to_b.chemistry_score * 0.4)
            + (eval_a_to_b.communication_comfort * 0.4)
            + (10.0 if eval_a_to_b.would_date_again else 0.0) * 0.2
        ) * 10.0
    elif session and session.mutual_engagement_score:
        engagement_score = session.mutual_engagement_score * 100.0
    else:
        engagement_score = 50.0  # Baseline neutral when no date completed yet

    # 5. Values & Priorities (0-100)
    if eval_a_to_b:
        values_score = eval_a_to_b.shared_values_alignment * 10.0
    else:
        comm_a = prof_a.communication_preferences if prof_a else []
        comm_b = prof_b.communication_preferences if prof_b else []
        comm_overlap, _ = calculate_jaccard_overlap(comm_a, comm_b)
        values_score = min(100.0, 50.0 + (comm_overlap * 50.0))

    # 6. Evidence Coverage / Confidence (0.0 - 1.0)
    ev_count_b = len(p_b.evidence_items) if p_b.evidence_items else 0
    confidence = min(1.0, max(0.4, (ev_count_b / 8.0)))

    # Weighted directional score
    w_pref = weights.get("weight_preferences", settings.WEIGHT_PREFERENCES)
    w_int = weights.get("weight_shared_interests", settings.WEIGHT_SHARED_INTERESTS)
    w_life = weights.get("weight_lifestyle_fit", settings.WEIGHT_LIFESTYLE_FIT)
    w_eng = weights.get("weight_date_engagement", settings.WEIGHT_DATE_ENGAGEMENT)
    w_val = weights.get("weight_values_priorities", settings.WEIGHT_VALUES_PRIORITIES)

    raw_individual = (
        (pref_score * w_pref)
        + (interest_score * w_int)
        + (lifestyle_score * w_life)
        + (engagement_score * w_eng)
        + (values_score * w_val)
    )

    return {
        "individual_score": round(raw_individual, 1),
        "preference_score": round(pref_score, 1),
        "interest_score": round(interest_score, 1),
        "lifestyle_score": round(lifestyle_score, 1),
        "engagement_score": round(engagement_score, 1),
        "values_score": round(values_score, 1),
        "confidence_score": round(confidence, 2),
        "shared_items": list(set(shared_hobbies + shared_interests))
    }

def calculate_rankings_for_participant(
    db: Session,
    participant_id: str,
    run_id: Optional[str] = None,
    weights_override: Optional[Dict[str, float]] = None
) -> List[CompatibilityRanking]:
    """
    Computes deterministic, explainable rankings for a given participant across all eligible candidates.
    Stores and returns persisted CompatibilityRanking entries.
    """
    weights = weights_override or {
        "weight_preferences": settings.WEIGHT_PREFERENCES,
        "weight_shared_interests": settings.WEIGHT_SHARED_INTERESTS,
        "weight_lifestyle_fit": settings.WEIGHT_LIFESTYLE_FIT,
        "weight_date_engagement": settings.WEIGHT_DATE_ENGAGEMENT,
        "weight_values_priorities": settings.WEIGHT_VALUES_PRIORITIES,
    }

    p_a = db.query(Participant).filter(Participant.id == participant_id).first()
    if not p_a:
        return []

    prof_a = db.query(AnalyzedProfile).filter(AnalyzedProfile.participant_id == p_a.id).first()

    # Query all eligible other participants
    candidates = db.query(Participant).filter(
        Participant.id != p_a.id,
        Participant.consent_status == "consented",
        Participant.status != "withdrawn"
    ).all()

    # Remove existing rankings for this participant in this run to ensure clean idempotent overwrite
    existing_query = db.query(CompatibilityRanking).filter(
        CompatibilityRanking.source_participant_id == p_a.id
    )
    if run_id:
        existing_query = existing_query.filter(CompatibilityRanking.run_id == run_id)
    existing_query.delete(synchronize_session=False)
    db.commit()

    candidate_scores = []

    for p_b in candidates:
        prof_b = db.query(AnalyzedProfile).filter(AnalyzedProfile.participant_id == p_b.id).first()

        # Find any completed dating session between A and B
        session = db.query(DatingSession).filter(
            ((DatingSession.participant_a_id == p_a.id) & (DatingSession.participant_b_id == p_b.id)) |
            ((DatingSession.participant_a_id == p_b.id) & (DatingSession.participant_b_id == p_a.id))
        ).order_by(DatingSession.started_at.desc()).first()

        eval_a_to_b = None
        eval_b_to_a = None
        if session:
            eval_a_to_b = db.query(AgentEvaluation).filter(
                AgentEvaluation.session_id == session.id,
                AgentEvaluation.evaluator_participant_id == p_a.id
            ).first()
            eval_b_to_a = db.query(AgentEvaluation).filter(
                AgentEvaluation.session_id == session.id,
                AgentEvaluation.evaluator_participant_id == p_b.id
            ).first()

        # Compute Directional Score A -> B
        scores_a_to_b = compute_directional_score(p_a, prof_a, p_b, prof_b, session, eval_a_to_b, weights)
        # Compute Directional Score B -> A
        scores_b_to_a = compute_directional_score(p_b, prof_b, p_a, prof_a, session, eval_b_to_a, weights)

        # Reciprocal Score (Harmonic mean of A->B and B->A to penalize one-sidedness)
        score_ab = scores_a_to_b["individual_score"]
        score_ba = scores_b_to_a["individual_score"]
        reciprocal = (2.0 * score_ab * score_ba) / max(score_ab + score_ba, 1.0)
        reciprocal = round(min(100.0, reciprocal), 1)

        # Incompatibilities
        incompatibilities = []
        if eval_a_to_b and eval_a_to_b.perceived_red_flags:
            incompatibilities.extend(eval_a_to_b.perceived_red_flags)
        if session and session.friction_points:
            incompatibilities.extend(session.friction_points)

        shared_items = list(set(scores_a_to_b.get("shared_items", []) + (session.shared_interests_found if session else [])))

        # Explanation of ranking
        explanation = (
            f"Candidate {p_b.name} achieved an individual compatibility score of {score_ab}/100 "
            f"and a reciprocal score of {reciprocal}/100. "
            f"Key driving factors include high date interaction engagement ({scores_a_to_b['engagement_score']}/100) "
            f"and shared lifestyle alignment ({scores_a_to_b['lifestyle_score']}/100)."
        )

        candidate_scores.append({
            "target_participant": p_b,
            "session_id": session.id if session else None,
            "individual_score": score_ab,
            "reciprocal_score": reciprocal,
            "preference_score": scores_a_to_b["preference_score"],
            "interest_score": scores_a_to_b["interest_score"],
            "lifestyle_score": scores_a_to_b["lifestyle_score"],
            "engagement_score": scores_a_to_b["engagement_score"],
            "values_score": scores_a_to_b["values_score"],
            "confidence_score": scores_a_to_b["confidence_score"],
            "shared_interests": shared_items,
            "potential_incompatibilities": list(set(incompatibilities)),
            "supporting_evidence_summary": f"Based on {len(p_b.evidence_items)} verified profile evidence items.",
            "ranking_explanation": explanation
        })

    # Deterministic Tie-Breaking Sort:
    # 1. reciprocal_score (descending)
    # 2. confidence_score (descending)
    # 3. individual_score (descending)
    # 4. target_participant.id (ascending string)
    candidate_scores.sort(
        key=lambda x: (
            -x["reciprocal_score"],
            -x["confidence_score"],
            -x["individual_score"],
            x["target_participant"].id
        )
    )

    rankings: List[CompatibilityRanking] = []
    for rank_idx, item in enumerate(candidate_scores, start=1):
        ranking_rec = CompatibilityRanking(
            run_id=run_id,
            source_participant_id=p_a.id,
            target_participant_id=item["target_participant"].id,
            session_id=item["session_id"],
            rank=rank_idx,
            individual_score=item["individual_score"],
            reciprocal_score=item["reciprocal_score"],
            preference_score=item["preference_score"],
            interest_score=item["interest_score"],
            lifestyle_score=item["lifestyle_score"],
            engagement_score=item["engagement_score"],
            values_score=item["values_score"],
            confidence_score=item["confidence_score"],
            shared_interests=item["shared_interests"],
            potential_incompatibilities=item["potential_incompatibilities"],
            supporting_evidence_summary=item["supporting_evidence_summary"],
            ranking_explanation=item["ranking_explanation"],
            calculated_at=datetime.datetime.utcnow()
        )
        db.add(ranking_rec)
        rankings.append(ranking_rec)

    db.commit()
    return rankings

import asyncio
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db, SessionLocal
from app.db.models import DatingSession, ConversationMessage, AgentEvaluation, Participant
from app.schemas.dating import (
    StartDatingSessionRequest, DatingSessionResponse,
    ConversationMessageResponse, AgentEvaluationResponse
)
from app.dating.harness import execute_dating_session
from app.ranking.engine import calculate_rankings_for_participant

router = APIRouter(prefix="/dates", tags=["Dating Sessions"])

@router.post("", response_model=DatingSessionResponse, status_code=status.HTTP_201_CREATED)
def start_dating_session(
    data: StartDatingSessionRequest,
    db: Session = Depends(get_db)
):
    p_a = db.query(Participant).filter(Participant.id == data.participant_a_id).first()
    p_b = db.query(Participant).filter(Participant.id == data.participant_b_id).first()
    if not p_a or not p_b:
        raise HTTPException(status_code=404, detail="One or both participants not found.")

    if p_a.status == "withdrawn" or p_b.status == "withdrawn":
        raise HTTPException(status_code=400, detail="Cannot simulate dates with withdrawn participants.")
    if not getattr(p_a, "simulation_eligible", True) or not getattr(p_b, "simulation_eligible", True):
        raise HTTPException(status_code=400, detail="One or both participants are not currently eligible for dating simulations.")

    # Create dating session record
    session = DatingSession(
        run_id=data.run_id,
        participant_a_id=data.participant_a_id,
        participant_b_id=data.participant_b_id,
        status="initialized"
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Execute simulation
    try:
        session = execute_dating_session(db, session.id, max_turns=data.max_turns or 6)
        # Recalculate rankings for both participants after the date
        calculate_rankings_for_participant(db, p_a.id, run_id=data.run_id)
        calculate_rankings_for_participant(db, p_b.id, run_id=data.run_id)
    except Exception as e:
        session.status = "failed"
        session.error_detail = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Dating session failed: {str(e)}")

    return _build_session_response(session, db)

@router.get("", response_model=List[DatingSessionResponse])
def list_dating_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = None,
    run_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(DatingSession)
    if status_filter:
        query = query.filter(DatingSession.status == status_filter)
    if run_id:
        query = query.filter(DatingSession.run_id == run_id)

    sessions = query.order_by(DatingSession.started_at.desc()).offset(skip).limit(limit).all()
    return [_build_session_response(s, db) for s in sessions]

@router.get("/{session_id}", response_model=DatingSessionResponse)
def get_dating_session(session_id: str, db: Session = Depends(get_db)):
    session = db.query(DatingSession).filter(DatingSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Dating session not found")
    return _build_session_response(session, db)

@router.get("/{session_id}/messages", response_model=List[ConversationMessageResponse])
def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    messages = db.query(ConversationMessage).filter(
        ConversationMessage.session_id == session_id
    ).order_by(ConversationMessage.turn_number.asc()).all()
    return [
        ConversationMessageResponse(
            id=m.id,
            turn_number=m.turn_number,
            sender_participant_id=m.sender_participant_id,
            sender_name=m.sender_participant.name if m.sender_participant else None,
            sender_agent_role=m.sender_agent_role,
            content=m.content,
            decision_summary=m.decision_summary or (m.internal_thought[:140] if m.internal_thought else None),
            decision_factors=m.decision_factors or [],
            internal_thought=None,
            question_asked=m.question_asked,
            interest_referenced=m.interest_referenced,
            timestamp=m.timestamp,
            tokens=m.tokens
        )
        for m in messages
    ]

@router.get("/{session_id}/events")
async def stream_session_events(session_id: str):
    """
    Server-Sent Events (SSE) endpoint to stream live turn-by-turn messages and status.
    """
    async def event_generator():
        last_turn = 0
        is_finished = False
        
        while not is_finished:
            db = SessionLocal()
            try:
                session = db.query(DatingSession).filter(DatingSession.id == session_id).first()
                if not session:
                    yield f"event: error\ndata: {json.dumps({'error': 'Session not found'})}\n\n"
                    break

                messages = db.query(ConversationMessage).filter(
                    ConversationMessage.session_id == session_id,
                    ConversationMessage.turn_number > last_turn
                ).order_by(ConversationMessage.turn_number.asc()).all()

                for msg in messages:
                    payload = {
                        "turn": msg.turn_number,
                        "sender_name": msg.sender_participant.name if msg.sender_participant else msg.sender_agent_role,
                        "role": msg.sender_agent_role,
                        "content": msg.content,
                        "decision_summary": msg.decision_summary or (msg.internal_thought[:140] if msg.internal_thought else None),
                        "decision_factors": msg.decision_factors or [],
                        "question": msg.question_asked,
                        "interest": msg.interest_referenced
                    }
                    yield f"event: message\ndata: {json.dumps(payload)}\n\n"
                    last_turn = msg.turn_number

                if session.status in ("completed", "incompatible", "failed", "cancelled"):
                    summary_payload = {
                        "status": session.status,
                        "outcome": session.outcome_status,
                        "summary": session.outcome_summary,
                        "engagement_score": session.mutual_engagement_score,
                        "shared_interests": session.shared_interests_found,
                        "friction_points": session.friction_points
                    }
                    yield f"event: complete\ndata: {json.dumps(summary_payload)}\n\n"
                    is_finished = True
                    break

            finally:
                db.close()

            await asyncio.sleep(1.0)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

def _build_session_response(session: DatingSession, db: Session) -> DatingSessionResponse:
    p_a = session.participant_a
    p_b = session.participant_b
    
    msgs = [
        ConversationMessageResponse(
            id=m.id,
            turn_number=m.turn_number,
            sender_participant_id=m.sender_participant_id,
            sender_name=m.sender_participant.name if m.sender_participant else None,
            sender_agent_role=m.sender_agent_role,
            content=m.content,
            decision_summary=m.decision_summary or (m.internal_thought[:140] if m.internal_thought else None),
            decision_factors=m.decision_factors or [],
            internal_thought=None,
            question_asked=m.question_asked,
            interest_referenced=m.interest_referenced,
            timestamp=m.timestamp,
            tokens=m.tokens
        )
        for m in session.messages
    ]

    evals = [
        AgentEvaluationResponse(
            id=e.id,
            evaluator_participant_id=e.evaluator_participant_id,
            evaluator_name=e.evaluator.name if e.evaluator else None,
            target_participant_id=e.target_participant_id,
            target_name=e.target.name if e.target else None,
            chemistry_score=e.chemistry_score,
            communication_comfort=e.communication_comfort,
            shared_values_alignment=e.shared_values_alignment,
            would_date_again=e.would_date_again,
            evaluation_rationale=e.evaluation_rationale,
            perceived_green_flags=e.perceived_green_flags or [],
            perceived_red_flags=e.perceived_red_flags or [],
            unanswered_questions=e.unanswered_questions or [],
            created_at=e.created_at
        )
        for e in session.evaluations
    ]

    return DatingSessionResponse(
        id=session.id,
        run_id=session.run_id,
        participant_a_id=session.participant_a_id,
        participant_a_name=p_a.name if p_a else "Unknown",
        participant_b_id=session.participant_b_id,
        participant_b_name=p_b.name if p_b else "Unknown",
        is_synthetic=bool(session.is_synthetic),
        status=session.status,
        current_turn=session.current_turn,
        total_turns=session.total_turns,
        agent_a_objective=session.agent_a_objective,
        agent_b_objective=session.agent_b_objective,
        outcome_status=session.outcome_status,
        outcome_summary=session.outcome_summary,
        shared_interests_found=session.shared_interests_found or [],
        friction_points=session.friction_points or [],
        mutual_engagement_score=session.mutual_engagement_score or 0.0,
        total_tokens_used=session.total_tokens_used or 0,
        approx_cost_usd=session.approx_cost_usd or 0.0,
        latency_ms=session.latency_ms or 0,
        error_detail=session.error_detail,
        started_at=session.started_at,
        completed_at=session.completed_at,
        messages=msgs,
        evaluations=evals
    )

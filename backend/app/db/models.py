import datetime
import uuid
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.db.base import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Participant(Base):
    __tablename__ = "participants"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String(50), nullable=True)
    target_gender = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    
    linkedin_url = Column(String(512), unique=True, nullable=False, index=True)
    linkedin_handle = Column(String(255), nullable=False)
    instagram_url = Column(String(512), unique=True, nullable=False, index=True)
    instagram_handle = Column(String(255), nullable=False)
    
    consent_status = Column(String(50), default="consented", nullable=False)
    consent_timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    status = Column(String(50), default="pending", nullable=False)  # pending, analyzed, failed, withdrawn
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    evidence_items = relationship("EvidenceItem", back_populates="participant", cascade="all, delete-orphan")
    analyzed_profile = relationship("AnalyzedProfile", back_populates="participant", uselist=False, cascade="all, delete-orphan")
    rankings_as_source = relationship("CompatibilityRanking", foreign_keys="CompatibilityRanking.source_participant_id", back_populates="source_participant", cascade="all, delete-orphan")
    rankings_as_target = relationship("CompatibilityRanking", foreign_keys="CompatibilityRanking.target_participant_id", back_populates="target_participant", cascade="all, delete-orphan")


class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    participant_id = Column(String(36), ForeignKey("participants.id", ondelete="CASCADE"), nullable=False, index=True)
    source_platform = Column(String(50), nullable=False)  # linkedin, instagram
    source_url = Column(String(512), nullable=False)
    category = Column(String(100), nullable=False)  # professional, hobby, interest, lifestyle, communication, relationship_preference
    evidence_type = Column(String(50), nullable=False)  # explicit_statement, observed_activity, model_interpretation
    raw_quote = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)
    retrieved_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    participant = relationship("Participant", back_populates="evidence_items")


class AnalyzedProfile(Base):
    __tablename__ = "analyzed_profiles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    participant_id = Column(String(36), ForeignKey("participants.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    summary = Column(Text, nullable=False)
    
    career_interests = Column(JSON, default=list)
    demonstrated_hobbies = Column(JSON, default=list)
    stated_interests = Column(JSON, default=list)
    lifestyle_preferences = Column(JSON, default=list)
    communication_preferences = Column(JSON, default=list)
    relationship_preferences = Column(JSON, default=list)
    
    explicit_facts = Column(JSON, default=list)
    inferences_with_confidence = Column(JSON, default=list)
    uncertainties_and_unknowns = Column(JSON, default=list)
    
    model_version = Column(String(100), default="gemini-2.5-flash")
    analyzed_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    participant = relationship("Participant", back_populates="analyzed_profile")


class DemonstrationRun(Base):
    __tablename__ = "demonstration_runs"

    id = Column(String(128), primary_key=True)
    name = Column(String(255), nullable=False)
    status = Column(String(50), default="pending", nullable=False)  # pending, running, completed, failed, cancelled
    total_participants = Column(Integer, default=0)
    total_eligible_pairs = Column(Integer, default=0)
    simulated_pairs = Column(Integer, default=0)
    completed_sessions = Column(Integer, default=0)
    failed_sessions = Column(Integer, default=0)
    model_used = Column(String(100), default="gemini-2.5-flash")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    execution_summary = Column(JSON, default=dict)


class EligibleCandidatePair(Base):
    __tablename__ = "eligible_candidate_pairs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    run_id = Column(String(128), ForeignKey("demonstration_runs.id"), nullable=False, index=True)
    participant_a_id = Column(String(36), ForeignKey("participants.id"), nullable=False)
    participant_b_id = Column(String(36), ForeignKey("participants.id"), nullable=False)
    is_eligible = Column(Boolean, default=True, nullable=False)
    ineligibility_reason = Column(String(255), nullable=True)
    pair_status = Column(String(50), default="pending", nullable=False)  # pending, simulating, completed, failed, skipped
    session_id = Column(String(36), nullable=True)

    __table_args__ = (
        UniqueConstraint("run_id", "participant_a_id", "participant_b_id", name="uq_run_pair"),
    )


class DatingSession(Base):
    __tablename__ = "dating_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    run_id = Column(String(128), nullable=True, index=True)
    participant_a_id = Column(String(36), ForeignKey("participants.id"), nullable=False, index=True)
    participant_b_id = Column(String(36), ForeignKey("participants.id"), nullable=False, index=True)
    status = Column(String(50), default="initialized", nullable=False)  # initialized, in_progress, completed, incompatible, failed, cancelled
    
    current_turn = Column(Integer, default=0)
    total_turns = Column(Integer, default=0)
    agent_a_objective = Column(Text, nullable=True)
    agent_b_objective = Column(Text, nullable=True)
    
    outcome_status = Column(String(50), nullable=True)  # second_date_agreed, mutual_friendship, polite_pass, incompatible
    outcome_summary = Column(Text, nullable=True)
    shared_interests_found = Column(JSON, default=list)
    friction_points = Column(JSON, default=list)
    mutual_engagement_score = Column(Float, default=0.0)
    
    total_tokens_used = Column(Integer, default=0)
    approx_cost_usd = Column(Float, default=0.0)
    latency_ms = Column(Integer, default=0)
    error_detail = Column(Text, nullable=True)
    
    started_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    participant_a = relationship("Participant", foreign_keys=[participant_a_id])
    participant_b = relationship("Participant", foreign_keys=[participant_b_id])
    messages = relationship("ConversationMessage", back_populates="session", order_by="ConversationMessage.turn_number", cascade="all, delete-orphan")
    evaluations = relationship("AgentEvaluation", back_populates="session", cascade="all, delete-orphan")


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("dating_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    turn_number = Column(Integer, nullable=False)
    sender_participant_id = Column(String(36), ForeignKey("participants.id"), nullable=False)
    sender_agent_role = Column(String(20), nullable=False)  # "Agent A", "Agent B"
    content = Column(Text, nullable=False)
    internal_thought = Column(Text, nullable=True)
    question_asked = Column(Text, nullable=True)
    interest_referenced = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    tokens = Column(Integer, default=0)

    session = relationship("DatingSession", back_populates="messages")
    sender_participant = relationship("Participant", foreign_keys=[sender_participant_id])


class AgentEvaluation(Base):
    __tablename__ = "agent_evaluations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("dating_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    evaluator_participant_id = Column(String(36), ForeignKey("participants.id"), nullable=False)
    target_participant_id = Column(String(36), ForeignKey("participants.id"), nullable=False)
    
    chemistry_score = Column(Float, nullable=False)  # 1-10
    communication_comfort = Column(Float, nullable=False)  # 1-10
    shared_values_alignment = Column(Float, nullable=False)  # 1-10
    would_date_again = Column(Boolean, nullable=False)
    evaluation_rationale = Column(Text, nullable=False)
    perceived_green_flags = Column(JSON, default=list)
    perceived_red_flags = Column(JSON, default=list)
    unanswered_questions = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    session = relationship("DatingSession", back_populates="evaluations")
    evaluator = relationship("Participant", foreign_keys=[evaluator_participant_id])
    target = relationship("Participant", foreign_keys=[target_participant_id])


class CompatibilityRanking(Base):
    __tablename__ = "compatibility_rankings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    run_id = Column(String(128), nullable=True, index=True)
    source_participant_id = Column(String(36), ForeignKey("participants.id", ondelete="CASCADE"), nullable=False, index=True)
    target_participant_id = Column(String(36), ForeignKey("participants.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(36), ForeignKey("dating_sessions.id"), nullable=True)
    
    rank = Column(Integer, nullable=False)
    individual_score = Column(Float, nullable=False)  # Directional Score A -> B (0 - 100)
    reciprocal_score = Column(Float, nullable=False)  # Harmonized Score between A and B (0 - 100)
    
    preference_score = Column(Float, default=0.0)
    interest_score = Column(Float, default=0.0)
    lifestyle_score = Column(Float, default=0.0)
    engagement_score = Column(Float, default=0.0)
    values_score = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)
    
    shared_interests = Column(JSON, default=list)
    potential_incompatibilities = Column(JSON, default=list)
    supporting_evidence_summary = Column(Text, nullable=True)
    ranking_explanation = Column(Text, nullable=False)
    calculated_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    source_participant = relationship("Participant", foreign_keys=[source_participant_id], back_populates="rankings_as_source")
    target_participant = relationship("Participant", foreign_keys=[target_participant_id], back_populates="rankings_as_target")
    dating_session = relationship("DatingSession", foreign_keys=[session_id])


class BackgroundJob(Base):
    __tablename__ = "background_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_type = Column(String(50), nullable=False)  # batch_run, profile_analysis, dating_session, ranking_calc
    status = Column(String(50), default="queued", nullable=False)  # queued, running, completed, failed, cancelled
    progress_pct = Column(Integer, default=0)
    payload = Column(JSON, default=dict)
    result = Column(JSON, default=dict)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

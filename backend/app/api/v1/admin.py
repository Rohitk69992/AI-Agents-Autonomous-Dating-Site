import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.db.models import (
    Participant, DatingSession, AnalyzedProfile, BackgroundJob, DemonstrationRun
)
from app.schemas.admin import (
    HealthResponse, AdminConfigResponse, UpdateConfigAdminRequest, ObservabilityMetricsResponse
)
from app.core.config import settings
from app.core.security import require_admin_auth

router = APIRouter(tags=["Admin & Observability"])

@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    # Test DB query
    try:
        db.execute(func.now() if not settings.DATABASE_URL.startswith("sqlite") else func.datetime('now'))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    active_jobs = db.query(BackgroundJob).filter(BackgroundJob.status.in_(["queued", "running"])).count()
    active_model = settings.GROQ_MODEL if settings.LLM_PROVIDER == "groq" else settings.GEMINI_MODEL

    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        version=settings.VERSION,
        database=db_status,
        llm_provider=settings.LLM_PROVIDER,
        llm_model=active_model,
        active_background_jobs=active_jobs
    )

@router.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    return {"status": "ready", "timestamp": datetime.datetime.utcnow().isoformat()}

@router.get("/admin/config", response_model=AdminConfigResponse)
def get_admin_config():
    masked_db = settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else settings.DATABASE_URL
    active_model = settings.GROQ_MODEL if settings.LLM_PROVIDER == "groq" else settings.GEMINI_MODEL
    key_configured = bool(settings.GROQ_API_KEY) if settings.LLM_PROVIDER == "groq" else bool(settings.GEMINI_API_KEY)
    return AdminConfigResponse(
        llm_provider=settings.LLM_PROVIDER,
        gemini_model=active_model,
        groq_model=settings.GROQ_MODEL,
        api_key_configured=key_configured,
        database_url_masked=masked_db,
        max_turns=settings.MAX_CONVERSATION_TURNS,
        ranking_weights={
            "weight_preferences": settings.WEIGHT_PREFERENCES,
            "weight_shared_interests": settings.WEIGHT_SHARED_INTERESTS,
            "weight_lifestyle_fit": settings.WEIGHT_LIFESTYLE_FIT,
            "weight_date_engagement": settings.WEIGHT_DATE_ENGAGEMENT,
            "weight_values_priorities": settings.WEIGHT_VALUES_PRIORITIES,
        },
        demo_run_id=settings.DEMO_RUN_ID
    )

@router.post("/admin/config", response_model=AdminConfigResponse)
def update_admin_config(
    req: UpdateConfigAdminRequest,
    _: bool = Depends(require_admin_auth)
):
    if req.llm_provider:
        settings.LLM_PROVIDER = req.llm_provider
    if req.groq_model:
        settings.GROQ_MODEL = req.groq_model
    if req.gemini_model:
        if settings.LLM_PROVIDER == "groq":
            settings.GROQ_MODEL = req.gemini_model
        else:
            settings.GEMINI_MODEL = req.gemini_model
    if req.max_turns:
        settings.MAX_CONVERSATION_TURNS = req.max_turns
    if req.ranking_weights:
        settings.WEIGHT_PREFERENCES = req.ranking_weights.get("weight_preferences", settings.WEIGHT_PREFERENCES)
        settings.WEIGHT_SHARED_INTERESTS = req.ranking_weights.get("weight_shared_interests", settings.WEIGHT_SHARED_INTERESTS)
        settings.WEIGHT_LIFESTYLE_FIT = req.ranking_weights.get("weight_lifestyle_fit", settings.WEIGHT_LIFESTYLE_FIT)
        settings.WEIGHT_DATE_ENGAGEMENT = req.ranking_weights.get("weight_date_engagement", settings.WEIGHT_DATE_ENGAGEMENT)
        settings.WEIGHT_VALUES_PRIORITIES = req.ranking_weights.get("weight_values_priorities", settings.WEIGHT_VALUES_PRIORITIES)
    return get_admin_config()

@router.get("/admin/metrics", response_model=ObservabilityMetricsResponse)
def get_observability_metrics(db: Session = Depends(get_db)):
    total_parts = db.query(Participant).count()
    synth_parts = db.query(Participant).filter(Participant.is_synthetic == True).count()
    verified_parts = db.query(Participant).filter(Participant.is_synthetic == False, Participant.consent_verified == True).count()
    withdrawn_parts = db.query(Participant).filter(Participant.status == "withdrawn").count()
    analyzed_parts = db.query(Participant).filter(Participant.status == "analyzed").count()
    total_sessions = db.query(DatingSession).count()
    completed_sessions = db.query(DatingSession).filter(DatingSession.status == "completed").count()
    failed_sessions = db.query(DatingSession).filter(DatingSession.status.in_(["failed", "incompatible"])).count()

    total_tokens = db.query(func.sum(DatingSession.total_tokens_used)).scalar() or 0
    total_cost = db.query(func.sum(DatingSession.approx_cost_usd)).scalar() or 0.0
    avg_latency = db.query(func.avg(DatingSession.latency_ms)).scalar() or 0.0

    return ObservabilityMetricsResponse(
        total_participants=total_parts,
        synthetic_participants=synth_parts,
        verified_participants=verified_parts,
        withdrawn_participants=withdrawn_parts,
        analyzed_participants=analyzed_parts,
        total_dating_sessions=total_sessions,
        completed_sessions=completed_sessions,
        failed_sessions=failed_sessions,
        total_tokens_consumed=int(total_tokens),
        estimated_total_cost_usd=round(float(total_cost), 4),
        average_session_latency_ms=round(float(avg_latency), 1)
    )

@router.post("/admin/seed-demo")
def trigger_seed_demo(
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin_auth)
):
    from app.db.seed_demo import seed_database
    try:
        seed_database(db=db, run_simulation=True)
        return {"status": "success", "message": "Demonstration dataset seeded and simulated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to seed demo dataset: {str(e)}")


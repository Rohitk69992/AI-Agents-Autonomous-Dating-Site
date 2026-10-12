import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import DemonstrationRun, EligibleCandidatePair, Participant, BackgroundJob
from app.schemas.run import DemonstrationRunResponse, StartRunRequest, RunProgressResponse
from app.worker.manager import worker_manager
from app.dating.harness import check_eligibility

router = APIRouter(prefix="/runs", tags=["Demonstration Runs"])

@router.post("", response_model=DemonstrationRunResponse, status_code=status.HTTP_202_ACCEPTED)
def start_demonstration_run(
    req: StartRunRequest,
    db: Session = Depends(get_db)
):
    run_id = req.run_id or "demo-run-25-participants"
    run = db.query(DemonstrationRun).filter(DemonstrationRun.id == run_id).first()
    
    participants = db.query(Participant).filter(
        Participant.consent_status == "consented",
        Participant.status != "withdrawn"
    ).all()

    if len(participants) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"At least 2 consented participants required to generate pairs. Current count: {len(participants)}."
        )

    if not run:
        run = DemonstrationRun(
            id=run_id,
            name=req.name or f"Official Demonstration Simulation ({len(participants)} Participants)",
            status="pending",
            total_participants=len(participants),
            started_at=datetime.datetime.utcnow()
        )
        db.add(run)
        db.commit()
        db.refresh(run)

    # Generate all unordered candidate pairs (N * (N-1) / 2)
    pair_count = 0
    for i in range(len(participants)):
        for j in range(i + 1, len(participants)):
            p_a = participants[i]
            p_b = participants[j]
            
            # Check existing pair
            existing_pair = db.query(EligibleCandidatePair).filter(
                EligibleCandidatePair.run_id == run_id,
                EligibleCandidatePair.participant_a_id == p_a.id,
                EligibleCandidatePair.participant_b_id == p_b.id
            ).first()

            if not existing_pair:
                is_el, inelig_reason = check_eligibility(p_a, p_b)
                pair = EligibleCandidatePair(
                    run_id=run_id,
                    participant_a_id=p_a.id,
                    participant_b_id=p_b.id,
                    is_eligible=is_el,
                    ineligibility_reason=inelig_reason,
                    pair_status="pending" if is_el else "skipped"
                )
                db.add(pair)
            pair_count += 1

    run.total_eligible_pairs = pair_count
    run.total_participants = len(participants)
    db.commit()

    # Launch background simulation job
    job_id = worker_manager.enqueue_job("demonstration_run", {"run_id": run_id, "max_turns": 4})
    
    return DemonstrationRunResponse.from_orm(run)

@router.get("/{run_id}", response_model=DemonstrationRunResponse)
def get_run(run_id: str, db: Session = Depends(get_db)):
    run = db.query(DemonstrationRun).filter(DemonstrationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Demonstration run not found")
    return DemonstrationRunResponse.from_orm(run)

@router.get("/{run_id}/progress", response_model=RunProgressResponse)
def get_run_progress(run_id: str, db: Session = Depends(get_db)):
    run = db.query(DemonstrationRun).filter(DemonstrationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Demonstration run not found")

    pairs = db.query(EligibleCandidatePair).filter(EligibleCandidatePair.run_id == run_id).all()
    total = len(pairs)
    completed = sum(1 for p in pairs if p.pair_status == "completed")
    failed = sum(1 for p in pairs if p.pair_status == "failed")
    pending = sum(1 for p in pairs if p.pair_status in ("pending", "simulating"))

    pct = round((completed / max(total, 1)) * 100.0, 1)

    return RunProgressResponse(
        run_id=run.id,
        status=run.status,
        percent_complete=pct,
        total_pairs=total,
        completed_pairs=completed,
        failed_pairs=failed,
        pending_pairs=pending
    )

@router.post("/{run_id}/resume", response_model=DemonstrationRunResponse)
def resume_run(run_id: str, db: Session = Depends(get_db)):
    run = db.query(DemonstrationRun).filter(DemonstrationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Demonstration run not found")

    worker_manager.enqueue_job("demonstration_run", {"run_id": run_id, "max_turns": 4})
    run.status = "running"
    db.commit()
    return DemonstrationRunResponse.from_orm(run)

@router.get("", response_model=List[DemonstrationRunResponse])
def list_runs(db: Session = Depends(get_db)):
    runs = db.query(DemonstrationRun).order_by(DemonstrationRun.started_at.desc()).all()
    return [DemonstrationRunResponse.from_orm(r) for r in runs]

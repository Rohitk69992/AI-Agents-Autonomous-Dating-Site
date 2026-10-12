import datetime
import logging
import threading
import time
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import (
    DemonstrationRun, EligibleCandidatePair, DatingSession, Participant, BackgroundJob
)
from app.dating.harness import check_eligibility, execute_dating_session
from app.ranking.engine import calculate_rankings_for_participant
from app.analysis.analyzer import analyze_participant_profile

logger = logging.getLogger(__name__)

class BackgroundWorkerManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(BackgroundWorkerManager, cls).__new__(cls)
                cls._instance._active_jobs = {}
                cls._instance._stop_flags = {}
        return cls._instance

    def enqueue_job(self, job_type: str, payload: Dict[str, Any]) -> str:
        db = SessionLocal()
        try:
            job = BackgroundJob(
                job_type=job_type,
                status="queued",
                progress_pct=0,
                payload=payload,
                created_at=datetime.datetime.utcnow()
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            job_id = job.id
        finally:
            db.close()

        # Launch in worker thread
        t = threading.Thread(target=self._run_job_wrapper, args=(job_id, job_type, payload), daemon=True)
        t.start()
        return job_id

    def cancel_job(self, job_id: str) -> bool:
        with self._lock:
            self._stop_flags[job_id] = True
        db = SessionLocal()
        try:
            job = db.query(BackgroundJob).filter(BackgroundJob.id == job_id).first()
            if job:
                job.status = "cancelled"
                db.commit()
                return True
            return False
        finally:
            db.close()

    def _run_job_wrapper(self, job_id: str, job_type: str, payload: Dict[str, Any]):
        db = SessionLocal()
        try:
            job = db.query(BackgroundJob).filter(BackgroundJob.id == job_id).first()
            if not job:
                return
            job.status = "running"
            db.commit()

            if job_type == "demonstration_run":
                self._execute_demonstration_run(job_id, payload.get("run_id", "demo-run-25-participants"), payload.get("max_turns", 4))
            elif job_type == "single_dating_session":
                self._execute_single_dating_job(job_id, payload.get("session_id"), payload.get("max_turns", 6))
            elif job_type == "analyze_profile":
                self._execute_analysis_job(job_id, payload.get("participant_id"))

            job = db.query(BackgroundJob).filter(BackgroundJob.id == job_id).first()
            if job and job.status != "cancelled":
                job.status = "completed"
                job.progress_pct = 100
                db.commit()
        except Exception as e:
            logger.exception(f"Job {job_id} failed: {e}")
            job = db.query(BackgroundJob).filter(BackgroundJob.id == job_id).first()
            if job:
                job.status = "failed"
                job.error = str(e)
                db.commit()
        finally:
            db.close()
            with self._lock:
                self._stop_flags.pop(job_id, None)

    def _execute_analysis_job(self, job_id: str, participant_id: str):
        db = SessionLocal()
        try:
            analyze_participant_profile(db, participant_id)
        finally:
            db.close()

    def _execute_single_dating_job(self, job_id: str, session_id: str, max_turns: int):
        db = SessionLocal()
        try:
            execute_dating_session(db, session_id, max_turns=max_turns)
            session = db.query(DatingSession).filter(DatingSession.id == session_id).first()
            if session:
                calculate_rankings_for_participant(db, session.participant_a_id)
                calculate_rankings_for_participant(db, session.participant_b_id)
        finally:
            db.close()

    def _execute_demonstration_run(self, job_id: str, run_id: str, max_turns: int):
        db = SessionLocal()
        try:
            run = db.query(DemonstrationRun).filter(DemonstrationRun.id == run_id).first()
            if not run:
                run = DemonstrationRun(
                    id=run_id,
                    name="Official 25-Participant Demonstration Simulation",
                    status="running",
                    started_at=datetime.datetime.utcnow()
                )
                db.add(run)
                db.commit()
            else:
                run.status = "running"
                if not run.started_at:
                    run.started_at = datetime.datetime.utcnow()
                db.commit()

            # Retrieve candidate pairs for this run
            pairs = db.query(EligibleCandidatePair).filter(EligibleCandidatePair.run_id == run_id).all()
            total_pairs = len(pairs)
            run.total_eligible_pairs = total_pairs

            for idx, pair in enumerate(pairs):
                # Check for cancellation
                if self._stop_flags.get(job_id, False):
                    run.status = "cancelled"
                    db.commit()
                    return

                # If pair is already completed, skip to maintain idempotency
                if pair.pair_status == "completed" and pair.session_id:
                    continue

                if not pair.is_eligible:
                    pair.pair_status = "skipped"
                    db.commit()
                    continue

                pair.pair_status = "simulating"
                db.commit()

                # Create or locate dating session
                session = DatingSession(
                    run_id=run_id,
                    participant_a_id=pair.participant_a_id,
                    participant_b_id=pair.participant_b_id,
                    status="initialized"
                )
                db.add(session)
                db.commit()
                db.refresh(session)
                pair.session_id = session.id

                try:
                    execute_dating_session(db, session.id, max_turns=max_turns)
                    pair.pair_status = "completed"
                    run.completed_sessions = (run.completed_sessions or 0) + 1
                except Exception as e:
                    logger.error(f"Error simulating pair {pair.id}: {e}")
                    pair.pair_status = "failed"
                    run.failed_sessions = (run.failed_sessions or 0) + 1

                run.simulated_pairs = (run.simulated_pairs or 0) + 1
                
                # Update job progress
                job = db.query(BackgroundJob).filter(BackgroundJob.id == job_id).first()
                if job:
                    job.progress_pct = int(((idx + 1) / max(total_pairs, 1)) * 100)

                db.commit()

            # After all pairs are simulated, calculate explainable rankings for all participants
            participants = db.query(Participant).filter(
                Participant.consent_status == "consented",
                Participant.status != "withdrawn"
            ).all()

            for p in participants:
                calculate_rankings_for_participant(db, p.id, run_id=run_id)

            run.status = "completed"
            run.completed_at = datetime.datetime.utcnow()
            run.execution_summary = {
                "total_pairs": total_pairs,
                "simulated_pairs": run.simulated_pairs,
                "completed_sessions": run.completed_sessions,
                "failed_sessions": run.failed_sessions,
                "policy": f"Complete All-Pairs Simulation ({max_turns} turns per date)"
            }
            db.commit()
        finally:
            db.close()

worker_manager = BackgroundWorkerManager()

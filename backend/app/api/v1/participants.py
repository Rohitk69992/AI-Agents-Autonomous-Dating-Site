import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Participant, EvidenceItem, AnalyzedProfile
from app.schemas.participant import (
    ParticipantCreate, ParticipantBatchCreate, ParticipantResponse,
    EvidenceItemResponse, AnalyzedProfileResponse,
    ManifestImportRequest, ManifestImportResponse
)
from app.core.security import (
    validate_and_normalize_linkedin_url, validate_and_normalize_instagram_url,
    require_admin_auth
)
from app.adapters.linkedin import LinkedInAcquisitionAdapter
from app.adapters.instagram import InstagramAcquisitionAdapter
from app.analysis.analyzer import analyze_participant_profile

router = APIRouter(prefix="/participants", tags=["Participants"])

def _build_participant_response(p: Participant) -> ParticipantResponse:
    analyzed_resp = None
    if p.analyzed_profile:
        analyzed_resp = AnalyzedProfileResponse.model_validate(p.analyzed_profile)
    return ParticipantResponse(
        id=p.id,
        name=p.name,
        age=p.age,
        gender=p.gender,
        target_gender=p.target_gender,
        location=p.location,
        linkedin_url=p.linkedin_url,
        linkedin_handle=p.linkedin_handle,
        instagram_url=p.instagram_url,
        instagram_handle=p.instagram_handle,
        consent_status=p.consent_status,
        consent_timestamp=p.consent_timestamp,
        consent_verified=bool(getattr(p, "consent_verified", False)),
        source_verified=bool(getattr(p, "source_verified", False)),
        is_synthetic=bool(getattr(p, "is_synthetic", False)),
        simulation_eligible=bool(getattr(p, "simulation_eligible", True)),
        status=p.status,
        analysis_status=getattr(p, "analysis_status", "pending") or "pending",
        created_at=p.created_at,
        analyzed_profile=analyzed_resp,
        evidence_count=len(p.evidence_items)
    )

@router.post("", response_model=ParticipantResponse, status_code=status.HTTP_201_CREATED)
def create_participant(
    data: ParticipantCreate,
    db: Session = Depends(get_db)
):
    if not data.consent_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Participant consent confirmation is strictly required to represent a person via an AI agent."
        )

    # Validate LinkedIn URL
    valid_li, norm_li, li_handle = validate_and_normalize_linkedin_url(data.linkedin_url)
    if not valid_li:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid LinkedIn URL '{data.linkedin_url}'. Expected format: https://www.linkedin.com/in/username"
        )

    # Validate Instagram URL
    valid_ig, norm_ig, ig_handle = validate_and_normalize_instagram_url(data.instagram_url)
    if not valid_ig:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid Instagram URL '{data.instagram_url}'. Expected format: https://www.instagram.com/username"
        )

    # Duplicate check
    existing_li = db.query(Participant).filter(Participant.linkedin_url == norm_li).first()
    if existing_li:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A participant with LinkedIn URL '{norm_li}' already exists (ID: {existing_li.id})."
        )
    existing_ig = db.query(Participant).filter(Participant.instagram_url == norm_ig).first()
    if existing_ig:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A participant with Instagram URL '{norm_ig}' already exists (ID: {existing_ig.id})."
        )

    participant = Participant(
        name=data.name.strip(),
        age=data.age,
        gender=data.gender,
        target_gender=data.target_gender,
        location=data.location,
        linkedin_url=norm_li,
        linkedin_handle=li_handle,
        instagram_url=norm_ig,
        instagram_handle=ig_handle,
        consent_status="consented",
        consent_timestamp=datetime.datetime.utcnow(),
        consent_verified=True,
        source_verified=False,
        is_synthetic=False,
        simulation_eligible=True,
        status="pending",
        analysis_status="pending"
    )
    db.add(participant)
    db.commit()
    db.refresh(participant)

    # Attempt initial source acquisition via adapters
    li_adapter = LinkedInAcquisitionAdapter()
    ig_adapter = InstagramAcquisitionAdapter()
    
    li_res = li_adapter.acquire(norm_li, li_handle)
    for item in li_res.evidence_items:
        db.add(EvidenceItem(
            participant_id=participant.id,
            source_platform="linkedin",
            source_url=norm_li,
            category=item.category,
            evidence_type=item.evidence_type,
            raw_quote=item.raw_quote,
            confidence=item.confidence,
            is_synthetic=False,
            processing_version="1.0.0"
        ))

    ig_res = ig_adapter.acquire(norm_ig, ig_handle)
    for item in ig_res.evidence_items:
        db.add(EvidenceItem(
            participant_id=participant.id,
            source_platform="instagram",
            source_url=norm_ig,
            category=item.category,
            evidence_type=item.evidence_type,
            raw_quote=item.raw_quote,
            confidence=item.confidence,
            is_synthetic=False,
            processing_version="1.0.0"
        ))

    db.commit()
    db.refresh(participant)

    # Trigger initial analysis
    analyze_participant_profile(db, participant.id)
    db.refresh(participant)

    return _build_participant_response(participant)

@router.post("/import-manifest", response_model=ManifestImportResponse, status_code=status.HTTP_200_OK)
def import_participant_manifest(
    req: ManifestImportRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin_auth)
):
    imported_ids = []
    errors = []
    skipped = 0

    for item in req.participants:
        valid_li, norm_li, li_handle = validate_and_normalize_linkedin_url(item.linkedin_url)
        valid_ig, norm_ig, ig_handle = validate_and_normalize_instagram_url(item.instagram_url)
        if not valid_li or not valid_ig:
            errors.append(f"Invalid URLs for {item.name}: {item.linkedin_url}, {item.instagram_url}")
            skipped += 1
            continue

        existing = db.query(Participant).filter(
            (Participant.linkedin_url == norm_li) | (Participant.instagram_url == norm_ig)
        ).first()
        if existing:
            skipped += 1
            continue

        p = Participant(
            name=item.name.strip(),
            age=item.age,
            gender=item.gender,
            target_gender=item.target_gender,
            location=item.location,
            linkedin_url=norm_li,
            linkedin_handle=li_handle,
            instagram_url=norm_ig,
            instagram_handle=ig_handle,
            consent_status="consented",
            consent_timestamp=datetime.datetime.utcnow(),
            consent_verified=item.consent_verified,
            source_verified=item.source_verified,
            is_synthetic=False,
            simulation_eligible=True,
            status="pending",
            analysis_status="pending"
        )
        db.add(p)
        db.commit()
        db.refresh(p)

        for ev in item.evidence:
            ev_item = EvidenceItem(
                participant_id=p.id,
                source_platform=ev.platform,
                source_url=norm_li if ev.platform == "linkedin" else norm_ig,
                category=ev.category,
                evidence_type=ev.type,
                raw_quote=ev.quote,
                confidence=ev.confidence,
                is_synthetic=False,
                processing_version="1.0.0",
                retrieved_at=datetime.datetime.utcnow()
            )
            db.add(ev_item)
        db.commit()

        if req.run_immediate_analysis:
            try:
                analyze_participant_profile(db, p.id)
            except Exception as e:
                errors.append(f"Analysis failed for {p.name}: {str(e)}")

        imported_ids.append(p.id)

    return ManifestImportResponse(
        imported_count=len(imported_ids),
        skipped_count=skipped,
        errors=errors,
        imported_participant_ids=imported_ids
    )

@router.get("", response_model=List[ParticipantResponse])
def list_participants(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Participant)
    if search:
        query = query.filter(Participant.name.ilike(f"%{search}%"))
    if status_filter:
        query = query.filter(Participant.status == status_filter)

    participants = query.order_by(Participant.created_at.desc()).offset(skip).limit(limit).all()
    return [_build_participant_response(p) for p in participants]

@router.get("/{participant_id}", response_model=ParticipantResponse)
def get_participant(participant_id: str, db: Session = Depends(get_db)):
    p = db.query(Participant).filter(Participant.id == participant_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Participant not found")
    return _build_participant_response(p)

@router.delete("/{participant_id}", status_code=status.HTTP_200_OK)
def delete_or_withdraw_participant(
    participant_id: str,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin_auth)
):
    p = db.query(Participant).filter(Participant.id == participant_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Participant not found")
    
    # Cascade delete according to privacy & right-to-be-forgotten policy
    db.delete(p)
    db.commit()
    return {"status": "success", "message": f"Participant {participant_id} and all associated data permanently removed."}

@router.post("/{participant_id}/analyze", response_model=AnalyzedProfileResponse)
def trigger_analysis(participant_id: str, db: Session = Depends(get_db)):
    analyzed = analyze_participant_profile(db, participant_id)
    if not analyzed:
        raise HTTPException(status_code=404, detail="Failed to analyze participant.")
    return AnalyzedProfileResponse.model_validate(analyzed)

@router.get("/{participant_id}/profile", response_model=AnalyzedProfileResponse)
def get_participant_profile(participant_id: str, db: Session = Depends(get_db)):
    p = db.query(Participant).filter(Participant.id == participant_id).first()
    if not p or not p.analyzed_profile:
        raise HTTPException(status_code=404, detail="Profile analysis not found for participant.")
    return AnalyzedProfileResponse.model_validate(p.analyzed_profile)

@router.get("/{participant_id}/evidence", response_model=List[EvidenceItemResponse])
def get_participant_evidence(participant_id: str, db: Session = Depends(get_db)):
    evidence = db.query(EvidenceItem).filter(EvidenceItem.participant_id == participant_id).all()
    return [EvidenceItemResponse.model_validate(item) for item in evidence]

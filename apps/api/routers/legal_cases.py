from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from db.session import get_db
from app.models.domain_models import Claim, LegalEscalationRecord
from app.services.legal_case_service import (
    calculate_tiered_fee,
    escalate_claim_to_legal,
    update_litigation_milestone,
    get_legal_escalation_record,
    assemble_case_file_dossier,
)

router = APIRouter(prefix="/api/claims", tags=["legal-cases"])

class EscalateClaimRequest(BaseModel):
    user_id: str
    escalation_tier_rate: float = Field(0.30, ge=0.20, le=0.40)
    escalation_reason: Optional[str] = None
    assigned_counsel_name: Optional[str] = None
    counsel_firm: Optional[str] = None

class MilestoneUpdateRequest(BaseModel):
    milestone: str
    notes: Optional[str] = None

class TieredFeeCalculateRequest(BaseModel):
    recovery_amount: float
    is_escalated: bool = False
    escalation_rate: float = 0.30
    standard_rate: float = 0.20

class LegalEscalationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    claim_id: str
    organization_id: str
    is_escalated: bool
    escalation_tier_rate: float
    escalated_by_user_id: Optional[str] = None
    escalated_at: Optional[str] = None
    escalation_reason: Optional[str] = None
    current_milestone: str
    milestone_updated_at: Optional[str] = None
    assigned_counsel_name: Optional[str] = None
    counsel_firm: Optional[str] = None
    case_file_notes: Optional[str] = None


@router.post("/tiered-fee/calculate")
def calculate_fee_endpoint(payload: TieredFeeCalculateRequest):
    """Computes standard 20% vs escalated 30%–35% fee breakdown."""
    return calculate_tiered_fee(
        recovery_amount=payload.recovery_amount,
        is_escalated=payload.is_escalated,
        escalation_rate=payload.escalation_rate,
        standard_rate=payload.standard_rate,
    )


@router.post("/{claim_id}/legal-escalation", response_model=LegalEscalationResponse)
def escalate_claim_endpoint(
    claim_id: str,
    payload: EscalateClaimRequest,
    db: Session = Depends(get_db),
):
    """
    Role-gated escalation of a claim to legal counsel tier (30%–35%).
    Requires Senior Approver, Finance, or Admin role authorization.
    """
    rec = escalate_claim_to_legal(
        db=db,
        claim_id=claim_id,
        user_id=payload.user_id,
        escalation_tier_rate=payload.escalation_tier_rate,
        escalation_reason=payload.escalation_reason,
        assigned_counsel_name=payload.assigned_counsel_name,
        counsel_firm=payload.counsel_firm,
    )
    return LegalEscalationResponse(
        id=rec.id,
        claim_id=rec.claim_id,
        organization_id=rec.organization_id,
        is_escalated=rec.is_escalated,
        escalation_tier_rate=rec.escalation_tier_rate,
        escalated_by_user_id=rec.escalated_by_user_id,
        escalated_at=rec.escalated_at.isoformat() if rec.escalated_at else None,
        escalation_reason=rec.escalation_reason,
        current_milestone=rec.current_milestone,
        milestone_updated_at=rec.milestone_updated_at.isoformat() if rec.milestone_updated_at else None,
        assigned_counsel_name=rec.assigned_counsel_name,
        counsel_firm=rec.counsel_firm,
        case_file_notes=rec.case_file_notes,
    )


@router.get("/{claim_id}/legal-escalation", response_model=Optional[LegalEscalationResponse])
def get_escalation_endpoint(
    claim_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves legal escalation status and current milestone."""
    rec = get_legal_escalation_record(db, claim_id=claim_id)
    if not rec:
        return None
    return LegalEscalationResponse(
        id=rec.id,
        claim_id=rec.claim_id,
        organization_id=rec.organization_id,
        is_escalated=rec.is_escalated,
        escalation_tier_rate=rec.escalation_tier_rate,
        escalated_by_user_id=rec.escalated_by_user_id,
        escalated_at=rec.escalated_at.isoformat() if rec.escalated_at else None,
        escalation_reason=rec.escalation_reason,
        current_milestone=rec.current_milestone,
        milestone_updated_at=rec.milestone_updated_at.isoformat() if rec.milestone_updated_at else None,
        assigned_counsel_name=rec.assigned_counsel_name,
        counsel_firm=rec.counsel_firm,
        case_file_notes=rec.case_file_notes,
    )


@router.post("/{claim_id}/milestones", response_model=LegalEscalationResponse)
def update_milestone_endpoint(
    claim_id: str,
    payload: MilestoneUpdateRequest,
    db: Session = Depends(get_db),
):
    """Updates manual litigation milestone (e.g. DEMAND_LETTER_SENT, REFERRED_TO_COUNSEL, LAWSUIT_FILED)."""
    rec = update_litigation_milestone(
        db=db,
        claim_id=claim_id,
        milestone=payload.milestone,
        notes=payload.notes,
    )
    return LegalEscalationResponse(
        id=rec.id,
        claim_id=rec.claim_id,
        organization_id=rec.organization_id,
        is_escalated=rec.is_escalated,
        escalation_tier_rate=rec.escalation_tier_rate,
        escalated_by_user_id=rec.escalated_by_user_id,
        escalated_at=rec.escalated_at.isoformat() if rec.escalated_at else None,
        escalation_reason=rec.escalation_reason,
        current_milestone=rec.current_milestone,
        milestone_updated_at=rec.milestone_updated_at.isoformat() if rec.milestone_updated_at else None,
        assigned_counsel_name=rec.assigned_counsel_name,
        counsel_firm=rec.counsel_firm,
        case_file_notes=rec.case_file_notes,
    )


@router.get("/{claim_id}/case-file-dossier")
def get_case_file_dossier_endpoint(
    claim_id: str,
    db: Session = Depends(get_db),
):
    """
    Compiles an organized factual Case-File Dossier for human legal counsel.
    Packages Table of Contents, SHA-256 Hashes, Chronology, and Carmack statutory deadlines.
    Zero auto-generated judicial arguments.
    """
    return assemble_case_file_dossier(db, claim_id=claim_id)

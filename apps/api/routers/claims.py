from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from db.session import get_db
from app.models.domain_models import Claim
from services.submission_service import submission_service, SubmissionBlockedException

router = APIRouter(prefix="/api/claims", tags=["claims"])

class ApproveClaimRequest(BaseModel):
    user_id: str = "usr-1"
    notes: Optional[str] = "Approved by Claims Manager"

class ClaimResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    shipment_id: Optional[str] = None
    claim_type: str
    status: str
    claimed_amount: float
    is_approved_by_human: bool
    approved_by_user_id: Optional[str] = None
    submission_reference: Optional[str] = None

@router.get("", status_code=status.HTTP_200_OK)
def list_claims(
    status_filter: Optional[str] = None,
    claim_type: Optional[str] = None,
    search_query: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Lists claims for claims manager dashboard with status, claim_type, and search filtering."""
    query = db.query(Claim)
    if status_filter and status_filter.upper() != "ALL":
        query = query.filter(Claim.status == status_filter.upper())
    if claim_type and claim_type.upper() != "ALL":
        query = query.filter(Claim.claim_type == claim_type)
    claims = query.all()
    
    res = []
    for c in claims:
        if search_query:
            q_lower = search_query.lower()
            if q_lower not in c.id.lower() and q_lower not in (c.claim_type or "").lower():
                continue
        res.append({
            "id": c.id,
            "claim_number": c.id.upper(),
            "claim_type": c.claim_type,
            "status": c.status,
            "claimed_amount": c.claimed_amount,
            "is_approved_by_human": c.is_approved_by_human,
            "approved_by_user_id": c.approved_by_user_id,
            "created_at": str(c.created_at)
        })
    return res

@router.post("/{claim_id}/approve", status_code=status.HTTP_200_OK)
def approve_claim(
    claim_id: str,
    req: ApproveClaimRequest,
    db: Session = Depends(get_db)
):
    """Records human operator approval sign-off and releases submission lock."""
    try:
        claim = submission_service.approve_claim(
            db=db,
            claim_id=claim_id,
            user_id=req.user_id,
            notes=req.notes or "Approved by Claims Manager"
        )
        return {
            "id": claim.id,
            "status": claim.status,
            "is_approved_by_human": claim.is_approved_by_human,
            "approved_by_user_id": claim.approved_by_user_id,
            "claimed_amount": claim.claimed_amount
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "not_found", "message": str(exc)}
        )

@router.post("/{claim_id}/submit", status_code=status.HTTP_200_OK)
def submit_claim(claim_id: str, db: Session = Depends(get_db)):
    """
    Submits claim package to carrier. Enforces 403 Forbidden guard if claim is unapproved.
    """
    try:
        claim = submission_service.submit_claim(db=db, claim_id=claim_id)
        return {
            "id": claim.id,
            "status": claim.status,
            "is_approved_by_human": claim.is_approved_by_human,
            "submission_reference": f"CARRIER-SUB-{claim.id.upper()}",
            "submitted_at": str(claim.submitted_at)
        }
    except SubmissionBlockedException as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "submission_blocked",
                "message": exc.message,
                "details": exc.details
            }
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "not_found", "message": str(exc)}
        )

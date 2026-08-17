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

@router.get("/{claim_id}/sla", status_code=status.HTTP_200_OK)
def get_claim_sla(claim_id: str, db: Session = Depends(get_db)):
    """Returns statutory 30-day and 120-day SLA status (49 CFR § 370.9) for a claim."""
    from app.services.sla_service import check_claim_sla_status
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    return check_claim_sla_status(claim)

@router.post("/{claim_id}/followups/generate", status_code=status.HTTP_200_OK)
def generate_followup(claim_id: str, trigger_type: str = "ACKNOWLEDGMENT_OVERDUE", db: Session = Depends(get_db)):
    """Generates citation-grounded follow-up draft (49 CFR § 370.9)."""
    from app.services.followup_service import generate_followup_draft
    comm = generate_followup_draft(db, claim_id=claim_id, trigger_type=trigger_type)
    return {
        "id": comm.id,
        "claim_id": comm.claim_id,
        "subject": comm.subject,
        "body": comm.body,
        "draft_status": comm.draft_status
    }

class DispatchFollowupRequest(BaseModel):
    user_id: str = "usr-1"
    is_approved: bool = True

@router.post("/{claim_id}/followups/{comm_id}/dispatch", status_code=status.HTTP_200_OK)
def dispatch_followup(claim_id: str, comm_id: str, req: DispatchFollowupRequest, db: Session = Depends(get_db)):
    """Enforces human sign-off guard (403 Forbidden if unapproved) and dispatches follow-up."""
    from app.services.followup_service import approve_and_dispatch_followup
    comm = approve_and_dispatch_followup(db, communication_id=comm_id, user_id=req.user_id, is_approved=req.is_approved)
    return {
        "id": comm.id,
        "draft_status": comm.draft_status,
        "approved_by": comm.approved_by,
        "sent_at": str(comm.sent_at)
    }

class CarrierResponseProcessRequest(BaseModel):
    document_id: str
    decision_type: str
    offer_amount: float = 0.0
    carrier_claim_reference: Optional[str] = None
    denial_reasons: Optional[List[str]] = None

@router.post("/{claim_id}/carrier-response/process", status_code=status.HTTP_200_OK)
def process_carrier_response_endpoint(claim_id: str, req: CarrierResponseProcessRequest, db: Session = Depends(get_db)):
    """Processes inbound carrier response document and calculates settlement discrepancy."""
    from app.services.carrier_response_service import process_carrier_response
    resp = process_carrier_response(
        db=db,
        claim_id=claim_id,
        document_id=req.document_id,
        decision_type=req.decision_type,
        offer_amount=req.offer_amount,
        carrier_claim_reference=req.carrier_claim_reference,
        denial_reasons=req.denial_reasons
    )
    return {
        "id": resp.id,
        "claim_id": resp.claim_id,
        "decision_type": resp.decision_type,
        "offer_amount": resp.offer_amount,
        "disputed_amount": resp.disputed_amount,
        "carrier_claim_reference": resp.carrier_claim_reference
    }

@router.get("/{claim_id}/lawsuit-deadline", status_code=status.HTTP_200_OK)
def get_carmack_lawsuit_deadline_endpoint(claim_id: str, db: Session = Depends(get_db)):
    """Returns statutory Carmack 2-year + 1-day lawsuit clock (49 U.S.C. § 14706)."""
    from app.services.carmack_lawsuit_service import calculate_carmack_lawsuit_deadline
    from datetime import datetime, timezone
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    
    denial_date = claim.closed_at or datetime.now(timezone.utc)
    return calculate_carmack_lawsuit_deadline(denial_date)

class GenerateRebuttalRequest(BaseModel):
    denial_pretext: str = "improper_packaging"

@router.post("/{claim_id}/rebuttals/generate", status_code=status.HTTP_200_OK)
def generate_rebuttal_endpoint(claim_id: str, req: GenerateRebuttalRequest, db: Session = Depends(get_db)):
    """Generates evidence-backed rebuttal demand packet targeting carrier denial pretexts."""
    from app.services.rebuttal_service import generate_rebuttal_package
    return generate_rebuttal_package(db, claim_id=claim_id, denial_pretext=req.denial_pretext)

class RecordRecoveryRequest(BaseModel):
    amount: float
    user_id: str = "usr-1"
    payment_reference: Optional[str] = None
    payer: Optional[str] = None
    evidence_document_id: Optional[str] = None

@router.post("/{claim_id}/recovery/record", status_code=status.HTTP_200_OK)
def record_recovery_endpoint(claim_id: str, req: RecordRecoveryRequest, db: Session = Depends(get_db)):
    """Records immutable recovery event, calculates 20% contingency fee, and issues billing invoice."""
    from app.services.recovery_ledger_service import record_recovery_event_and_issue_invoice
    res = record_recovery_event_and_issue_invoice(
        db=db,
        claim_id=claim_id,
        amount=req.amount,
        user_id=req.user_id,
        payment_reference=req.payment_reference,
        payer=req.payer,
        evidence_document_id=req.evidence_document_id
    )
    return {
        "recovery_event_id": res["recovery_event"].id,
        "recovered_amount": res["recovery_event"].amount,
        "fee_amount": res["fee_event"].fee_amount,
        "invoice_number": res["invoice"].invoice_number,
        "invoice_total": res["invoice"].total,
        "due_date": str(res["invoice"].due_date)
    }

@router.get("/{claim_id}/ledger", status_code=status.HTTP_200_OK)
def get_claim_ledger_endpoint(claim_id: str, db: Session = Depends(get_db)):
    """Returns immutable recovery events, fee events, and invoices for a claim."""
    from app.models.domain_models import RecoveryEvent, FeeEvent
    recoveries = db.query(RecoveryEvent).filter(RecoveryEvent.claim_id == claim_id).all()
    fees = db.query(FeeEvent).filter(FeeEvent.claim_id == claim_id).all()
    
    return {
        "claim_id": claim_id,
        "recoveries": [{"id": r.id, "amount": r.amount, "payer": r.payer, "received_at": str(r.received_at)} for r in recoveries],
        "fee_events": [{"id": f.id, "fee_amount": f.fee_amount, "contingency_rate": f.contingency_rate, "invoice_id": f.invoice_id} for f in fees]
    }





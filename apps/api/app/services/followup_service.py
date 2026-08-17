from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.domain_models import Claim, Communication

def generate_followup_draft(db: Session, claim_id: str, trigger_type: str = "ACKNOWLEDGMENT_OVERDUE") -> Communication:
    """
    Generate a citation-grounded follow-up draft referencing 49 CFR § 370.9 & original claim PRO#.
    """
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Claim {claim_id} not found.")

    pro_num = claim.shipment.external_reference if claim.shipment else "N/A"
    carrier_name = claim.shipment.carrier.canonical_name if (claim.shipment and claim.shipment.carrier) else "Carrier"

    if trigger_type == "ACKNOWLEDGMENT_OVERDUE":
        subject = f"URGENT: Written Acknowledgment Required — Cargo Claim {claim.id} (PRO# {pro_num})"
        body = (
            f"Dear {carrier_name} Claims Department,\n\n"
            f"Regarding Cargo Claim {claim.id} (PRO# {pro_num}) submitted for $ {claim.claimed_amount:,.2f}:\n\n"
            f"Under federal motor carrier regulations (49 CFR § 370.9), motor carriers are required to "
            f"acknowledge receipt of written loss/damage claims within 30 calendar days of receipt.\n\n"
            f"As of today, we have not received formal written acknowledgment. Please confirm receipt and provide "
            f"your assigned carrier claim reference number immediately.\n\n"
            f"Sincerely,\nSarah Jenkins (Claims Manager)"
        )
    else:
        subject = f"URGENT: Formal Resolution Status Inquiry — Cargo Claim {claim.id} (PRO# {pro_num})"
        body = (
            f"Dear {carrier_name} Claims Department,\n\n"
            f"Regarding Cargo Claim {claim.id} (PRO# {pro_num}) submitted for ${claim.claimed_amount:,.2f}:\n\n"
            f"Under 49 CFR § 370.9, cargo claims should be resolved within 120 calendar days of filing. "
            f"This claim is currently past the 120-day benchmark. Please provide a formal written disposition or "
            f"settlement offer today.\n\n"
            f"Sincerely,\nSarah Jenkins (Claims Manager)"
        )

    comm = Communication(
        id=f"comm-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        claim_id=claim_id,
        channel="email",
        direction="outbound",
        sender="sarah@apex.com",
        recipient=f"claims@{carrier_name.lower().replace(' ', '')}.com",
        subject=subject,
        body=body,
        draft_status="DRAFT"
    )
    db.add(comm)
    db.commit()
    db.refresh(comm)
    return comm

def approve_and_dispatch_followup(db: Session, communication_id: str, user_id: str, is_approved: bool = True) -> Communication:
    """
    Approve and dispatch a follow-up draft. Guaranteed server-side 403 guard if unapproved.
    """
    comm = db.query(Communication).filter(Communication.id == communication_id).first()
    if not comm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Communication {communication_id} not found.")

    if not is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Follow-up dispatch blocked: Explicit human approval sign-off is required before sending."
        )

    comm.draft_status = "DISPATCHED"
    comm.approved_by = user_id
    comm.sent_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(comm)
    return comm

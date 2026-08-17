from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.domain_models import Claim, CarrierResponse, AuditEvent

def calculate_settlement_discrepancy(claimed_amount: float, offer_amount: float) -> Dict[str, Any]:
    """
    Deterministically calculate settlement discrepancy and recovery ratio in plain Python.
    """
    claimed = round(float(claimed_amount), 2)
    offer = round(float(offer_amount), 2)
    disputed = max(0.0, round(claimed - offer, 2))
    ratio = round(offer / claimed, 4) if claimed > 0 else 0.0

    return {
        "claimed_amount": claimed,
        "offer_amount": offer,
        "disputed_amount": disputed,
        "recovery_ratio": ratio
    }

def process_carrier_response(
    db: Session,
    claim_id: str,
    document_id: str,
    decision_type: str,
    offer_amount: float = 0.0,
    carrier_claim_reference: Optional[str] = None,
    denial_reasons: Optional[List[str]] = None
) -> CarrierResponse:
    """
    Process inbound carrier response letter into CarrierResponse table and log audit diff.
    """
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Claim {claim_id} not found.")

    discrepancy = calculate_settlement_discrepancy(claim.claimed_amount, offer_amount)

    response_record = CarrierResponse(
        id=f"resp-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        claim_id=claim_id,
        document_id=document_id,
        decision_type=decision_type,
        carrier_claim_reference=carrier_claim_reference,
        offer_amount=discrepancy["offer_amount"],
        disputed_amount=discrepancy["disputed_amount"],
        denial_reasons_json={"reasons": denial_reasons or []}
    )
    db.add(response_record)

    # Update claim status based on decision
    if decision_type == "ACCEPTANCE":
        claim.status = "RECOVERED"
        claim.approved_claim_amount = discrepancy["offer_amount"]
    elif decision_type == "PARTIAL_SETTLEMENT":
        claim.status = "UNDER_REVIEW"
        claim.approved_claim_amount = discrepancy["offer_amount"]
    elif decision_type == "DENIAL":
        claim.status = "REJECTED"

    # Log audit event
    audit = AuditEvent(
        id=f"aud-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        organization_id=claim.organization_id,
        actor_type="AI",
        actor_id="CarrierResponseParser",
        entity_type="CarrierResponse",
        entity_id=response_record.id,
        action="CARRIER_RESPONSE_PROCESSED",
        before_json={"claimed_amount": claim.claimed_amount},
        after_json=discrepancy,
        reason=f"Carrier decision: {decision_type}"
    )
    db.add(audit)

    db.commit()
    db.refresh(response_record)
    return response_record

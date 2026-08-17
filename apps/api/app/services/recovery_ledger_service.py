from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.domain_models import Claim, Organization, RecoveryEvent, FeeEvent, Invoice, AuditEvent

DEFAULT_CONTINGENCY_RATE = 0.20

def calculate_contingency_fee(eligible_amount: float, rate: float = DEFAULT_CONTINGENCY_RATE) -> Dict[str, Any]:
    """
    Deterministically calculate Marajet 20% contingency fee ($0 fee on $0 recovered).
    """
    eligible = round(float(eligible_amount), 2)
    effective_rate = round(float(rate), 4)
    fee = round(eligible * effective_rate, 2) if eligible > 0.0 else 0.0

    return {
        "eligible_amount": eligible,
        "contingency_rate": effective_rate,
        "fee_amount": fee
    }

def record_recovery_event_and_issue_invoice(
    db: Session,
    claim_id: str,
    amount: float,
    user_id: str = "usr-1",
    payment_reference: Optional[str] = None,
    payer: Optional[str] = None,
    evidence_document_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Record immutable RecoveryEvent, create FeeEvent, auto-generate Invoice, and update Claim status to RECOVERED.
    """
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Claim {claim_id} not found.")

    org = db.query(Organization).filter(Organization.id == claim.organization_id).first()
    rate = org.contingency_rate if org and org.contingency_rate else DEFAULT_CONTINGENCY_RATE

    fee_info = calculate_contingency_fee(amount, rate)

    # 1. Create immutable RecoveryEvent
    rec_event = RecoveryEvent(
        id=f"rec-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        claim_id=claim_id,
        amount=fee_info["eligible_amount"],
        currency="USD",
        payment_reference=payment_reference,
        payer=payer,
        evidence_document_id=evidence_document_id,
        status="recorded",
        created_by=user_id
    )
    db.add(rec_event)
    db.flush()

    # 2. Create FeeEvent
    fee_event = FeeEvent(
        id=f"fee-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        claim_id=claim_id,
        recovery_event_id=rec_event.id,
        eligible_amount=fee_info["eligible_amount"],
        contingency_rate=fee_info["contingency_rate"],
        fee_amount=fee_info["fee_amount"],
        currency="USD",
        status="billed"
    )
    db.add(fee_event)

    # 3. Create Invoice
    now_utc = datetime.now(timezone.utc)
    due_date = now_utc + timedelta(days=14)
    invoice = Invoice(
        id=f"inv-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        organization_id=claim.organization_id,
        invoice_number=f"INV-{now_utc.strftime('%Y%m%d')}-{rec_event.id[-4:]}",
        status="issued",
        issue_date=now_utc,
        due_date=due_date,
        currency="USD",
        subtotal=fee_info["fee_amount"],
        tax=0.0,
        total=fee_info["fee_amount"]
    )
    db.add(invoice)

    # Link invoice to fee event
    fee_event.invoice_id = invoice.id

    # 4. Update Claim status
    claim.status = "RECOVERED"
    claim.approved_claim_amount = fee_info["eligible_amount"]

    # 5. Audit Log
    audit = AuditEvent(
        id=f"aud-rec-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        organization_id=claim.organization_id,
        actor_type="HUMAN",
        actor_id=user_id,
        entity_type="RecoveryEvent",
        entity_id=rec_event.id,
        action="RECOVERY_RECORDED_FEE_INVOICED",
        before_json={"claim_status": "SUBMITTED"},
        after_json={
            "recovered_amount": fee_info["eligible_amount"],
            "fee_amount": fee_info["fee_amount"],
            "invoice_number": invoice.invoice_number
        },
        reason="Carrier payout verified and fee invoice generated."
    )
    db.add(audit)

    db.commit()
    db.refresh(rec_event)
    db.refresh(fee_event)
    db.refresh(invoice)

    return {
        "recovery_event": rec_event,
        "fee_event": fee_event,
        "invoice": invoice
    }

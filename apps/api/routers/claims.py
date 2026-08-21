from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from db.session import get_db
from app.models.domain_models import Claim, Shipment, Carrier, ClaimFact, Organization, AuditEvent
from services.submission_service import submission_service, SubmissionBlockedException

router = APIRouter(prefix="/api/claims", tags=["claims"])

class IngestClaimRequest(BaseModel):
    organization_id: str = "org-apex-001"
    pro_number: str
    bol_number: Optional[str] = None
    carrier_name: str = "FXFE"
    claim_type: str = "Cargo Damage"
    claimed_amount: float = 8000.0
    currency: str = "USD"
    commodity: Optional[str] = "High-Precision Microcontrollers"
    shipper_name: Optional[str] = "TechComponents Corp (Los Angeles, CA)"
    consignee_name: Optional[str] = "Metro Logistics Distribution (Chicago, IL)"
    origin: Optional[str] = "Los Angeles, CA"
    destination: Optional[str] = "Chicago, IL"
    delivery_date: Optional[str] = "2026-08-20"
    pickup_date: Optional[str] = "2026-08-15"
    facts: Optional[List[Dict[str, Any]]] = None

@router.post("/ingest", status_code=status.HTTP_201_CREATED)
def ingest_claim_endpoint(req: IngestClaimRequest, db: Session = Depends(get_db)):
    """Ingests a new claim, shipment, and facts directly into Cloud Supabase PostgreSQL database."""
    import uuid
    from datetime import datetime, timezone, timedelta
    from dateutil.relativedelta import relativedelta

    # 1. Resolve Organization
    org = db.query(Organization).filter(Organization.id == req.organization_id).first()
    if not org:
        org = db.query(Organization).first()
        if not org:
            org = Organization(id="org-apex-001", name="Apex Freight Brokers", type="broker")
            db.add(org)
            db.flush()
    org_id = org.id

    # 2. Resolve Carrier
    carrier = db.query(Carrier).filter(Carrier.canonical_name == req.carrier_name).first()
    if not carrier:
        carrier = Carrier(
            id=f"car-{uuid.uuid4().hex[:8]}",
            canonical_name=req.carrier_name,
            active=True
        )
        db.add(carrier)
        db.flush()

    # 3. Create Shipment
    delivery_dt = None
    if req.delivery_date:
        try:
            delivery_dt = datetime.fromisoformat(req.delivery_date)
        except Exception:
            delivery_dt = datetime(2026, 8, 20, 14, 30, tzinfo=timezone.utc)
    if delivery_dt and delivery_dt.tzinfo is None:
        delivery_dt = delivery_dt.replace(tzinfo=timezone.utc)

    bol_num = req.bol_number or f"BOL-{req.pro_number.replace('PRO-', '')}"
    shipment_id = f"shp-{uuid.uuid4().hex[:12]}"
    shipment = Shipment(
        id=shipment_id,
        organization_id=org_id,
        external_reference=f"REF-{req.pro_number}",
        bol_number=bol_num,
        carrier_id=carrier.id,
        shipper_name=req.shipper_name,
        consignee_name=req.consignee_name,
        origin=req.origin,
        destination=req.destination,
        delivery_at=delivery_dt,
        declared_value=req.claimed_amount,
        commodity=req.commodity
    )
    db.add(shipment)
    db.flush()

    # 4. Compute Carmack Deadlines
    ref_date = delivery_dt or datetime.now(timezone.utc)
    carmack_deadline = ref_date + relativedelta(months=9)
    concealed_deadline = ref_date + timedelta(days=5)
    lawsuit_deadline = ref_date + relativedelta(years=2, days=1)

    # 5. Create Claim
    claim_id = f"clm-{uuid.uuid4().hex[:12]}"
    claim = Claim(
        id=claim_id,
        organization_id=org_id,
        shipment_id=shipment.id,
        claim_type=req.claim_type,
        status="HUMAN_REVIEW",
        claimed_amount=req.claimed_amount,
        currency=req.currency,
        deadline_at=carmack_deadline,
        concealed_deadline_at=concealed_deadline,
        lawsuit_deadline_at=lawsuit_deadline,
        human_threshold_triggered=req.claimed_amount >= 5000.0,
        is_approved_by_human=False
    )
    db.add(claim)
    db.flush()

    # 6. Save Facts
    if req.facts:
        for idx, f in enumerate(req.facts):
            fact_id = f"f-{claim.id}-{idx}"
            fact = ClaimFact(
                id=fact_id,
                claim_id=claim.id,
                field_name=f.get("fieldName") or f.get("field_name") or f"fact_{idx}",
                display_name=f.get("displayName") or f.get("display_name") or f.get("fieldName") or f"Fact {idx+1}",
                value_json=str(f.get("valueJson") or f.get("value_json") or f.get("value")),
                confidence=float(f.get("confidence", 0.98)),
                verification_status="VERIFIED"
            )
            db.add(fact)

    # 7. Audit Event
    audit = AuditEvent(
        id=f"aud-{uuid.uuid4().hex[:12]}",
        organization_id=org_id,
        claim_id=claim.id,
        actor_type="AI",
        actor_id="Algolyra-Ingestion-Engine-v4",
        action="CLAIM_INGESTED_TO_SUPABASE",
        entity_type="Claim",
        entity_id=claim.id
    )
    db.add(audit)

    db.commit()
    db.refresh(claim)
    db.refresh(shipment)

    return {
        "status": "success",
        "claim_id": claim.id,
        "shipment_id": shipment.id,
        "organization_id": org_id,
        "carrier_name": carrier.canonical_name,
        "pro_number": req.pro_number,
        "bol_number": shipment.bol_number,
        "delivery_at": str(shipment.delivery_at),
        "deadline_at": str(claim.deadline_at),
        "concealed_deadline_at": str(claim.concealed_deadline_at),
        "lawsuit_deadline_at": str(claim.lawsuit_deadline_at),
        "claimed_amount": claim.claimed_amount
    }


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

class BackdateSubmissionRequest(BaseModel):
    days_ago: int = 31

@router.post("/{claim_id}/backdate-submission", status_code=status.HTTP_200_OK)
def backdate_submission_endpoint(claim_id: str, req: BackdateSubmissionRequest, db: Session = Depends(get_db)):
    """Backdates claim's submitted_at timestamp by N days to simulate SLA overdue status under 49 CFR § 370.9."""
    from datetime import datetime, timedelta, timezone
    from app.services.sla_service import check_claim_sla_status
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    
    claim.submitted_at = datetime.now(timezone.utc) - timedelta(days=req.days_ago)
    claim.status = "SUBMITTED"
    db.commit()
    db.refresh(claim)
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





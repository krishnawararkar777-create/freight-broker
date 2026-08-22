import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.domain_models import Claim, Shipment, Carrier, CarrierContractClause

CARMACK_DEFAULT_FILING_DAYS = 270       # 9 months statutory floor (49 U.S.C. § 14706(e)(1))
CARMACK_DEFAULT_LAWSUIT_DAYS = 731      # 2 years + 1 day statutory floor
NMFC_DEFAULT_CONCEALED_DAYS = 5         # 5 calendar days standard concealed damage notice

class GoverningDeadlineReport(BaseModel):
    claim_id: str
    carrier_id: str
    carrier_name: str
    filing_governing_source: str = Field(..., description="BROKER_CARRIER_MSA | CARRIER_RULES_TARIFF | CARMACK_STATUTORY_DEFAULT")
    governing_contract_reference: Optional[str] = None
    filing_window_days: int
    governing_filing_deadline: Optional[datetime] = None
    days_remaining: int
    urgency_status: str = Field("ON_SCHEDULE", description="ON_SCHEDULE | URGENT_DEADLINE_APPROACHING | TIME_BARRED_BY_LIMITATION")
    concealed_notice_days: int
    concealed_notice_deadline: Optional[datetime] = None
    lawsuit_window_days: int
    governing_lawsuit_deadline: Optional[datetime] = None
    released_rate_cap_per_lb: Optional[float] = None
    max_liability_cap: Optional[float] = None
    clause_text_excerpt: Optional[str] = None
    all_active_clauses: List[Dict[str, Any]] = []


def compute_governing_deadlines(
    db: Session,
    claim_id: str,
    current_time: Optional[datetime] = None,
) -> GoverningDeadlineReport:
    """
    Deterministically computes the strictest governing claim and lawsuit deadlines across
    Broker-Carrier MSAs, Carrier Tariffs, and Carmack statutory defaults.
    """
    now = current_time or datetime.now(timezone.utc)

    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Claim {claim_id} not found.")

    shipment = db.query(Shipment).filter(Shipment.id == claim.shipment_id).first()
    carrier = db.query(Carrier).filter(Carrier.id == (shipment.carrier_id if shipment else None)).first() if shipment else None
    carrier_id = carrier.id if carrier else "unknown"
    carrier_name = carrier.canonical_name if carrier else "Unassigned Carrier"

    # Base reference dates
    raw_date = (shipment.delivery_at if shipment and shipment.delivery_at else None) or (shipment.pickup_at if shipment else None) or claim.created_at or now
    if raw_date and raw_date.tzinfo is None:
        delivery_date = raw_date.replace(tzinfo=timezone.utc)
    else:
        delivery_date = raw_date or now

    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    # Fetch active contract clauses for carrier
    clauses = db.query(CarrierContractClause).filter(
        CarrierContractClause.carrier_id == carrier_id
    ).all()

    # Determine governing rules by hierarchy
    # 1. Check if any Broker-Carrier MSA with supersedes_carrier_tariff=True exists
    msa_clauses = [c for c in clauses if c.contract_type == "BROKER_CARRIER_MSA"]
    tariff_clauses = [c for c in clauses if c.contract_type == "CARRIER_RULES_TARIFF"]

    governing_clause: Optional[CarrierContractClause] = None
    filing_source = "CARMACK_STATUTORY_DEFAULT"
    filing_window = CARMACK_DEFAULT_FILING_DAYS
    concealed_window = NMFC_DEFAULT_CONCEALED_DAYS
    lawsuit_window = CARMACK_DEFAULT_LAWSUIT_DAYS
    rate_cap: Optional[float] = None
    liability_cap: Optional[float] = None

    if msa_clauses:
        # Broker MSA takes precedence
        msa = msa_clauses[0]
        governing_clause = msa
        filing_source = "BROKER_CARRIER_MSA"
        if msa.filing_window_days:
            filing_window = msa.filing_window_days
        if msa.concealed_notice_days:
            concealed_window = msa.concealed_notice_days
        if msa.lawsuit_window_days:
            lawsuit_window = msa.lawsuit_window_days
        rate_cap = msa.released_rate_cap_per_lb
        liability_cap = msa.max_liability_cap
    elif tariff_clauses:
        tariff = tariff_clauses[0]
        governing_clause = tariff
        filing_source = "CARRIER_RULES_TARIFF"
        if tariff.filing_window_days:
            filing_window = min(CARMACK_DEFAULT_FILING_DAYS, tariff.filing_window_days)
        if tariff.concealed_notice_days:
            concealed_window = tariff.concealed_notice_days
        if tariff.lawsuit_window_days:
            lawsuit_window = min(CARMACK_DEFAULT_LAWSUIT_DAYS, tariff.lawsuit_window_days)
        rate_cap = tariff.released_rate_cap_per_lb
        liability_cap = tariff.max_liability_cap

    # Calculate exact timestamp deadlines
    filing_deadline = delivery_date + timedelta(days=filing_window)
    concealed_deadline = delivery_date + timedelta(days=concealed_window)
    lawsuit_deadline = delivery_date + timedelta(days=lawsuit_window)

    # Calculate days remaining
    diff = (filing_deadline - now).total_seconds()
    days_remaining = int(diff // 86400)

    # Determine urgency status
    if days_remaining < 0:
        urgency = "TIME_BARRED_BY_LIMITATION"
    elif days_remaining <= 14:
        urgency = "URGENT_DEADLINE_APPROACHING"
    else:
        urgency = "ON_SCHEDULE"

    clause_summaries = []
    for c in clauses:
        clause_summaries.append({
            "id": c.id,
            "contract_type": c.contract_type,
            "contract_reference": c.contract_reference,
            "filing_window_days": c.filing_window_days,
            "concealed_notice_days": c.concealed_notice_days,
            "lawsuit_window_days": c.lawsuit_window_days,
            "supersedes_carrier_tariff": c.supersedes_carrier_tariff,
            "clause_text_excerpt": c.clause_text_excerpt,
        })

    return GoverningDeadlineReport(
        claim_id=claim.id,
        carrier_id=carrier_id,
        carrier_name=carrier_name,
        filing_governing_source=filing_source,
        governing_contract_reference=governing_clause.contract_reference if governing_clause else "49 U.S.C. § 14706(e)(1)",
        filing_window_days=filing_window,
        governing_filing_deadline=filing_deadline,
        days_remaining=days_remaining,
        urgency_status=urgency,
        concealed_notice_days=concealed_window,
        concealed_notice_deadline=concealed_deadline,
        lawsuit_window_days=lawsuit_window,
        governing_lawsuit_deadline=lawsuit_deadline,
        released_rate_cap_per_lb=rate_cap,
        max_liability_cap=liability_cap,
        clause_text_excerpt=governing_clause.clause_text_excerpt if governing_clause else None,
        all_active_clauses=clause_summaries,
    )


def save_carrier_contract_clause(
    db: Session,
    carrier_id: str,
    organization_id: str,
    contract_type: str,
    contract_reference: str,
    filing_window_days: Optional[int] = None,
    concealed_notice_days: Optional[int] = None,
    lawsuit_window_days: Optional[int] = None,
    released_rate_cap_per_lb: Optional[float] = None,
    max_liability_cap: Optional[float] = None,
    supersedes_carrier_tariff: bool = True,
    clause_text_excerpt: Optional[str] = None,
) -> CarrierContractClause:
    """Creates or updates a custom contract limitation clause for a carrier."""
    clause = CarrierContractClause(
        id=f"clause-{uuid.uuid4().hex[:12]}",
        carrier_id=carrier_id,
        organization_id=organization_id,
        contract_type=contract_type,
        contract_reference=contract_reference,
        effective_date=datetime.now(timezone.utc),
        filing_window_days=filing_window_days,
        concealed_notice_days=concealed_notice_days,
        lawsuit_window_days=lawsuit_window_days,
        released_rate_cap_per_lb=released_rate_cap_per_lb,
        max_liability_cap=max_liability_cap,
        supersedes_carrier_tariff=supersedes_carrier_tariff,
        clause_text_excerpt=clause_text_excerpt,
    )
    db.add(clause)
    db.commit()
    db.refresh(clause)
    return clause


def get_carrier_contract_clauses(db: Session, carrier_id: str) -> List[CarrierContractClause]:
    """Retrieves all contract clauses on file for a carrier."""
    return db.query(CarrierContractClause).filter(CarrierContractClause.carrier_id == carrier_id).all()

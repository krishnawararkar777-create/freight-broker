from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from db.session import get_db
from app.models.domain_models import Carrier, CarrierContractClause, Claim
from app.services.tariff_guardian_service import (
    compute_governing_deadlines,
    save_carrier_contract_clause,
    get_carrier_contract_clauses,
    GoverningDeadlineReport,
)

router = APIRouter(prefix="/api", tags=["tariff-guardian"])

class CreateContractClauseRequest(BaseModel):
    organization_id: str
    contract_type: str = Field("BROKER_CARRIER_MSA", description="BROKER_CARRIER_MSA | CARRIER_RULES_TARIFF | RATE_CON_TERMS")
    contract_reference: str
    filing_window_days: Optional[int] = None
    concealed_notice_days: Optional[int] = None
    lawsuit_window_days: Optional[int] = None
    released_rate_cap_per_lb: Optional[float] = None
    max_liability_cap: Optional[float] = None
    supersedes_carrier_tariff: bool = True
    clause_text_excerpt: Optional[str] = None

class CarrierContractClauseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    carrier_id: str
    organization_id: str
    contract_type: str
    contract_reference: str
    effective_date: Optional[str] = None
    filing_window_days: Optional[int] = None
    concealed_notice_days: Optional[int] = None
    lawsuit_window_days: Optional[int] = None
    released_rate_cap_per_lb: Optional[float] = None
    max_liability_cap: Optional[float] = None
    supersedes_carrier_tariff: bool
    clause_text_excerpt: Optional[str] = None


@router.post("/carriers/{carrier_id}/contracts", response_model=CarrierContractClauseResponse)
def add_carrier_contract_clause_endpoint(
    carrier_id: str,
    payload: CreateContractClauseRequest,
    db: Session = Depends(get_db),
):
    """Ingests/saves a custom contract clause or rules tariff addendum for a carrier."""
    carrier = db.query(Carrier).filter(Carrier.id == carrier_id).first()
    if not carrier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Carrier {carrier_id} not found.")

    clause = save_carrier_contract_clause(
        db=db,
        carrier_id=carrier_id,
        organization_id=payload.organization_id,
        contract_type=payload.contract_type,
        contract_reference=payload.contract_reference,
        filing_window_days=payload.filing_window_days,
        concealed_notice_days=payload.concealed_notice_days,
        lawsuit_window_days=payload.lawsuit_window_days,
        released_rate_cap_per_lb=payload.released_rate_cap_per_lb,
        max_liability_cap=payload.max_liability_cap,
        supersedes_carrier_tariff=payload.supersedes_carrier_tariff,
        clause_text_excerpt=payload.clause_text_excerpt,
    )
    return CarrierContractClauseResponse(
        id=clause.id,
        carrier_id=clause.carrier_id,
        organization_id=clause.organization_id,
        contract_type=clause.contract_type,
        contract_reference=clause.contract_reference,
        effective_date=clause.effective_date.isoformat() if clause.effective_date else None,
        filing_window_days=clause.filing_window_days,
        concealed_notice_days=clause.concealed_notice_days,
        lawsuit_window_days=clause.lawsuit_window_days,
        released_rate_cap_per_lb=clause.released_rate_cap_per_lb,
        max_liability_cap=clause.max_liability_cap,
        supersedes_carrier_tariff=clause.supersedes_carrier_tariff,
        clause_text_excerpt=clause.clause_text_excerpt,
    )


@router.get("/carriers/{carrier_id}/contracts", response_model=List[CarrierContractClauseResponse])
def get_carrier_contract_clauses_endpoint(
    carrier_id: str,
    db: Session = Depends(get_db),
):
    """Lists all active contracts and tariff clauses on file for a carrier."""
    clauses = get_carrier_contract_clauses(db, carrier_id=carrier_id)
    return [
        CarrierContractClauseResponse(
            id=c.id,
            carrier_id=c.carrier_id,
            organization_id=c.organization_id,
            contract_type=c.contract_type,
            contract_reference=c.contract_reference,
            effective_date=c.effective_date.isoformat() if c.effective_date else None,
            filing_window_days=c.filing_window_days,
            concealed_notice_days=c.concealed_notice_days,
            lawsuit_window_days=c.lawsuit_window_days,
            released_rate_cap_per_lb=c.released_rate_cap_per_lb,
            max_liability_cap=c.max_liability_cap,
            supersedes_carrier_tariff=c.supersedes_carrier_tariff,
            clause_text_excerpt=c.clause_text_excerpt,
        )
        for c in clauses
    ]


@router.get("/claims/{claim_id}/governing-deadlines", response_model=GoverningDeadlineReport)
def get_claim_governing_deadlines_endpoint(
    claim_id: str,
    db: Session = Depends(get_db),
):
    """
    Computes deterministic min() governing deadlines across MSA contracts,
    carrier rules tariffs, and statutory Carmack rules.
    """
    return compute_governing_deadlines(db, claim_id=claim_id)

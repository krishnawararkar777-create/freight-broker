from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from db.session import get_db
from app.models.domain_models import Claim, SalvageRecord
from app.services.salvage_service import (
    calculate_salvage_valuation,
    save_or_update_salvage_record,
    get_salvage_record,
    generate_mitigation_document,
    SalvageCalculationResult,
    COMMODITY_BASE_SALVAGE_RATES,
)

router = APIRouter(prefix="/api/claims", tags=["salvage"])

class SalvageRecordCreate(BaseModel):
    commodity_category: str
    damage_severity_score: float = Field(0.5, ge=0.0, le=1.0)
    gross_invoice_value: float = Field(..., gt=0.0)
    realized_salvage_value: Optional[float] = None
    disposition_status: str = "PENDING_INSPECTION"
    storage_location: Optional[str] = None
    evidence_document_id: Optional[str] = None
    notes: Optional[str] = None


class SalvageRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    claim_id: str
    organization_id: str
    commodity_category: str
    damage_severity_score: float
    gross_invoice_value: float
    salvage_rate: float
    estimated_salvage_value: float
    realized_salvage_value: Optional[float] = None
    net_claimed_amount: float
    disposition_status: str
    disposition_date: Optional[str] = None
    storage_location: Optional[str] = None
    evidence_document_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: str

class SalvageCalculateRequest(BaseModel):
    gross_invoice_value: float = Field(..., gt=0.0)
    commodity_category: str
    damage_severity_score: float = Field(0.5, ge=0.0, le=1.0)
    realized_salvage_value: Optional[float] = None


@router.post("/salvage/calculate", response_model=SalvageCalculationResult)
def calculate_salvage_preview(payload: SalvageCalculateRequest):
    """
    Dynamic preview endpoint for calculating salvage offsets and net claim demand.
    """
    return calculate_salvage_valuation(
        gross_invoice_value=payload.gross_invoice_value,
        commodity_category=payload.commodity_category,
        damage_severity_score=payload.damage_severity_score,
        realized_salvage_value=payload.realized_salvage_value,
    )


@router.post("/{claim_id}/salvage", response_model=SalvageRecordResponse)
def record_claim_salvage(
    claim_id: str,
    payload: SalvageRecordCreate,
    db: Session = Depends(get_db),
):
    """
    Records or updates cargo salvage valuation and disposition status,
    automatically updating the claim's net demand amount.
    """
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Claim {claim_id} not found.")

    record = save_or_update_salvage_record(
        db=db,
        claim_id=claim_id,
        organization_id=claim.organization_id,
        gross_invoice_value=payload.gross_invoice_value,
        commodity_category=payload.commodity_category,
        damage_severity_score=payload.damage_severity_score,
        realized_salvage_value=payload.realized_salvage_value,
        disposition_status=payload.disposition_status,
        storage_location=payload.storage_location,
        evidence_document_id=payload.evidence_document_id,
        notes=payload.notes,
    )
    return SalvageRecordResponse(
        id=record.id,
        claim_id=record.claim_id,
        organization_id=record.organization_id,
        commodity_category=record.commodity_category,
        damage_severity_score=record.damage_severity_score,
        gross_invoice_value=record.gross_invoice_value,
        salvage_rate=record.salvage_rate,
        estimated_salvage_value=record.estimated_salvage_value,
        realized_salvage_value=record.realized_salvage_value,
        net_claimed_amount=record.net_claimed_amount,
        disposition_status=record.disposition_status,
        disposition_date=record.disposition_date.isoformat() if record.disposition_date else None,
        storage_location=record.storage_location,
        evidence_document_id=record.evidence_document_id,
        notes=record.notes,
        created_at=record.created_at.isoformat() if record.created_at else "",
    )


@router.get("/{claim_id}/salvage", response_model=Optional[SalvageRecordResponse])
def get_claim_salvage(
    claim_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieves the active salvage record for a claim.
    """
    record = get_salvage_record(db, claim_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No salvage record found for claim {claim_id}.")

    return SalvageRecordResponse(
        id=record.id,
        claim_id=record.claim_id,
        organization_id=record.organization_id,
        commodity_category=record.commodity_category,
        damage_severity_score=record.damage_severity_score,
        gross_invoice_value=record.gross_invoice_value,
        salvage_rate=record.salvage_rate,
        estimated_salvage_value=record.estimated_salvage_value,
        realized_salvage_value=record.realized_salvage_value,
        net_claimed_amount=record.net_claimed_amount,
        disposition_status=record.disposition_status,
        disposition_date=record.disposition_date.isoformat() if record.disposition_date else None,
        storage_location=record.storage_location,
        evidence_document_id=record.evidence_document_id,
        notes=record.notes,
        created_at=record.created_at.isoformat() if record.created_at else "",
    )


@router.get("/{claim_id}/salvage/mitigation-doc")
def get_claim_mitigation_document(
    claim_id: str,
    db: Session = Depends(get_db),
):
    """
    Returns the factual mitigation proof document for the claim.
    """
    return generate_mitigation_document(db, claim_id)

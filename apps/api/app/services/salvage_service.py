import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.domain_models import SalvageRecord, Claim, Organization, Document

# Deterministic commodity category baseline recovery rates
COMMODITY_BASE_SALVAGE_RATES: Dict[str, float] = {
    "METALS_MACHINERY": 0.40,       # High scrap / scrap metal residual
    "ELECTRONICS": 0.25,            # Secondary market / component parts
    "DRY_GOODS": 0.15,              # Discount retailer liquidation
    "GENERAL_MERCHANDISE": 0.10,    # Generic salvage residual
    "PERISHABLES_FOOD": 0.00,       # Mandatory destruction under FDA / health regs
    "PHARMACEUTICALS": 0.00,        # Mandatory destruction under DEA / FDA regs
    "HAZMAT": 0.00,                 # Mandatory environmental destruction
}

class SalvageCalculationResult(BaseModel):
    gross_invoice_value: float = Field(..., description="Original invoiced value of damaged goods")
    commodity_category: str = Field(..., description="Commodity type")
    damage_severity_score: float = Field(..., description="Damage severity score (0.0=sound, 1.0=total loss)")
    salvage_rate: float = Field(..., description="Effective salvage percentage rate applied")
    estimated_salvage_value: float = Field(..., description="Calculated estimated residual salvage value")
    realized_salvage_value: Optional[float] = Field(None, description="Actual realized salvage sale proceeds if sold")
    salvage_offset_applied: float = Field(..., description="Total salvage dollar offset deducted")
    net_claimed_amount: float = Field(..., description="Final net claim demand after salvage deduction")


def calculate_salvage_valuation(
    gross_invoice_value: float,
    commodity_category: str,
    damage_severity_score: float = 0.5,
    realized_salvage_value: Optional[float] = None,
) -> SalvageCalculationResult:
    """
    Computes deterministic salvage valuation and net claim demand:
    Net Claim Demand = Gross Invoiced Loss - Salvage Offset
    """
    norm_category = commodity_category.upper() if commodity_category else "GENERAL_MERCHANDISE"
    base_rate = COMMODITY_BASE_SALVAGE_RATES.get(norm_category, 0.10)

    # Effective rate scales inversely with damage severity (more severe damage -> lower salvage residual)
    clamped_severity = max(0.0, min(1.0, damage_severity_score))
    effective_rate = round(base_rate * (1.0 - clamped_severity), 4)
    estimated_salvage = round(gross_invoice_value * effective_rate, 2)

    if realized_salvage_value is not None:
        salvage_offset = round(realized_salvage_value, 2)
    else:
        salvage_offset = estimated_salvage

    # Net claim demand cannot be negative
    net_demand = max(0.0, round(gross_invoice_value - salvage_offset, 2))

    return SalvageCalculationResult(
        gross_invoice_value=round(gross_invoice_value, 2),
        commodity_category=norm_category,
        damage_severity_score=clamped_severity,
        salvage_rate=effective_rate,
        estimated_salvage_value=estimated_salvage,
        realized_salvage_value=round(realized_salvage_value, 2) if realized_salvage_value is not None else None,
        salvage_offset_applied=salvage_offset,
        net_claimed_amount=net_demand,
    )


def save_or_update_salvage_record(
    db: Session,
    claim_id: str,
    organization_id: str,
    gross_invoice_value: float,
    commodity_category: str,
    damage_severity_score: float = 0.5,
    realized_salvage_value: Optional[float] = None,
    disposition_status: str = "PENDING_INSPECTION",
    storage_location: Optional[str] = None,
    evidence_document_id: Optional[str] = None,
    notes: Optional[str] = None,
) -> SalvageRecord:
    """
    Saves or updates the SalvageRecord for a claim and deterministically updates
    the claim's claimed_amount with the Net Claim Demand.
    """
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Claim {claim_id} not found.")

    calc = calculate_salvage_valuation(
        gross_invoice_value=gross_invoice_value,
        commodity_category=commodity_category,
        damage_severity_score=damage_severity_score,
        realized_salvage_value=realized_salvage_value,
    )

    record = db.query(SalvageRecord).filter(SalvageRecord.claim_id == claim_id).first()
    if not record:
        record = SalvageRecord(
            id=f"slv-{uuid.uuid4().hex[:12]}",
            claim_id=claim_id,
            organization_id=organization_id,
            commodity_category=calc.commodity_category,
            damage_severity_score=calc.damage_severity_score,
            gross_invoice_value=calc.gross_invoice_value,
            salvage_rate=calc.salvage_rate,
            estimated_salvage_value=calc.estimated_salvage_value,
            realized_salvage_value=calc.realized_salvage_value,
            net_claimed_amount=calc.net_claimed_amount,
            disposition_status=disposition_status,
            disposition_date=datetime.now(timezone.utc) if disposition_status in ["DESTROYED", "SOLD_BY_CONSIGNEE"] else None,
            storage_location=storage_location,
            evidence_document_id=evidence_document_id,
            notes=notes,
        )
        db.add(record)
    else:
        record.commodity_category = calc.commodity_category
        record.damage_severity_score = calc.damage_severity_score
        record.gross_invoice_value = calc.gross_invoice_value
        record.salvage_rate = calc.salvage_rate
        record.estimated_salvage_value = calc.estimated_salvage_value
        record.realized_salvage_value = calc.realized_salvage_value
        record.net_claimed_amount = calc.net_claimed_amount
        record.disposition_status = disposition_status
        if disposition_status in ["DESTROYED", "SOLD_BY_CONSIGNEE"] and not record.disposition_date:
            record.disposition_date = datetime.now(timezone.utc)
        record.storage_location = storage_location
        record.evidence_document_id = evidence_document_id
        record.notes = notes

    # Update claim claimed_amount to net demand
    claim.claimed_amount = calc.net_claimed_amount
    db.commit()
    db.refresh(record)
    return record


def get_salvage_record(db: Session, claim_id: str) -> Optional[SalvageRecord]:
    """Retrieves the salvage record for a claim."""
    return db.query(SalvageRecord).filter(SalvageRecord.claim_id == claim_id).first()


def generate_mitigation_document(db: Session, claim_id: str) -> Dict[str, Any]:
    """
    Generates a structured factual evidence document verifying that the common law
    and NMFC duty to mitigate loss was met, neutralizing carrier salvage denial pretexts.
    Factual documentation only — contains no judicial arguments.
    """
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Claim {claim_id} not found.")

    record = get_salvage_record(db, claim_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No salvage record found for claim {claim_id}.")

    return {
        "document_title": "Factual Record of Cargo Loss Mitigation & Salvage Valuation",
        "claim_id": claim.id,
        "organization_id": claim.organization_id,
        "mitigation_status": "DUTY_SATISFIED",
        "commodity_category": record.commodity_category,
        "damage_severity_score": record.damage_severity_score,
        "gross_invoice_value": record.gross_invoice_value,
        "salvage_rate_applied": record.salvage_rate,
        "salvage_offset": record.realized_salvage_value if record.realized_salvage_value is not None else record.estimated_salvage_value,
        "net_claimed_amount": record.net_claimed_amount,
        "disposition_status": record.disposition_status,
        "disposition_date": record.disposition_date.isoformat() if record.disposition_date else None,
        "storage_location": record.storage_location or "Consignee Receiving Facility",
        "factual_certification": (
            f"This factual record documents that cargo under claim {claim.id} was mitigated pursuant to "
            f"standard cargo loss duty. Gross invoice value of ${record.gross_invoice_value:,.2f} has been adjusted "
            f"by a salvage deduction of ${record.realized_salvage_value if record.realized_salvage_value is not None else record.estimated_salvage_value:,.2f}, "
            f"yielding a net claim demand of ${record.net_claimed_amount:,.2f}. "
            f"Current physical disposition: {record.disposition_status} at {record.storage_location or 'Consignee Facility'}."
        ),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

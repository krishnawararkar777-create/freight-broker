from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from db.session import get_db
from app.models.domain_models import Carrier, CarrierRiskFacts, Claim, Shipment, ClaimFact, Document
from app.services.carrier_risk_service import (
    sync_or_get_carrier_risk_facts,
    detect_carrier_anomalies,
    CarrierAnomalyFlag,
)

router = APIRouter(prefix="/api", tags=["carrier-risk"])

class CarrierRiskFactsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    carrier_id: str
    dot_number: Optional[str] = None
    mc_number: Optional[str] = None
    legal_name: str
    dba_name: Optional[str] = None
    authority_status: str
    common_authority_status: Optional[str] = None
    contract_authority_status: Optional[str] = None
    bipd_insurance_on_file: float
    cargo_insurance_on_file: float
    cargo_policy_active: bool
    cargo_form_type: Optional[str] = None
    safety_rating: Optional[str] = None
    out_of_service_rate_pct: Optional[float] = None
    last_fmcsa_sync_at: Optional[str] = None


class ClaimCarrierRiskReport(BaseModel):
    claim_id: str
    carrier_id: str
    fmcsa_facts: Optional[CarrierRiskFactsResponse] = None
    anomalies: List[CarrierAnomalyFlag] = []
    has_critical_warning: bool = False
    total_anomalies_detected: int = 0


@router.get("/carriers/{carrier_id}/fmcsa-facts", response_model=CarrierRiskFactsResponse)
def get_carrier_fmcsa_facts(
    carrier_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieves factual FMCSA SAFER / Licensing & Insurance registry facts for a carrier.
    No synthetic grades or manufactured risk scores.
    """
    facts = sync_or_get_carrier_risk_facts(db, carrier_id=carrier_id)
    return CarrierRiskFactsResponse(
        id=facts.id,
        carrier_id=facts.carrier_id,
        dot_number=facts.dot_number,
        mc_number=facts.mc_number,
        legal_name=facts.legal_name,
        dba_name=facts.dba_name,
        authority_status=facts.authority_status,
        common_authority_status=facts.common_authority_status,
        contract_authority_status=facts.contract_authority_status,
        bipd_insurance_on_file=facts.bipd_insurance_on_file,
        cargo_insurance_on_file=facts.cargo_insurance_on_file,
        cargo_policy_active=facts.cargo_policy_active,
        cargo_form_type=facts.cargo_form_type,
        safety_rating=facts.safety_rating,
        out_of_service_rate_pct=facts.out_of_service_rate_pct,
        last_fmcsa_sync_at=facts.last_fmcsa_sync_at.isoformat() if facts.last_fmcsa_sync_at else None,
    )


@router.post("/carriers/{carrier_id}/fmcsa-facts/sync", response_model=CarrierRiskFactsResponse)
def sync_carrier_fmcsa_facts(
    carrier_id: str,
    db: Session = Depends(get_db),
):
    """
    Triggers live registry sync/refresh with FMCSA SAFER for a carrier.
    """
    facts = sync_or_get_carrier_risk_facts(db, carrier_id=carrier_id, force_refresh=True)
    return CarrierRiskFactsResponse(
        id=facts.id,
        carrier_id=facts.carrier_id,
        dot_number=facts.dot_number,
        mc_number=facts.mc_number,
        legal_name=facts.legal_name,
        dba_name=facts.dba_name,
        authority_status=facts.authority_status,
        common_authority_status=facts.common_authority_status,
        contract_authority_status=facts.contract_authority_status,
        bipd_insurance_on_file=facts.bipd_insurance_on_file,
        cargo_insurance_on_file=facts.cargo_insurance_on_file,
        cargo_policy_active=facts.cargo_policy_active,
        cargo_form_type=facts.cargo_form_type,
        safety_rating=facts.safety_rating,
        out_of_service_rate_pct=facts.out_of_service_rate_pct,
        last_fmcsa_sync_at=facts.last_fmcsa_sync_at.isoformat() if facts.last_fmcsa_sync_at else None,
    )


@router.get("/claims/{claim_id}/carrier-anomalies", response_model=ClaimCarrierRiskReport)
def get_claim_carrier_anomalies(
    claim_id: str,
    db: Session = Depends(get_db),
):
    """
    Compares document facts (Rate Con, BOL, POD) against FMCSA SAFER registry
    to identify double-brokering risks, MC mismatches, or cancelled insurance warnings.
    """
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Claim {claim_id} not found.")

    shipment = db.query(Shipment).filter(Shipment.id == claim.shipment_id).first()
    carrier_id = shipment.carrier_id if shipment else None

    carrier = db.query(Carrier).filter(Carrier.id == carrier_id).first() if carrier_id else None
    fmcsa_facts = sync_or_get_carrier_risk_facts(db, carrier_id=carrier.id) if carrier else None

    # Retrieve facts extracted from documents
    facts = db.query(ClaimFact).filter(ClaimFact.claim_id == claim_id).all()
    fact_dict = {f.field_name: f.value_json for f in facts}

    rate_con_carrier = carrier.canonical_name if carrier else fact_dict.get("carrier_name")
    bol_carrier = fact_dict.get("bol_carrier_name") or fact_dict.get("carrier_name")
    pod_carrier = fact_dict.get("pod_carrier_name")
    rate_con_mc = carrier.mc_number if carrier else fact_dict.get("carrier_mc_number")
    bol_mc = fact_dict.get("bol_carrier_mc")
    pod_mc = fact_dict.get("pod_carrier_mc")

    anomalies = detect_carrier_anomalies(
        rate_con_carrier=rate_con_carrier,
        bol_carrier=bol_carrier,
        pod_carrier=pod_carrier,
        rate_con_mc=rate_con_mc,
        bol_mc=bol_mc,
        pod_mc=pod_mc,
        fmcsa_facts=fmcsa_facts,
        pickup_date=shipment.pickup_at if shipment else None,
    )

    has_critical = any(a.severity == "CRITICAL" for a in anomalies)

    facts_resp = None
    if fmcsa_facts:
        facts_resp = CarrierRiskFactsResponse(
            id=fmcsa_facts.id,
            carrier_id=fmcsa_facts.carrier_id,
            dot_number=fmcsa_facts.dot_number,
            mc_number=fmcsa_facts.mc_number,
            legal_name=fmcsa_facts.legal_name,
            dba_name=fmcsa_facts.dba_name,
            authority_status=fmcsa_facts.authority_status,
            common_authority_status=fmcsa_facts.common_authority_status,
            contract_authority_status=fmcsa_facts.contract_authority_status,
            bipd_insurance_on_file=fmcsa_facts.bipd_insurance_on_file,
            cargo_insurance_on_file=fmcsa_facts.cargo_insurance_on_file,
            cargo_policy_active=fmcsa_facts.cargo_policy_active,
            cargo_form_type=fmcsa_facts.cargo_form_type,
            safety_rating=fmcsa_facts.safety_rating,
            out_of_service_rate_pct=fmcsa_facts.out_of_service_rate_pct,
            last_fmcsa_sync_at=fmcsa_facts.last_fmcsa_sync_at.isoformat() if fmcsa_facts.last_fmcsa_sync_at else None,
        )

    return ClaimCarrierRiskReport(
        claim_id=claim.id,
        carrier_id=carrier.id if carrier else "unknown",
        fmcsa_facts=facts_resp,
        anomalies=anomalies,
        has_critical_warning=has_critical,
        total_anomalies_detected=len(anomalies),
    )

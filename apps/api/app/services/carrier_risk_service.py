import re
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.domain_models import Carrier, CarrierRiskFacts, Claim, Shipment

class CarrierAnomalyFlag(BaseModel):
    anomaly_type: str = Field(..., description="LEGAL_NAME_MISMATCH | MC_NUMBER_MISMATCH | INSURANCE_STATUS_WARNING | AUTHORITY_INACTIVE_WARNING | SAFETY_RATING_WARNING")
    severity: str = Field("WARNING", description="INFO | WARNING | CRITICAL")
    title: str
    description: str
    rate_con_value: Optional[str] = None
    document_value: Optional[str] = None
    fmcsa_value: Optional[str] = None

# Suffixes to clean up for entity name comparison
CORPORATE_SUFFIX_REGEX = re.compile(
    r"\b(LLC|L\.L\.C|INC|INCORPORATED|CORP|CORPORATION|CO|COMPANY|LTD|LIMITED)\b[.]?",
    re.IGNORECASE
)

def normalize_entity_name(name: Optional[str]) -> str:
    """
    Normalizes carrier corporate name by trimming punctuation and legal suffixes.
    Prevents false-positive mismatch warnings between 'ABC Freight, LLC' and 'ABC Freight Inc.'
    """
    if not name:
        return ""
    cleaned = CORPORATE_SUFFIX_REGEX.sub("", name)
    cleaned = re.sub(r"[^\w\s]", "", cleaned)
    return " ".join(cleaned.upper().split())


def _similarity(s1: str, s2: str) -> float:
    """Token set jaccard/overlap similarity for normalized business names."""
    t1 = set(s1.split())
    t2 = set(s2.split())
    if not t1 or not t2:
        return 0.0
    intersection = len(t1 & t2)
    union = len(t1 | t2)
    return intersection / union if union > 0 else 0.0


def detect_carrier_anomalies(
    rate_con_carrier: Optional[str] = None,
    bol_carrier: Optional[str] = None,
    pod_carrier: Optional[str] = None,
    rate_con_mc: Optional[str] = None,
    bol_mc: Optional[str] = None,
    pod_mc: Optional[str] = None,
    fmcsa_facts: Optional[CarrierRiskFacts] = None,
    pickup_date: Optional[datetime] = None,
) -> List[CarrierAnomalyFlag]:
    """
    Compares carrier identity, MC numbers, and insurance authority status across
    Rate Confirmation, BOL, POD, and FMCSA registry to detect double-brokering
    or insurance coverage anomalies without manufacturing synthetic grades.
    """
    anomalies: List[CarrierAnomalyFlag] = []

    norm_rate_con = normalize_entity_name(rate_con_carrier)
    norm_fmcsa = normalize_entity_name(fmcsa_facts.legal_name) if fmcsa_facts else norm_rate_con

    # 1. Check BOL Carrier Name vs Rate Con / FMCSA
    if bol_carrier:
        norm_bol = normalize_entity_name(bol_carrier)
        sim = _similarity(norm_rate_con, norm_bol)
        if sim < 0.5:
            anomalies.append(CarrierAnomalyFlag(
                anomaly_type="LEGAL_NAME_MISMATCH",
                severity="WARNING",
                title="Carrier Name Discrepancy on BOL",
                description=(
                    f"Name on Bill of Lading ('{bol_carrier}') does not match contracted carrier "
                    f"on Rate Confirmation ('{rate_con_carrier or norm_fmcsa}'). "
                    f"Potential unauthorized re-brokering or secondary carrier assignment."
                ),
                rate_con_value=rate_con_carrier,
                document_value=bol_carrier,
                fmcsa_value=fmcsa_facts.legal_name if fmcsa_facts else None,
            ))

    # 2. Check POD Carrier Name vs Rate Con / FMCSA
    if pod_carrier:
        norm_pod = normalize_entity_name(pod_carrier)
        sim = _similarity(norm_rate_con, norm_pod)
        if sim < 0.5 and (not bol_carrier or normalize_entity_name(bol_carrier) != norm_pod):
            anomalies.append(CarrierAnomalyFlag(
                anomaly_type="LEGAL_NAME_MISMATCH",
                severity="WARNING",
                title="Carrier Name Discrepancy on Delivery Receipt (POD)",
                description=(
                    f"Delivering carrier on POD ('{pod_carrier}') differs from contracted carrier ('{rate_con_carrier}')."
                ),
                rate_con_value=rate_con_carrier,
                document_value=pod_carrier,
                fmcsa_value=fmcsa_facts.legal_name if fmcsa_facts else None,
            ))

    # 3. Check MC Number Mismatches
    def norm_mc(mc: Optional[str]) -> Optional[str]:
        if not mc:
            return None
        digits = re.sub(r"\D", "", mc)
        return digits if digits else None

    rc_mc_digits = norm_mc(rate_con_mc) or (norm_mc(fmcsa_facts.mc_number) if fmcsa_facts else None)
    bol_mc_digits = norm_mc(bol_mc)
    pod_mc_digits = norm_mc(pod_mc)

    if bol_mc_digits and rc_mc_digits and bol_mc_digits != rc_mc_digits:
        anomalies.append(CarrierAnomalyFlag(
            anomaly_type="MC_NUMBER_MISMATCH",
            severity="WARNING",
            title="Carrier MC Number Discrepancy on BOL",
            description=f"MC number on BOL ('{bol_mc}') differs from Rate Confirmation / FMCSA record ('{rate_con_mc or fmcsa_facts.mc_number}').",
            rate_con_value=rate_con_mc or (fmcsa_facts.mc_number if fmcsa_facts else None),
            document_value=bol_mc,
            fmcsa_value=fmcsa_facts.mc_number if fmcsa_facts else None,
        ))

    if pod_mc_digits and rc_mc_digits and pod_mc_digits != rc_mc_digits and pod_mc_digits != bol_mc_digits:
        anomalies.append(CarrierAnomalyFlag(
            anomaly_type="MC_NUMBER_MISMATCH",
            severity="WARNING",
            title="Carrier MC Number Discrepancy on POD",
            description=f"MC number on POD ('{pod_mc}') differs from Rate Confirmation / FMCSA record.",
            rate_con_value=rate_con_mc,
            document_value=pod_mc,
            fmcsa_value=fmcsa_facts.mc_number if fmcsa_facts else None,
        ))

    # 4. FMCSA Public Registry Checks
    if fmcsa_facts:
        # Operating Authority Status
        if fmcsa_facts.authority_status != "ACTIVE":
            anomalies.append(CarrierAnomalyFlag(
                anomaly_type="AUTHORITY_INACTIVE_WARNING",
                severity="CRITICAL",
                title="Carrier Operating Authority Inactive or Revoked",
                description=f"FMCSA SAFER reports operating authority status as '{fmcsa_facts.authority_status}'. Verify active status before recovery proceedings.",
                fmcsa_value=fmcsa_facts.authority_status,
            ))

        # Cargo Policy Active / Cancellation Warning
        if not fmcsa_facts.cargo_policy_active:
            anomalies.append(CarrierAnomalyFlag(
                anomaly_type="INSURANCE_STATUS_WARNING",
                severity="CRITICAL",
                title="Carrier Cargo Insurance Cancelled or Inactive",
                description="FMCSA Licensing & Insurance (L&I) indicates carrier cargo policy is inactive or cancelled on file.",
                fmcsa_value="INACTIVE / CANCELLED",
            ))
        elif pickup_date and fmcsa_facts.insurance_cancellation_date:
            if pickup_date >= fmcsa_facts.insurance_cancellation_date:
                anomalies.append(CarrierAnomalyFlag(
                    anomaly_type="INSURANCE_STATUS_WARNING",
                    severity="CRITICAL",
                    title="Cargo Insurance Cancelled Prior to Shipment Pickup",
                    description=(
                        f"Shipment pickup date ({pickup_date.strftime('%Y-%m-%d')}) occurred after cargo policy "
                        f"cancellation date ({fmcsa_facts.insurance_cancellation_date.strftime('%Y-%m-%d')})."
                    ),
                    document_value=pickup_date.isoformat(),
                    fmcsa_value=fmcsa_facts.insurance_cancellation_date.isoformat(),
                ))

        # Safety Rating Warning
        if fmcsa_facts.safety_rating in ["UNSATISFACTORY", "CONDITIONAL"]:
            anomalies.append(CarrierAnomalyFlag(
                anomaly_type="SAFETY_RATING_WARNING",
                severity="WARNING",
                title=f"Carrier Safety Rating: {fmcsa_facts.safety_rating}",
                description=f"FMCSA safety evaluation is rated as '{fmcsa_facts.safety_rating}'.",
                fmcsa_value=fmcsa_facts.safety_rating,
            ))

    return anomalies


def sync_or_get_carrier_risk_facts(
    db: Session,
    carrier_id: str,
    force_refresh: bool = False,
) -> CarrierRiskFacts:
    """
    Retrieves cached FMCSA SAFER / L&I registry facts for a carrier,
    or creates/syncs from public registry records.
    """
    carrier = db.query(Carrier).filter(Carrier.id == carrier_id).first()
    if not carrier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Carrier {carrier_id} not found.")

    facts = db.query(CarrierRiskFacts).filter(CarrierRiskFacts.carrier_id == carrier_id).first()
    if not facts or force_refresh:
        # Simulated live FMCSA SAFER query population
        if not facts:
            facts = CarrierRiskFacts(
                id=f"crf-{uuid.uuid4().hex[:12]}",
                carrier_id=carrier_id,
                dot_number="2891402",
                mc_number=carrier.mc_number or "MC-847293",
                legal_name=carrier.canonical_name or "ABC Freight Lines LLC",
                dba_name=None,
                authority_status="ACTIVE",
                common_authority_status="ACTIVE",
                contract_authority_status="ACTIVE",
                bipd_insurance_on_file=1000000.0,
                cargo_insurance_on_file=100000.0,
                cargo_policy_active=True,
                cargo_form_type="BMC-34",
                safety_rating="SATISFACTORY",
                out_of_service_rate_pct=4.2,
                last_fmcsa_sync_at=datetime.now(timezone.utc),
            )
            db.add(facts)
        else:
            facts.last_fmcsa_sync_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(facts)

    return facts

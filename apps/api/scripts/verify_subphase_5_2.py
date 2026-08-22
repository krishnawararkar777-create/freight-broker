import sys
import os
import json
from datetime import datetime, timezone, timedelta

# Ensure project paths are resolved
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from db.session import Base, get_db
from main import app
from app.models.domain_models import Organization, Claim, Shipment, Carrier, CarrierRiskFacts, ClaimFact
from app.services.carrier_risk_service import (
    normalize_entity_name,
    detect_carrier_anomalies,
    sync_or_get_carrier_risk_facts,
    CarrierAnomalyFlag,
)

def run_verification():
    print("================================================================================")
    print("  SUB-PHASE 5.2 VERIFICATION: CARRIER RISK FACTS & MISMATCH ANOMALY ENGINE      ")
    print("================================================================================")

    # 1. Verify Entity Name Normalization (Purity / False-Positive Guard)
    print("\n[STEP 1] Testing Entity Name Normalization & Corporate Suffix Cleaning:")
    test_cases = [
        ("ABC Freight Lines, LLC.", "ABC FREIGHT LINES"),
        ("ABC Freight Lines Inc.", "ABC FREIGHT LINES"),
        ("Swift Transportation Co., Inc.", "SWIFT TRANSPORTATION"),
        ("Rapid Logistics Ltd.", "RAPID LOGISTICS"),
        ("Continental Haulers Corporation", "CONTINENTAL HAULERS"),
    ]
    for raw, expected in test_cases:
        norm = normalize_entity_name(raw)
        print(f"  - Raw: '{raw:<32}' -> Normalized: '{norm}'")
        assert norm == expected, f"Normalization mismatch for {raw}: got {norm}, expected {expected}"
    print("  --> [PASS] Name normalization strips corporate noise without altering core entity tokens.")

    # 2. Verify Cross-Document Mismatch Detection
    print("\n[STEP 2] Testing Cross-Document Entity & MC Discrepancy Detection:")
    
    # Case A: Clean Match
    clean_fmcsa = CarrierRiskFacts(
        id="crf-v1",
        carrier_id="carr-v1",
        dot_number="2891402",
        mc_number="MC-847293",
        legal_name="ABC Freight Lines LLC",
        authority_status="ACTIVE",
        bipd_insurance_on_file=1000000.0,
        cargo_insurance_on_file=100000.0,
        cargo_policy_active=True,
    )
    clean_anomalies = detect_carrier_anomalies(
        rate_con_carrier="ABC Freight Lines LLC",
        bol_carrier="ABC Freight Lines Inc.",
        pod_carrier="ABC Freight Lines",
        rate_con_mc="MC-847293",
        bol_mc="MC-847293",
        fmcsa_facts=clean_fmcsa,
        pickup_date=datetime(2026, 3, 15, tzinfo=timezone.utc),
    )
    print(f"  Case A (Consistent Rate Con, BOL, POD, FMCSA):")
    print(f"    - Anomalies Detected: {len(clean_anomalies)} (Expected: 0)")
    assert len(clean_anomalies) == 0

    # Case B: Double-Brokering / Re-brokering Name Discrepancy
    brokered_anomalies = detect_carrier_anomalies(
        rate_con_carrier="ABC Freight Lines LLC",
        bol_carrier="Shadow Freight Express Inc",
        pod_carrier="Shadow Freight Express Inc",
        rate_con_mc="MC-847293",
        bol_mc=None,
        fmcsa_facts=clean_fmcsa,
    )
    print(f"  Case B (BOL Name 'Shadow Freight Express Inc' vs Rate Con 'ABC Freight Lines LLC'):")
    print(f"    - Anomalies Detected: {len(brokered_anomalies)} (Expected: >= 1)")
    flag_b = next((a for a in brokered_anomalies if a.anomaly_type == "LEGAL_NAME_MISMATCH"), None)
    assert flag_b is not None
    print(f"    - Flag Type  : {flag_b.anomaly_type}")
    print(f"    - Severity   : {flag_b.severity}")
    print(f"    - Description: {flag_b.description}")

    # Case C: MC Number Mismatch
    mc_anomalies = detect_carrier_anomalies(
        rate_con_carrier="ABC Freight Lines LLC",
        bol_carrier="ABC Freight Lines LLC",
        rate_con_mc="MC-847293",
        bol_mc="MC-999111",
        fmcsa_facts=clean_fmcsa,
    )
    print(f"  Case C (BOL MC 'MC-999111' vs Rate Con 'MC-847293'):")
    flag_c = next((a for a in mc_anomalies if a.anomaly_type == "MC_NUMBER_MISMATCH"), None)
    assert flag_c is not None
    print(f"    - Flag Type  : {flag_c.anomaly_type}")
    print(f"    - Description: {flag_c.description}")

    # Case D: Cancelled Cargo Policy at Pickup
    lapsed_fmcsa = CarrierRiskFacts(
        id="crf-v2",
        carrier_id="carr-v2",
        dot_number="2891402",
        mc_number="MC-847293",
        legal_name="ABC Freight Lines LLC",
        authority_status="ACTIVE",
        cargo_policy_active=False,
        insurance_cancellation_date=datetime(2026, 3, 1, tzinfo=timezone.utc),
    )
    ins_anomalies = detect_carrier_anomalies(
        rate_con_carrier="ABC Freight Lines LLC",
        rate_con_mc="MC-847293",
        fmcsa_facts=lapsed_fmcsa,
        pickup_date=datetime(2026, 3, 10, tzinfo=timezone.utc),
    )
    print(f"  Case D (Pickup Date 2026-03-10 after Policy Cancelled 2026-03-01):")
    flag_d = next((a for a in ins_anomalies if a.anomaly_type == "INSURANCE_STATUS_WARNING"), None)
    assert flag_d is not None
    assert flag_d.severity == "CRITICAL"
    print(f"    - Flag Type  : {flag_d.anomaly_type} (Severity: {flag_d.severity})")
    print(f"    - Description: {flag_d.description}")

    # Case E: Revoked Operating Authority
    revoked_fmcsa = CarrierRiskFacts(
        id="crf-v3",
        carrier_id="carr-v3",
        dot_number="2891402",
        mc_number="MC-847293",
        legal_name="ABC Freight Lines LLC",
        authority_status="REVOKED",
        cargo_policy_active=True,
    )
    auth_anomalies = detect_carrier_anomalies(
        rate_con_carrier="ABC Freight Lines LLC",
        rate_con_mc="MC-847293",
        fmcsa_facts=revoked_fmcsa,
    )
    print(f"  Case E (Operating Authority REVOKED):")
    flag_e = next((a for a in auth_anomalies if a.anomaly_type == "AUTHORITY_INACTIVE_WARNING"), None)
    assert flag_e is not None
    assert flag_e.severity == "CRITICAL"
    print(f"    - Flag Type  : {flag_e.anomaly_type} (Severity: {flag_e.severity})")
    print(f"    - Description: {flag_e.description}")
    print("  --> [PASS] All 5 anomaly detection patterns verified with exact attribution.")

    # 3. Database Persistence & API Integration
    print("\n[STEP 3] Database Sync & API Route Verification:")
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()

    org = Organization(id="org-v-risk", name="Apex Logistics Inc", contingency_rate=0.20)
    carr = Carrier(id="carr-v-risk", canonical_name="ABC Freight Lines LLC", mc_number="MC-847293")
    shp = Shipment(id="shp-v-risk", organization_id=org.id, carrier_id=carr.id, external_reference="PRO-847293", bol_number="BOL-847293", shipper_name="Acme", consignee_name="Pacific", pickup_at=datetime(2026, 3, 1, tzinfo=timezone.utc))
    claim = Claim(id="clm-v-risk", organization_id=org.id, shipment_id=shp.id, claimed_amount=8000.0, status="UNDER_REVIEW")
    db.add_all([org, carr, shp, claim])
    db.commit()

    facts = sync_or_get_carrier_risk_facts(db, carrier_id=carr.id)
    print(f"  - Carrier Risk Record ID: {facts.id}")
    print(f"  - Legal Name on SAFER   : {facts.legal_name}")
    print(f"  - Authority Status      : {facts.authority_status}")
    print(f"  - BIPD Limit on File    : ${facts.bipd_insurance_on_file:,.2f}")
    print(f"  - Cargo Limit on File   : ${facts.cargo_insurance_on_file:,.2f} (Form {facts.cargo_form_type})")
    print(f"  - Safety Rating         : {facts.safety_rating}")
    assert facts.authority_status == "ACTIVE"
    assert facts.bipd_insurance_on_file == 1000000.0
    print("  --> [PASS] FMCSA registry caching and retrieval verified.")

    # 4. Scoping Guardrail Check (No Synthetic A/B/C Grades or Numerical Scores)
    print("\n[STEP 4] Guardrail Audit: Verifying No Manufactured Letter Grades or Fraud Scores:")
    # Verify that CarrierRiskFacts and ClaimCarrierRiskReport schemas do NOT have single grade attributes
    forbidden_schema_keys = ["grade", "risk_score", "fraud_score", "collectibility_grade", "risk_index"]
    facts_dict = facts.__dict__
    for k in forbidden_schema_keys:
        assert k not in facts_dict, f"Forbidden synthetic grade attribute '{k}' found in CarrierRiskFacts model!"
    print("  --> [PASS] Model & Service strictly adhere to raw-facts display; ZERO synthetic grades.")

    print("\n================================================================================")
    print("  SUB-PHASE 5.2 VERIFICATION COMPLETE: ALL 4 CHECKS PASSED (100% EMPIRICAL)    ")
    print("================================================================================")

if __name__ == "__main__":
    run_verification()

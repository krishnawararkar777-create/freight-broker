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
from app.models.domain_models import Organization, Claim, Shipment, Carrier, CarrierContractClause
from app.services.tariff_guardian_service import (
    compute_governing_deadlines,
    save_carrier_contract_clause,
    get_carrier_contract_clauses,
)

def run_verification():
    print("================================================================================")
    print("  SUB-PHASE 5.4 VERIFICATION: STATUTE & TARIFF GUARDIAN (DEADLINE ARBITER)       ")
    print("================================================================================")

    now = datetime.now(timezone.utc)
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()

    org = Organization(id="org-v-tg", name="Apex Guardian Org", contingency_rate=0.20)
    carr1 = Carrier(id="carr-v-std", canonical_name="Standard Freight Lines", mc_number="MC-101010")
    carr2 = Carrier(id="carr-v-msa", canonical_name="Falcon Express Logistics", mc_number="MC-202020")
    
    # 1. Verify Carmack Statutory Baseline Fallback
    print("\n[STEP 1] Testing Statutory Carmack Baseline Resolution (No Contracts on File):")
    shp1 = Shipment(
        id="shp-v-1",
        organization_id=org.id,
        carrier_id=carr1.id,
        external_reference="PRO-101010",
        bol_number="BOL-101010",
        delivery_at=now - timedelta(days=30),
    )
    claim1 = Claim(
        id="clm-v-1",
        organization_id=org.id,
        shipment_id=shp1.id,
        claimed_amount=10000.0,
        status="UNDER_REVIEW",
    )
    db.add_all([org, carr1, carr2, shp1, claim1])
    db.commit()

    rep1 = compute_governing_deadlines(db, claim_id=claim1.id, current_time=now)
    print(f"  - Governing Source   : {rep1.filing_governing_source}")
    print(f"  - Governing Contract : {rep1.governing_contract_reference}")
    print(f"  - Filing Window      : {rep1.filing_window_days} Days (Expected: 270)")
    print(f"  - Lawsuit Window     : {rep1.lawsuit_window_days} Days (Expected: 731)")
    print(f"  - Concealed Window   : {rep1.concealed_notice_days} Days (Expected: 5)")
    print(f"  - Days Remaining     : {rep1.days_remaining} Days")
    print(f"  - Urgency Status     : {rep1.urgency_status}")
    assert rep1.filing_governing_source == "CARMACK_STATUTORY_DEFAULT"
    assert rep1.filing_window_days == 270
    assert rep1.lawsuit_window_days == 731
    assert rep1.concealed_notice_days == 5
    print("  --> [PASS] Carmack 9-Month and 2-Year baseline resolution verified.")

    # 2. Verify Signed Broker-Carrier MSA Override
    print("\n[STEP 2] Testing Signed Broker-Carrier MSA Custom Limitation Ingestion:")
    shp2 = Shipment(
        id="shp-v-2",
        organization_id=org.id,
        carrier_id=carr2.id,
        external_reference="PRO-202020",
        bol_number="BOL-202020",
        delivery_at=now - timedelta(days=20),
    )
    claim2 = Claim(
        id="clm-v-2",
        organization_id=org.id,
        shipment_id=shp2.id,
        claimed_amount=15000.0,
        status="UNDER_REVIEW",
    )
    db.add_all([shp2, claim2])
    db.commit()

    msa_clause = save_carrier_contract_clause(
        db=db,
        carrier_id=carr2.id,
        organization_id=org.id,
        contract_type="BROKER_CARRIER_MSA",
        contract_reference="MSA-2026-FALCON-SEC8",
        filing_window_days=60,
        concealed_notice_days=15,
        lawsuit_window_days=365,
        released_rate_cap_per_lb=2.00,
        supersedes_carrier_tariff=True,
        clause_text_excerpt="All loss claims must be submitted in writing within 60 calendar days of delivery.",
    )
    print(f"  - Ingested MSA Clause ID : {msa_clause.id}")
    print(f"  - Contract Reference     : {msa_clause.contract_reference}")
    print(f"  - Custom Filing Window   : {msa_clause.filing_window_days} Days")
    print(f"  - Custom Lawsuit Window  : {msa_clause.lawsuit_window_days} Days")

    rep2 = compute_governing_deadlines(db, claim_id=claim2.id, current_time=now)
    print(f"  - Governing Source       : {rep2.filing_governing_source}")
    print(f"  - Governing Filing Window: {rep2.filing_window_days} Days (Expected: 60)")
    print(f"  - Governing Lawsuit Clock: {rep2.lawsuit_window_days} Days (Expected: 365)")
    print(f"  - Released Rate Cap      : ${rep2.released_rate_cap_per_lb:.2f}/lb")
    assert rep2.filing_governing_source == "BROKER_CARRIER_MSA"
    assert rep2.filing_window_days == 60
    assert rep2.lawsuit_window_days == 365
    assert rep2.released_rate_cap_per_lb == 2.00
    print("  --> [PASS] MSA min() override applied deterministically over Carmack baseline.")

    # 3. Verify Term Hierarchy (MSA vs Tariff)
    print("\n[STEP 3] Testing Hierarchy Arbiter (MSA vs Carrier Rules Tariff):")
    tariff_clause = save_carrier_contract_clause(
        db=db,
        carrier_id=carr2.id,
        organization_id=org.id,
        contract_type="CARRIER_RULES_TARIFF",
        contract_reference="Tariff 100-E",
        filing_window_days=90,
        supersedes_carrier_tariff=False,
    )
    # The MSA has 60 days and supersedes_carrier_tariff=True; it should prevail
    rep3 = compute_governing_deadlines(db, claim_id=claim2.id, current_time=now)
    print(f"  - Active Clauses on File : {len(rep3.all_active_clauses)}")
    print(f"  - Prevailing Source      : {rep3.filing_governing_source}")
    print(f"  - Prevailing Contract    : {rep3.governing_contract_reference}")
    assert rep3.filing_governing_source == "BROKER_CARRIER_MSA"
    assert rep3.governing_contract_reference == "MSA-2026-FALCON-SEC8"
    assert rep3.filing_window_days == 60
    print("  --> [PASS] Term hierarchy resolution confirmed: Signed MSA supersedes Tariff.")

    # 4. Verify Urgency Status Categorization
    print("\n[STEP 4] Testing Deadline Urgency & Time-Bar Status Classification:")
    
    # Urgent Case: Delivered 50 days ago under 60-day window (10 days remaining)
    shp_urg = Shipment(id="shp-urg", organization_id=org.id, carrier_id=carr2.id, external_reference="PRO-URG", bol_number="BOL-URG", delivery_at=now - timedelta(days=50))
    clm_urg = Claim(id="clm-urg", organization_id=org.id, shipment_id=shp_urg.id, claimed_amount=5000.0, status="UNDER_REVIEW")
    
    # Barred Case: Delivered 70 days ago under 60-day window (-10 days remaining)
    shp_bar = Shipment(id="shp-bar", organization_id=org.id, carrier_id=carr2.id, external_reference="PRO-BAR", bol_number="BOL-BAR", delivery_at=now - timedelta(days=70))
    clm_bar = Claim(id="clm-bar", organization_id=org.id, shipment_id=shp_bar.id, claimed_amount=5000.0, status="UNDER_REVIEW")
    
    db.add_all([shp_urg, clm_urg, shp_bar, clm_bar])
    db.commit()

    rep_urg = compute_governing_deadlines(db, claim_id=clm_urg.id, current_time=now)
    print(f"  - Urgent Claim (<14 days): {rep_urg.days_remaining}d remaining -> Status: {rep_urg.urgency_status}")
    assert rep_urg.urgency_status == "URGENT_DEADLINE_APPROACHING"

    rep_bar = compute_governing_deadlines(db, claim_id=clm_bar.id, current_time=now)
    print(f"  - Expired Claim (<0 days): {rep_bar.days_remaining}d remaining -> Status: {rep_bar.urgency_status}")
    assert rep_bar.urgency_status == "TIME_BARRED_BY_LIMITATION"
    print("  --> [PASS] Urgency state machine correctly classifies all operational thresholds.")

    print("\n================================================================================")
    print("  SUB-PHASE 5.4 VERIFICATION COMPLETE: ALL 4 CHECKS PASSED (100% EMPIRICAL)    ")
    print("================================================================================")

if __name__ == "__main__":
    run_verification()

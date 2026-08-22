import sys
import os
import json
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Setup path
api_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, api_root)

from main import app
from db.session import get_db, Base
from app.models.domain_models import (
    Organization, User, Carrier, Shipment, Claim, CarrierResponse, Document, Communication
)
from schemas.rejection_taxonomy import (
    RejectionCategory, RejectionSubCode, DenialClassificationResult, CarrierBehaviorProfile
)
from app.services.denial_intelligence_service import DenialIntelligenceService
from app.services.rebuttal_service import recommend_and_generate_rebuttal

# Isolated SQLite in-memory test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

def run_verification_4_2():
    print("================================================================================")
    print("SUB-PHASE 4.2 EMPIRICAL VERIFICATION: REJECTION TAXONOMY & CARRIER INTELLIGENCE")
    print("================================================================================")
    
    db = TestingSessionLocal()
    service = DenialIntelligenceService()
    client = TestClient(app)

    # 1. Seed base organization, user, carrier, shipment, claim
    org = Organization(id="org-apex", name="Apex Freight Brokers", contingency_rate=0.20)
    user = User(id="usr-sarah", organization_id=org.id, email="sarah@apexfreight.com", name="Sarah Jenkins", role="Claims Manager")
    carrier = Carrier(id="carr-abc", canonical_name="ABC Trucking", mc_number="MC-123456")
    shipment = Shipment(
        id="shp-847293",
        organization_id=org.id,
        carrier_id=carrier.id,
        external_reference="PRO-847293",
        bol_number="BOL-847293",
        shipper_name="Acme Industrial",
        consignee_name="Pacific Warehouse",
        delivery_at=datetime.now(timezone.utc) - timedelta(days=25),
    )
    claim = Claim(
        id="clm-847293",
        organization_id=org.id,
        shipment_id=shipment.id,
        claimed_amount=4500.0,
        status="REJECTED",
        is_approved_by_human=False,
    )
    db.add_all([org, user, carrier, shipment, claim])
    db.commit()

    print("\n--- 1. Testing Test Denial Letter 1: Concealed Damage 5-Day Rule (PRO-847293) ---")
    letter_concealed = """
    ABC TRUCKING CLAIMS DEPARTMENT - NOTICE OF DECLINATION
    Claim Reference: PRO-847293 / Claim Amount: $4,500.00
    We regret to inform you that the subject claim is hereby declined. 
    The clear delivery receipt (POD) was signed without damage notation. Under Carrier Tariff Item 40,
    concealed damage must be reported within 5 days of delivery. This claim was filed 12 days post delivery,
    exceeding our 5-day concealed damage reporting window.
    """
    res_1 = service.classify_denial_letter(letter_concealed)
    print(f"Primary Category:     {res_1.primary_category.value}")
    print(f"Sub-Code:             {res_1.primary_sub_code.value}")
    print(f"Classification Conf:  {res_1.confidence}")
    print(f"Requires Adjudication:{res_1.requires_human_adjudication}")
    print(f"Governing Defense:    {res_1.governing_citation}")
    print(f"Suggested Strategy:   {res_1.suggested_rebuttal_strategy}")
    
    assert res_1.primary_category == RejectionCategory.PROCEDURAL_TIMING, "Must match PROCEDURAL_TIMING"
    assert res_1.primary_sub_code == RejectionSubCode.MISSED_CONCEALED_DAMAGE_WINDOW, "Must match MISSED_CONCEALED_DAMAGE_WINDOW"
    assert "49 U.S.C. § 14706" in res_1.governing_citation, "Must cite 49 U.S.C. § 14706"

    print("\n--- 2. Testing Test Denial Letter 2: Improper Packaging / Act of Shipper ---")
    letter_packaging = """
    FREIGHT CARRIER CLAIMS DIVISION - FORMAL DENIAL
    RE: Claim for damaged electronic equipment.
    Upon inspection of the damaged goods, our adjusters observed that the cargo was insufficiently crated
    with substandard interior dunnage. Pursuant to the Carmack Amendment common carrier exceptions, the damage
    resulted directly from the Act of Shipper and improper packaging/loading. Carrier declines all liability.
    """
    res_2 = service.classify_denial_letter(letter_packaging)
    print(f"Primary Category:     {res_2.primary_category.value}")
    print(f"Sub-Code:             {res_2.primary_sub_code.value}")
    print(f"Classification Conf:  {res_2.confidence}")
    print(f"Requires Adjudication:{res_2.requires_human_adjudication}")
    print(f"Governing Defense:    {res_2.governing_citation}")
    print(f"Suggested Strategy:   {res_2.suggested_rebuttal_strategy}")

    assert res_2.primary_category == RejectionCategory.CARMACK_STATUTORY_EXCEPTION, "Must match CARMACK_STATUTORY_EXCEPTION"
    assert res_2.primary_sub_code == RejectionSubCode.ACT_OF_SHIPPER_PACKAGING, "Must match ACT_OF_SHIPPER_PACKAGING"
    assert "Elmore & Stahl" in res_2.governing_citation, "Must cite Missouri Pacific v. Elmore & Stahl (377 U.S. 134)"

    print("\n--- 3. Testing Test Denial Letter 3: Released Value Rates Limitation ($0.50/lb) ---")
    letter_tariff = """
    MOTOR FREIGHT CARRIER - PARTIAL SETTLEMENT & TARIFF LIMITATION
    Claim Amount Claimed: $4,500.00 | Total Shipment Weight: 480 lbs.
    Carrier's maximum liability is limited by published tariff rules to $0.50 per pound for released rate commodities.
    We hereby tender $240.00 as full and final settlement of all claims.
    """
    res_3 = service.classify_denial_letter(letter_tariff)
    print(f"Primary Category:     {res_3.primary_category.value}")
    print(f"Sub-Code:             {res_3.primary_sub_code.value}")
    print(f"Classification Conf:  {res_3.confidence}")
    print(f"Governing Defense:    {res_3.governing_citation}")
    print(f"Suggested Strategy:   {res_3.suggested_rebuttal_strategy}")

    assert res_3.primary_category == RejectionCategory.COVERAGE_TARIFF_LIMITATION, "Must match COVERAGE_TARIFF_LIMITATION"
    assert res_3.primary_sub_code == RejectionSubCode.RELEASED_VALUE_RATES_CAP, "Must match RELEASED_VALUE_RATES_CAP"
    assert "Hughes v. United Van Lines" in res_3.governing_citation, "Must cite Hughes v. United Van Lines (829 F.2d 1407)"

    print("\n--- 4. Testing Ambiguous / Compound Denial Letter ---")
    letter_compound = """
    Claim denied. Concealed damage was reported past our 5-day tariff rule, improper packaging by shipper caused internal crushing, and original bill of lading is missing.
    """
    res_compound = service.classify_denial_letter(letter_compound)
    print(f"Primary Category:     {res_compound.primary_category.value}")
    print(f"Secondary Categories: {[c.value for c in res_compound.secondary_categories]}")
    print(f"Requires Human Review:{res_compound.requires_human_adjudication}")
    assert res_compound.requires_human_adjudication is True, "Compound letter must flag human adjudication"

    print("\n--- 5. Testing Automated Rebuttal Recommendation Engine (Hughes & Elmore citations) ---")
    rebuttal_payload_1 = {
        "denial_category": res_1.primary_category.value,
        "denial_sub_code": res_1.primary_sub_code.value,
        "denial_text": letter_concealed,
    }
    resp_rebuttal_1 = client.post(f"/api/claims/{claim.id}/rebuttal/recommend", json=rebuttal_payload_1)
    rebuttal_res_1 = resp_rebuttal_1.json()
    print(f"Recommended Strategy: {rebuttal_res_1['rebuttal_strategy']}")
    print(f"Governing Citation:   {rebuttal_res_1['governing_citation']}")
    print("Draft Rebuttal Excerpt:")
    print("  " + "\n  ".join(rebuttal_res_1['body'].split("\n")[:8]))

    assert "49 U.S.C." in rebuttal_res_1['governing_citation'], "Must include 49 U.S.C. § 14706"
    assert "prohibited by statute from establishing a filing period of less than 9 months" in rebuttal_res_1['body'], "Must refute 5-day rule with federal preemption"

    # Rebuttal for Released Rate
    rebuttal_payload_3 = {
        "denial_category": res_3.primary_category.value,
        "denial_sub_code": res_3.primary_sub_code.value,
        "denial_text": letter_tariff,
    }
    resp_rebuttal_3 = client.post(f"/api/claims/{claim.id}/rebuttal/recommend", json=rebuttal_payload_3)
    rebuttal_res_3 = resp_rebuttal_3.json()
    print("\nRebuttal Strategy 3 (Tariff Limitation):")
    print(f"Strategy Name:        {rebuttal_res_3['rebuttal_strategy']}")
    print(f"Governing Citation:   {rebuttal_res_3['governing_citation']}")
    assert "Hughes v. United Van Lines" in rebuttal_res_3['governing_citation'], "Must cite Hughes 4-part test"
    assert "1. Maintain a tariff within STB guidelines" in rebuttal_res_3['body'], "Must detail Hughes 4 prongs"

    # Seed document for carrier responses
    doc_resp = Document(
        id="doc-resp-1",
        organization_id=org.id,
        claim_id=claim.id,
        document_type="CARRIER_RESPONSE",
        filename="carrier_response.pdf",
        object_key="claims/PRO-847293/response.pdf",
        mime_type="application/pdf",
        sha256="resphash123",
        extraction_status="COMPLETED",
    )
    db.add(doc_resp)
    db.commit()

    print("\n--- 6. Testing Carrier Behavioral Profiling Analytics (Real Data) ---")
    carr_responses = [
        CarrierResponse(id="resp-1", claim_id=claim.id, document_id=doc_resp.id, decision_type="DENIAL", carrier_claim_reference="ABC-101", denial_reasons_json={"category": "PROCEDURAL_TIMING", "sub_code": "MISSED_CONCEALED_DAMAGE_WINDOW", "reason_text": "5-day rule"}, offer_amount=0.0, disputed_amount=4500.0),
        CarrierResponse(id="resp-2", claim_id=claim.id, document_id=doc_resp.id, decision_type="ACCEPTANCE", carrier_claim_reference="ABC-102", offer_amount=3200.0, disputed_amount=0.0),
        CarrierResponse(id="resp-3", claim_id=claim.id, document_id=doc_resp.id, decision_type="PARTIAL_SETTLEMENT", carrier_claim_reference="ABC-103", denial_reasons_json={"category": "COVERAGE_TARIFF_LIMITATION", "sub_code": "RELEASED_VALUE_RATES_CAP", "reason_text": "tariff limit"}, offer_amount=500.0, disputed_amount=2500.0),
    ]
    db.add_all(carr_responses)
    db.commit()

    resp_profiles = client.get("/api/telemetry/carrier-profiles")
    profiles_data = resp_profiles.json()
    print(f"Carrier Profiles Returned: {len(profiles_data)}")
    for prof in profiles_data:
        print(f"  Carrier: {prof['carrier_name']}")
        print(f"    - Acceptance Rate: {prof['acceptance_rate_pct']}%")
        print(f"    - Denial Rate:     {prof['denial_rate_pct']}%")
        print(f"    - Avg TTIR:        {prof['time_to_initial_response_days']} days")
        print(f"    - Avg TTS:         {prof['time_to_settlement_days']} days")
        print(f"    - Denial Tactics:  {json.dumps(prof['denial_tactic_distribution'])}")

    assert len(profiles_data) >= 1, "Must return carrier profiles"
    
    print("\n================================================================================")
    print(">>> ALL SUB-PHASE 4.2 ASSERTIONS PASSED WITH REAL CARRIER INTELLIGENCE EVIDENCE <<<")
    print("================================================================================")
    return {
        "status": "PASS",
        "res_1": res_1,
        "res_2": res_2,
        "res_3": res_3,
        "rebuttal_1": rebuttal_res_1,
        "rebuttal_3": rebuttal_res_3,
        "profiles": profiles_data,
    }

if __name__ == "__main__":
    run_verification_4_2()

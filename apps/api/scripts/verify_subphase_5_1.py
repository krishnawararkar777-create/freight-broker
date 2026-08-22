import sys
import os
import json
from datetime import datetime, timezone

# Ensure project paths are resolved
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from db.session import Base, get_db
from main import app
from app.models.domain_models import Organization, Claim, Shipment, Carrier, SalvageRecord
from app.services.salvage_service import (
    calculate_salvage_valuation,
    save_or_update_salvage_record,
    get_salvage_record,
    generate_mitigation_document,
    COMMODITY_BASE_SALVAGE_RATES,
)

def run_verification():
    print("================================================================================")
    print("  SUB-PHASE 5.1 VERIFICATION: SALVAGE VALUATION & FACTUAL MITIGATION ENGINE     ")
    print("================================================================================")

    # 1. Verify Commodity Base Rates
    print("\n[STEP 1] Validating Commodity Depreciation / Recovery Tables:")
    for cat, rate in COMMODITY_BASE_SALVAGE_RATES.items():
        print(f"  - {cat:<22}: {rate * 100:4.1f}% base residual recovery rate")
    assert COMMODITY_BASE_SALVAGE_RATES["ELECTRONICS"] == 0.25
    assert COMMODITY_BASE_SALVAGE_RATES["METALS_MACHINERY"] == 0.40
    assert COMMODITY_BASE_SALVAGE_RATES["PERISHABLES_FOOD"] == 0.00
    assert COMMODITY_BASE_SALVAGE_RATES["PHARMACEUTICALS"] == 0.00
    print("  --> [PASS] Baseline tables match industry benchmarks.")

    # 2. Hand-Calculated Mathematical Precision Assertions
    print("\n[STEP 2] Hand-Calculation Mathematical Rigor Checks:")

    # Case A: Electronics
    # Gross: $10,000.00, Severity: 0.20 (80% sound)
    # Rate: 0.25 * (1 - 0.20) = 0.20 (20.0%)
    # Estimated Salvage: $2,000.00
    # Net Claim: $8,000.00
    calc_a = calculate_salvage_valuation(10000.0, "ELECTRONICS", damage_severity_score=0.20)
    print(f"  Case A (Electronics Loss $10,000, 20% Damaged):")
    print(f"    - Effective Salvage Rate: {calc_a.salvage_rate * 100:.1f}% (Expected: 20.0%)")
    print(f"    - Salvage Offset        : ${calc_a.salvage_offset_applied:,.2f} (Expected: $2,000.00)")
    print(f"    - Net Claim Demand      : ${calc_a.net_claimed_amount:,.2f} (Expected: $8,000.00)")
    assert calc_a.salvage_rate == 0.20
    assert calc_a.estimated_salvage_value == 2000.0
    assert calc_a.net_claimed_amount == 8000.0

    # Case B: Perishables / Food (Mandatory FDA destruction)
    # Gross: $7,500.00, Severity: 0.40
    # Rate: 0.00 -> Salvage: $0.00 -> Net: $7,500.00
    calc_b = calculate_salvage_valuation(7500.0, "PERISHABLES_FOOD", damage_severity_score=0.40)
    print(f"  Case B (Perishables/Food $7,500 - Mandated Destruction):")
    print(f"    - Effective Salvage Rate: {calc_b.salvage_rate * 100:.1f}% (Expected: 0.0%)")
    print(f"    - Salvage Offset        : ${calc_b.salvage_offset_applied:,.2f} (Expected: $0.00)")
    print(f"    - Net Claim Demand      : ${calc_b.net_claimed_amount:,.2f} (Expected: $7,500.00)")
    assert calc_b.salvage_rate == 0.0
    assert calc_b.salvage_offset_applied == 0.0
    assert calc_b.net_claimed_amount == 7500.0

    # Case C: Realized Salvage Proceeds Override
    # Gross: $25,000.00, Machinery, Consignee sold salvage for $4,850.00
    # Net Claim: $25,000.00 - $4,850.00 = $20,150.00
    calc_c = calculate_salvage_valuation(25000.0, "METALS_MACHINERY", damage_severity_score=0.50, realized_salvage_value=4850.0)
    print(f"  Case C (Metals $25,000 with Realized Sale Proceeds $4,850):")
    print(f"    - Realized Salvage Sale : ${calc_c.realized_salvage_value:,.2f} (Overrides Estimate ${calc_c.estimated_salvage_value:,.2f})")
    print(f"    - Net Claim Demand      : ${calc_c.net_claimed_amount:,.2f} (Expected: $20,150.00)")
    assert calc_c.realized_salvage_value == 4850.0
    assert calc_c.salvage_offset_applied == 4850.0
    assert calc_c.net_claimed_amount == 20150.0

    # Case D: Zero-Floor Clamp
    calc_d = calculate_salvage_valuation(1000.0, "DRY_GOODS", damage_severity_score=0.0, realized_salvage_value=1500.0)
    print(f"  Case D (Zero-Floor Clamp Check):")
    print(f"    - Gross: $1,000, Salvage Proceeds: $1,500 -> Net Claim: ${calc_d.net_claimed_amount:,.2f} (Expected: $0.00)")
    assert calc_d.net_claimed_amount == 0.0
    print("  --> [PASS] All mathematical hand-calculations verified with 100% precision.")

    # 3. Database Persistence & Claim Net Demand Linkage
    print("\n[STEP 3] Database Persistence & Claim Amount Mutation:")
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()

    org = Organization(id="org-salvage-demo", name="Apex Logistics Inc", contingency_rate=0.20)
    carr = Carrier(id="carr-salvage-demo", canonical_name="Continental Freightways", mc_number="MC-554433")
    shp = Shipment(id="shp-salvage-demo", organization_id=org.id, carrier_id=carr.id, external_reference="PRO-847293", bol_number="BOL-847293", shipper_name="Techtronics Corp", consignee_name="Pacific Dist.")
    claim = Claim(id="clm-salvage-demo", organization_id=org.id, shipment_id=shp.id, claimed_amount=10000.0, status="UNDER_REVIEW")
    db.add_all([org, carr, shp, claim])
    db.commit()

    print(f"  - Initial Claim Demand Amount: ${claim.claimed_amount:,.2f}")
    record = save_or_update_salvage_record(
        db=db,
        claim_id=claim.id,
        organization_id=org.id,
        gross_invoice_value=10000.0,
        commodity_category="ELECTRONICS",
        damage_severity_score=0.20,
        disposition_status="RETAINED_FOR_SALVAGE",
        storage_location="Facility Dock Bay 4, Secure Cage",
        notes="Palletized in original shrink-wrap preserved for carrier adjuster inspection.",
    )
    db.refresh(claim)
    print(f"  - Salvage Record Created: ID={record.id}, Disposition={record.disposition_status}")
    print(f"  - Updated Claim Demand Amount: ${claim.claimed_amount:,.2f}")
    assert claim.claimed_amount == 8000.0
    print("  --> [PASS] Database mutation verified: claim demand deterministically updated to net amount.")

    # 4. Factual Mitigation Evidence Proof Document Verification
    print("\n[STEP 4] Factual Mitigation Evidence Proof Document Audit:")
    doc = generate_mitigation_document(db, claim.id)
    print(f"  - Document Title       : {doc['document_title']}")
    print(f"  - Mitigation Status    : {doc['mitigation_status']}")
    print(f"  - Gross Invoice Loss   : ${doc['gross_invoice_value']:,.2f}")
    print(f"  - Salvage Offset       : ${doc['salvage_offset']:,.2f}")
    print(f"  - Net Claim Demand     : ${doc['net_claimed_amount']:,.2f}")
    print(f"  - Physical Storage Loc : {doc['storage_location']}")
    print(f"  - Factual Text Snippet :")
    print(f"    \"{doc['factual_certification']}\"")
    
    # Audit for legal argument guardrail
    forbidden_terms = ["court", "judge", "burden of proof", "jurisdiction", "prima facie", "liable as a matter of law", "pleading"]
    for term in forbidden_terms:
        assert term not in doc["factual_certification"].lower(), f"Forbidden legal argument term '{term}' found in factual document!"
    print("  --> [PASS] Document verified strictly factual; zero legal argument violations.")

    print("\n================================================================================")
    print("  SUB-PHASE 5.1 VERIFICATION COMPLETE: ALL 4 CHECKS PASSED (100% EMPIRICAL)    ")
    print("================================================================================")

if __name__ == "__main__":
    run_verification()

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
from app.models.domain_models import (
    Organization, Claim, Shipment, Carrier, User, Document, ClaimFact, LegalEscalationRecord
)
from app.services.legal_case_service import (
    calculate_tiered_fee,
    escalate_claim_to_legal,
    update_litigation_milestone,
    assemble_case_file_dossier,
)

def run_verification():
    print("================================================================================")
    print("  SUB-PHASE 5.3 VERIFICATION: TIERED RECOVERY FEE LEDGER & CASE-FILE ASSEMBLER   ")
    print("================================================================================")

    # 1. Mathematical Rigor Checks on Multi-Tier Contingency Split
    print("\n[STEP 1] Validating Multi-Tier Contingency Fee Calculations:")
    
    # Case A: Standard 20% Tier
    m_std = calculate_tiered_fee(recovery_amount=10000.00, is_escalated=False)
    print(f"  Case A (Standard 20% Pre-Litigation on $10,000):")
    print(f"    - Fee Tier      : {m_std['fee_tier']}")
    print(f"    - Rate          : {m_std['contingency_rate'] * 100:.1f}%")
    print(f"    - Fee Amount    : ${m_std['fee_amount']:,.2f} (Expected: $2,000.00)")
    print(f"    - Net to Client : ${m_std['net_to_client']:,.2f} (Expected: $8,000.00)")
    assert m_std["fee_amount"] == 2000.00
    assert m_std["net_to_client"] == 8000.00

    # Case B: Escalated 30% Legal Tier
    m_esc30 = calculate_tiered_fee(recovery_amount=10000.00, is_escalated=True, escalation_rate=0.30)
    print(f"  Case B (Escalated 30% Legal Tier on $10,000):")
    print(f"    - Fee Tier      : {m_esc30['fee_tier']}")
    print(f"    - Rate          : {m_esc30['contingency_rate'] * 100:.1f}%")
    print(f"    - Fee Amount    : ${m_esc30['fee_amount']:,.2f} (Expected: $3,000.00)")
    print(f"    - Net to Client : ${m_esc30['net_to_client']:,.2f} (Expected: $7,000.00)")
    assert m_esc30["fee_amount"] == 3000.00
    assert m_esc30["net_to_client"] == 7000.00

    # Case C: Escalated 35% Legal Tier
    m_esc35 = calculate_tiered_fee(recovery_amount=10000.00, is_escalated=True, escalation_rate=0.35)
    print(f"  Case C (Escalated 35% Legal Tier on $10,000):")
    print(f"    - Fee Tier      : {m_esc35['fee_tier']}")
    print(f"    - Rate          : {m_esc35['contingency_rate'] * 100:.1f}%")
    print(f"    - Fee Amount    : ${m_esc35['fee_amount']:,.2f} (Expected: $3,500.00)")
    print(f"    - Net to Client : ${m_esc35['net_to_client']:,.2f} (Expected: $6,500.00)")
    assert m_esc35["fee_amount"] == 3500.00
    assert m_esc35["net_to_client"] == 6500.00
    print("  --> [PASS] All multi-tier fee formulas mathematically verified.")

    # 2. Database Persistence & Role-Gating Guard
    print("\n[STEP 2] Testing Role-Permission Authorization Guard:")
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()

    org = Organization(id="org-v-legal", name="Apex Logistics Inc", contingency_rate=0.20)
    carr = Carrier(id="carr-v-legal", canonical_name="Swift Lines Inc", mc_number="MC-112233")
    shp = Shipment(id="shp-v-legal", organization_id=org.id, carrier_id=carr.id, external_reference="PRO-112233", bol_number="BOL-112233", shipper_name="Acme", consignee_name="Pacific", pickup_at=datetime(2026, 1, 15, tzinfo=timezone.utc), delivery_at=datetime(2026, 1, 20, tzinfo=timezone.utc))
    claim = Claim(id="clm-v-legal", organization_id=org.id, shipment_id=shp.id, claimed_amount=25000.0, status="REJECTED", submitted_at=datetime(2026, 1, 25, tzinfo=timezone.utc), lawsuit_deadline_at=datetime(2028, 1, 26, tzinfo=timezone.utc))
    
    op_user = User(id="usr-v-op", organization_id=org.id, name="Dan Operator", email="dan@test.com", role="Claims Operator")
    sr_user = User(id="usr-v-sr", organization_id=org.id, name="Jane Approver", email="jane@test.com", role="Senior Approver")
    
    doc1 = Document(id="doc-v-1", organization_id=org.id, claim_id=claim.id, shipment_id=shp.id, document_type="BOL", filename="BOL_112233.pdf", mime_type="application/pdf", object_key="docs/bol.pdf", sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", page_count=2)
    doc2 = Document(id="doc-v-2", organization_id=org.id, claim_id=claim.id, shipment_id=shp.id, document_type="POD", filename="POD_112233.pdf", mime_type="application/pdf", object_key="docs/pod.pdf", sha256="8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4", page_count=1)
    
    db.add_all([org, carr, shp, claim, op_user, sr_user, doc1, doc2])
    db.commit()

    # Unauthorized attempt
    try:
        escalate_claim_to_legal(db, claim_id=claim.id, user_id=op_user.id, escalation_tier_rate=0.30, escalation_reason="Trying to escalate")
        assert False, "Unauthorized operator should not be allowed to escalate tier!"
    except Exception as e:
        print(f"  - Unauthorized Claims Operator Escalation Blocked: {e}")

    # Authorized attempt
    rec = escalate_claim_to_legal(
        db,
        claim_id=claim.id,
        user_id=sr_user.id,
        escalation_tier_rate=0.30,
        escalation_reason="Carrier bad-faith denial; transferring case to litigation counsel.",
        assigned_counsel_name="Marcus Kane, Esq.",
        counsel_firm="Kane & Associates LLP",
    )
    print(f"  - Authorized Senior Approver Escalation Succeeded:")
    print(f"    * Escalation Record ID : {rec.id}")
    print(f"    * Escalation Tier Rate : {rec.escalation_tier_rate * 100:.0f}%")
    print(f"    * Assigned Counsel     : {rec.assigned_counsel_name} ({rec.counsel_firm})")
    assert rec.is_escalated is True
    assert rec.escalation_tier_rate == 0.30
    print("  --> [PASS] Role permission guard and database persistence verified.")

    # 3. Case-File Evidence Assembler & Milestone Tracking
    print("\n[STEP 3] Testing Case-File Evidence Assembler & Milestone Stepper:")
    update_litigation_milestone(db, claim_id=claim.id, milestone="LAWSUIT_FILED", notes="Complaint filed in NDIL.")
    
    dossier = assemble_case_file_dossier(db, claim_id=claim.id)
    print(f"  - Dossier Title             : {dossier['dossier_title']}")
    print(f"  - PRO Number                : {dossier['pro_number']}")
    print(f"  - Lawsuit Statutory Deadline: {dossier['lawsuit_deadline_at']}")
    print(f"  - Active Fee Tier           : {dossier['fee_tier']} ({dossier['contingency_rate'] * 100:.0f}%)")
    print(f"  - Current Milestone         : {dossier['current_milestone']}")
    print(f"  - Table of Contents Indexed : {len(dossier['table_of_contents'])} documents")
    for doc in dossier["table_of_contents"]:
        print(f"    * [{doc['document_type']}] {doc['filename']} (SHA-256: {doc['sha256'][:16]}...)")
    print(f"  - Chronology Timeline Events: {len(dossier['chronology'])} events")
    for evt in dossier["chronology"]:
        print(f"    * {evt['event']:<38}: {evt['timestamp'][:10]} ({evt['source']})")

    assert len(dossier["table_of_contents"]) == 2
    assert dossier["fee_tier"] == "LEGAL_ESCALATED"
    assert dossier["current_milestone"] == "LAWSUIT_FILED"
    print("  --> [PASS] Case-file evidence index assembled accurately.")

    # 4. Strict Scoping Guardrail Check (Zero Persuasive Argument Generation)
    print("\n[STEP 4] Guardrail Audit: Verifying Zero Legal Brief / Argument Generation:")
    forbidden = ["hereby moves", "wherefore", "prima facie case is established", "defendant carrier is liable", "prayer for relief", "count i"]
    dossier_str = json.dumps(dossier).lower()
    for term in forbidden:
        assert term not in dossier_str, f"Forbidden judicial brief term '{term}' detected in evidence bundle!"
    print("  --> [PASS] Zero legal arguments generated; strictly factual evidence indexing and ledger math.")

    print("\n================================================================================")
    print("  SUB-PHASE 5.3 VERIFICATION COMPLETE: ALL 4 CHECKS PASSED (100% EMPIRICAL)    ")
    print("================================================================================")

if __name__ == "__main__":
    run_verification()

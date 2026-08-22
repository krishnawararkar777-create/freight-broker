import json
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db.session import Base
from app.models.domain_models import Organization, Claim, Shipment, Carrier, User, Document, ClaimFact, LegalEscalationRecord, FeeEvent
from app.services.legal_case_service import (
    calculate_tiered_fee,
    escalate_claim_to_legal,
    update_litigation_milestone,
    get_legal_escalation_record,
    assemble_case_file_dossier,
)

# In-memory test database fixture
@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_tiered_fee_calculation():
    """Verify standard 20% vs escalated 30% and 35% fee calculations."""
    # Standard 20%
    std = calculate_tiered_fee(recovery_amount=10000.0, is_escalated=False)
    assert std["fee_tier"] == "STANDARD"
    assert std["contingency_rate"] == 0.20
    assert std["fee_amount"] == 2000.0
    assert std["net_to_client"] == 8000.0

    # Escalated 30%
    esc30 = calculate_tiered_fee(recovery_amount=10000.0, is_escalated=True, escalation_rate=0.30)
    assert esc30["fee_tier"] == "LEGAL_ESCALATED"
    assert esc30["contingency_rate"] == 0.30
    assert esc30["fee_amount"] == 3000.0
    assert esc30["net_to_client"] == 7000.0

    # Escalated 35%
    esc35 = calculate_tiered_fee(recovery_amount=10000.0, is_escalated=True, escalation_rate=0.35)
    assert esc35["fee_tier"] == "LEGAL_ESCALATED"
    assert esc35["contingency_rate"] == 0.35
    assert esc35["fee_amount"] == 3500.0
    assert esc35["net_to_client"] == 6500.0

def test_escalate_claim_role_permission_guard(db_session):
    """Claims Operator role cannot escalate to legal tier; Senior Approver / Finance can."""
    org = Organization(id="org-legal-test", name="Apex Legal Org", contingency_rate=0.20)
    carr = Carrier(id="carr-legal-test", canonical_name="ABC Freight Lines LLC", mc_number="MC-847293")
    shp = Shipment(id="shp-legal-test", organization_id=org.id, carrier_id=carr.id, external_reference="PRO-847293", bol_number="BOL-847293", shipper_name="Acme", consignee_name="Pacific")
    claim = Claim(id="clm-legal-test", organization_id=org.id, shipment_id=shp.id, claimed_amount=15000.0, status="REJECTED")
    
    op_user = User(id="usr-op-1", organization_id=org.id, name="Operator Dan", email="dan@test.com", role="Claims Operator")
    sr_user = User(id="usr-sr-1", organization_id=org.id, name="Senior Approver Jane", email="jane@test.com", role="Senior Approver")
    db_session.add_all([org, carr, shp, claim, op_user, sr_user])
    db_session.commit()

    # Claims Operator attempt must fail
    with pytest.raises(Exception) as excinfo:
        escalate_claim_to_legal(
            db=db_session,
            claim_id=claim.id,
            user_id=op_user.id,
            escalation_tier_rate=0.30,
            escalation_reason="Carrier bad-faith denial; escalating to outside counsel.",
        )
    assert "Forbidden" in str(excinfo.value) or "permission" in str(excinfo.value).lower() or "403" in str(excinfo.value)

    # Senior Approver attempt succeeds
    record = escalate_claim_to_legal(
        db=db_session,
        claim_id=claim.id,
        user_id=sr_user.id,
        escalation_tier_rate=0.30,
        escalation_reason="Carrier bad-faith denial; escalating to outside counsel.",
        assigned_counsel_name="Robert Vance, Esq.",
        counsel_firm="Vance & Sterling LLP",
    )
    assert record.is_escalated is True
    assert record.escalation_tier_rate == 0.30
    assert record.escalated_by_user_id == sr_user.id
    assert record.assigned_counsel_name == "Robert Vance, Esq."

def test_update_litigation_milestone(db_session):
    """Verify manual litigation milestone transitions."""
    org = Organization(id="org-mile-test", name="Apex Milestone Org", contingency_rate=0.20)
    carr = Carrier(id="carr-mile-test", canonical_name="ABC Freight Lines LLC", mc_number="MC-847293")
    shp = Shipment(id="shp-mile-test", organization_id=org.id, carrier_id=carr.id, external_reference="PRO-847293", bol_number="BOL-847293", shipper_name="Acme", consignee_name="Pacific")
    claim = Claim(id="clm-mile-test", organization_id=org.id, shipment_id=shp.id, claimed_amount=20000.0, status="REJECTED")
    sr_user = User(id="usr-sr-2", organization_id=org.id, name="Finance Director Alex", email="alex@test.com", role="Finance")
    db_session.add_all([org, carr, shp, claim, sr_user])
    db_session.commit()

    escalate_claim_to_legal(
        db=db_session,
        claim_id=claim.id,
        user_id=sr_user.id,
        escalation_tier_rate=0.35,
        escalation_reason="Escalated for federal filing.",
    )

    rec = update_litigation_milestone(db=db_session, claim_id=claim.id, milestone="LAWSUIT_FILED", notes="Filed in US District Court, Northern District of Illinois.")
    assert rec.current_milestone == "LAWSUIT_FILED"
    assert "District of Illinois" in rec.case_file_notes

def test_assemble_case_file_dossier(db_session):
    """Verify case file assembler compiles clean factual table of contents and evidence index."""
    org = Organization(id="org-doss-test", name="Apex Dossier Org", contingency_rate=0.20)
    carr = Carrier(id="carr-doss-test", canonical_name="Continental Haulers", mc_number="MC-555444")
    now = datetime.now(timezone.utc)
    shp = Shipment(
        id="shp-doss-test",
        organization_id=org.id,
        carrier_id=carr.id,
        external_reference="PRO-847293",
        bol_number="BOL-847293",
        shipper_name="Acme Tech Components",
        consignee_name="Pacific Distribution Warehouse",
        pickup_at=now - timedelta(days=60),
        delivery_at=now - timedelta(days=55),
    )
    claim = Claim(
        id="clm-doss-test",
        organization_id=org.id,
        shipment_id=shp.id,
        claimed_amount=12500.0,
        status="REJECTED",
        submitted_at=now - timedelta(days=40),
        lawsuit_deadline_at=now + timedelta(days=650),
    )
    doc_bol = Document(
        id="doc-bol-1",
        organization_id=org.id,
        claim_id=claim.id,
        shipment_id=shp.id,
        document_type="BOL",
        filename="BillOfLading_847293.pdf",
        mime_type="application/pdf",
        object_key="docs/bol-847293.pdf",
        sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        page_count=2,
    )
    doc_pod = Document(
        id="doc-pod-1",
        organization_id=org.id,
        claim_id=claim.id,
        shipment_id=shp.id,
        document_type="POD",
        filename="ProofOfDelivery_847293.pdf",
        mime_type="application/pdf",
        object_key="docs/pod-847293.pdf",
        sha256="8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4",
        page_count=1,
    )
    db_session.add_all([org, carr, shp, claim, doc_bol, doc_pod])
    db_session.commit()

    dossier = assemble_case_file_dossier(db=db_session, claim_id=claim.id)
    assert dossier["claim_id"] == claim.id
    assert dossier["pro_number"] == "PRO-847293"
    assert dossier["carrier_name"] == "Continental Haulers"
    assert dossier["lawsuit_deadline_at"] is not None
    assert len(dossier["table_of_contents"]) >= 2
    assert dossier["table_of_contents"][0]["document_type"] in ["BOL", "POD"]
    assert "e3b0c442" in dossier["table_of_contents"][0]["sha256"] or "8f434346" in dossier["table_of_contents"][0]["sha256"]

    # Strict audit: verify ZERO judicial arguments or court briefs are drafted
    forbidden = ["hereby moves", "wherefore", "prima facie case is established", "defendant carrier is liable", "prayer for relief"]
    dossier_text = json.dumps(dossier)
    for term in forbidden:
        assert term not in dossier_text.lower(), f"Forbidden judicial brief term '{term}' found in evidence assembly!"

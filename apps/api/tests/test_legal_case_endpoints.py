import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from db.session import get_db, Base
from app.models.domain_models import Organization, Claim, Shipment, Carrier, User, Document

@pytest.fixture
def legal_test_client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    org = Organization(id="org-legal-api", name="Apex Legal API Org", contingency_rate=0.20)
    carr = Carrier(id="carr-legal-api", canonical_name="Swift Lines Inc", mc_number="MC-112233")
    shp = Shipment(
        id="shp-legal-api",
        organization_id=org.id,
        carrier_id=carr.id,
        external_reference="PRO-112233",
        bol_number="BOL-112233",
        shipper_name="Tech Global",
        consignee_name="Retail Hub",
        pickup_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
        delivery_at=datetime(2026, 2, 5, tzinfo=timezone.utc),
    )
    claim = Claim(
        id="clm-legal-api",
        organization_id=org.id,
        shipment_id=shp.id,
        claimed_amount=18000.0,
        status="REJECTED",
        submitted_at=datetime(2026, 2, 10, tzinfo=timezone.utc),
        lawsuit_deadline_at=datetime(2028, 2, 11, tzinfo=timezone.utc),
    )
    user_sr = User(id="usr-sr-legal", organization_id=org.id, name="Sarah Senior", email="sarah@test.com", role="Senior Approver")
    user_op = User(id="usr-op-legal", organization_id=org.id, name="Oliver Operator", email="oliver@test.com", role="Claims Operator")
    doc = Document(
        id="doc-legal-1",
        organization_id=org.id,
        claim_id=claim.id,
        shipment_id=shp.id,
        document_type="BOL",
        filename="BOL_112233.pdf",
        mime_type="application/pdf",
        object_key="docs/bol-112233.pdf",
        sha256="abc123sha256hash",
        page_count=2,
    )
    db.add_all([org, carr, shp, claim, user_sr, user_op, doc])
    db.commit()
    db.close()

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    try:
        yield client
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_calculate_tiered_fee_endpoint(legal_test_client):
    """Verify endpoint computes standard and legal escalation tier fee math."""
    # Standard
    resp = legal_test_client.post("/api/claims/tiered-fee/calculate", json={
        "recovery_amount": 10000.0,
        "is_escalated": False,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["fee_tier"] == "STANDARD"
    assert data["fee_amount"] == 2000.0
    assert data["net_to_client"] == 8000.0

    # Escalated 30%
    resp2 = legal_test_client.post("/api/claims/tiered-fee/calculate", json={
        "recovery_amount": 10000.0,
        "is_escalated": True,
        "escalation_rate": 0.30,
    })
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["fee_tier"] == "LEGAL_ESCALATED"
    assert data2["fee_amount"] == 3000.0
    assert data2["net_to_client"] == 7000.0


def test_escalation_endpoint_role_gating(legal_test_client):
    """Verify Claims Operator is rejected (403), while Senior Approver succeeds."""
    # Unauthorized Operator
    resp_op = legal_test_client.post("/api/claims/clm-legal-api/legal-escalation", json={
        "user_id": "usr-op-legal",
        "escalation_tier_rate": 0.30,
        "escalation_reason": "Operator trying to escalate.",
    })
    assert resp_op.status_code == 403

    # Authorized Senior Approver
    resp_sr = legal_test_client.post("/api/claims/clm-legal-api/legal-escalation", json={
        "user_id": "usr-sr-legal",
        "escalation_tier_rate": 0.35,
        "escalation_reason": "Litigation escalation authorized.",
        "assigned_counsel_name": "Marcus Kane, Esq.",
        "counsel_firm": "Kane Litigation Group",
    })
    assert resp_sr.status_code == 200
    data = resp_sr.json()
    assert data["is_escalated"] is True
    assert data["escalation_tier_rate"] == 0.35
    assert data["assigned_counsel_name"] == "Marcus Kane, Esq."


def test_milestone_and_dossier_endpoints(legal_test_client):
    """Verify milestone updating and case file evidence dossier generation."""
    # Update Milestone
    resp_ms = legal_test_client.post("/api/claims/clm-legal-api/milestones", json={
        "milestone": "LAWSUIT_FILED",
        "notes": "Filed in federal district court.",
    })
    assert resp_ms.status_code == 200
    assert resp_ms.json()["current_milestone"] == "LAWSUIT_FILED"

    # Get Dossier
    resp_dos = legal_test_client.get("/api/claims/clm-legal-api/case-file-dossier")
    assert resp_dos.status_code == 200
    dos = resp_dos.json()
    assert dos["claim_id"] == "clm-legal-api"
    assert dos["pro_number"] == "PRO-112233"
    assert len(dos["table_of_contents"]) >= 1
    assert dos["table_of_contents"][0]["sha256"] == "abc123sha256hash"
    assert dos["evidence_chain_of_custody_verified"] is True

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from db.session import get_db, Base
from app.models.domain_models import Organization, Claim, Shipment, Carrier, CarrierRiskFacts, ClaimFact

@pytest.fixture
def risk_test_client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    org = Organization(id="org-risk-test", name="Apex Risk Test", contingency_rate=0.20)
    carr = Carrier(id="carr-risk-test", canonical_name="ABC Freight Lines LLC", mc_number="MC-847293")
    shp = Shipment(
        id="shp-risk-test",
        organization_id=org.id,
        carrier_id=carr.id,
        external_reference="PRO-847293",
        bol_number="BOL-847293",
        shipper_name="Acme Tech",
        consignee_name="Pacific Dist.",
        pickup_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
    )
    claim = Claim(
        id="clm-risk-test",
        organization_id=org.id,
        shipment_id=shp.id,
        claimed_amount=8000.0,
        status="UNDER_REVIEW",
    )
    fact_bol_carrier = ClaimFact(
        id="cf-1",
        claim_id=claim.id,
        field_name="bol_carrier_name",
        value_json="Shadow Rebroker Logistics Inc",  # Mismatch!
    )
    fact_bol_mc = ClaimFact(
        id="cf-2",
        claim_id=claim.id,
        field_name="bol_carrier_mc",
        value_json="MC-999111",  # Mismatch!
    )
    db.add_all([org, carr, shp, claim, fact_bol_carrier, fact_bol_mc])
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


def test_get_fmcsa_facts_endpoint(risk_test_client):
    """Verify endpoint returns FMCSA SAFER raw facts."""
    resp = risk_test_client.get("/api/carriers/carr-risk-test/fmcsa-facts")
    assert resp.status_code == 200
    data = resp.json()
    assert data["carrier_id"] == "carr-risk-test"
    assert data["authority_status"] == "ACTIVE"
    assert data["bipd_insurance_on_file"] == 1000000.0
    assert data["cargo_policy_active"] is True
    assert data["cargo_form_type"] == "BMC-34"


def test_carrier_anomalies_endpoint_detects_mismatches(risk_test_client):
    """Verify endpoint detects legal name and MC number mismatches against FMCSA/Rate Con."""
    resp = risk_test_client.get("/api/claims/clm-risk-test/carrier-anomalies")
    assert resp.status_code == 200
    data = resp.json()
    assert data["claim_id"] == "clm-risk-test"
    assert data["carrier_id"] == "carr-risk-test"
    assert data["total_anomalies_detected"] >= 2
    
    anomalies = data["anomalies"]
    name_anomaly = next((a for a in anomalies if a["anomaly_type"] == "LEGAL_NAME_MISMATCH"), None)
    assert name_anomaly is not None
    assert "Shadow Rebroker" in name_anomaly["description"]

    mc_anomaly = next((a for a in anomalies if a["anomaly_type"] == "MC_NUMBER_MISMATCH"), None)
    assert mc_anomaly is not None
    assert "MC-999111" in mc_anomaly["description"]

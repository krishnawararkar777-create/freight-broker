import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from db.session import get_db, Base
from app.models.domain_models import Organization, Claim, Shipment, Carrier

@pytest.fixture
def salvage_test_client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    org = Organization(id="org-endpoint-test", name="Apex Test", contingency_rate=0.20)
    carr = Carrier(id="carr-endpoint-test", canonical_name="ABC Trucking", mc_number="MC-999")
    shp = Shipment(
        id="shp-endpoint-test",
        organization_id=org.id,
        carrier_id=carr.id,
        external_reference="PRO-888",
        bol_number="BOL-888",
        shipper_name="Acme",
        consignee_name="Pacific",
    )
    claim = Claim(
        id="clm-endpoint-test",
        organization_id=org.id,
        shipment_id=shp.id,
        claimed_amount=20000.0,
        status="DRAFT",
    )
    db.add_all([org, carr, shp, claim])
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


def test_salvage_calculate_endpoint(salvage_test_client):
    """Verify dynamic salvage calculate preview endpoint."""
    payload = {
        "gross_invoice_value": 15000.0,
        "commodity_category": "ELECTRONICS",
        "damage_severity_score": 0.40,
    }
    # Electronics base 25%, severity 0.40 -> effective rate = 0.25 * (1 - 0.40) = 0.15
    # Estimated salvage = 15,000 * 0.15 = 2,250.00
    # Net claim = 15,000 - 2,250 = 12,750.00
    resp = salvage_test_client.post("/api/claims/salvage/calculate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["gross_invoice_value"] == 15000.0
    assert data["salvage_rate"] == 0.15
    assert data["estimated_salvage_value"] == 2250.0
    assert data["net_claimed_amount"] == 12750.0


def test_salvage_crud_and_mitigation_document_endpoints(salvage_test_client):
    """Verify saving a salvage record updates claim demand and returns mitigation proof doc."""
    claim_id = "clm-endpoint-test"

    # 1. Post Salvage Record
    post_payload = {
        "gross_invoice_value": 20000.0,
        "commodity_category": "METALS_MACHINERY",
        "damage_severity_score": 0.50,  # Metals base 40%, severity 0.50 -> effective rate 0.20 -> salvage $4,000 -> net $16,000
        "disposition_status": "RETAINED_FOR_SALVAGE",
        "storage_location": "Bay 12 South Yard",
        "notes": "Machinery crated and protected from corrosion.",
    }
    resp_post = salvage_test_client.post(f"/api/claims/{claim_id}/salvage", json=post_payload)
    assert resp_post.status_code == 200
    post_data = resp_post.json()
    assert post_data["net_claimed_amount"] == 16000.0
    assert post_data["disposition_status"] == "RETAINED_FOR_SALVAGE"

    # 2. Get Salvage Record
    resp_get = salvage_test_client.get(f"/api/claims/{claim_id}/salvage")
    assert resp_get.status_code == 200
    get_data = resp_get.json()
    assert get_data["net_claimed_amount"] == 16000.0
    assert get_data["storage_location"] == "Bay 12 South Yard"

    # 3. Get Factual Mitigation Document
    resp_doc = salvage_test_client.get(f"/api/claims/{claim_id}/salvage/mitigation-doc")
    assert resp_doc.status_code == 200
    doc_data = resp_doc.json()
    assert doc_data["mitigation_status"] == "DUTY_SATISFIED"
    assert doc_data["net_claimed_amount"] == 16000.0
    assert "Factual Record of Cargo Loss Mitigation" in doc_data["document_title"]
    assert "Bay 12 South Yard" in doc_data["factual_certification"]

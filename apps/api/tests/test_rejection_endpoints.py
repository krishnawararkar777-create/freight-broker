import os
import sys
import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db.session import Base, get_db
from app.models.domain_models import Claim, Shipment, Carrier, CarrierResponse, Communication
from main import app


@pytest.fixture
def rejection_test_client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()
    now = datetime.datetime.now(datetime.timezone.utc)

    carr = Carrier(id="carr-101", canonical_name="ABC Trucking", mc_number="MC-123456", active=True)
    ship = Shipment(
        id="ship-101",
        organization_id="org-apex-001",
        external_reference="PRO-847293",
        bol_number="BOL-847293",
        carrier_id="carr-101",
    )
    clm = Claim(
        id="clm-847293",
        organization_id="org-apex-001",
        shipment_id="ship-101",
        claim_type="Cargo Damage",
        status="REJECTED",
        claimed_amount=8000.0,
        submitted_at=now - datetime.timedelta(days=10),
    )
    resp = CarrierResponse(
        id="resp-101",
        claim_id="clm-847293",
        document_id="doc-101",
        decision_type="DENIAL",
        offer_amount=0.0,
        disputed_amount=8000.0,
        denial_reasons_json={"reasons": ["improper_packaging"], "primary_category": "CARMACK_STATUTORY_EXCEPTION"},
        created_at=now - datetime.timedelta(days=2),
    )
    db.add_all([carr, ship, clm, resp])
    db.commit()
    db.close()

    def override_get_db():
        db_session = TestingSessionLocal()
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_get_rejection_analytics_endpoint(rejection_test_client):
    """Verifies GET /api/telemetry/rejections returns category & subcode taxonomy metrics."""
    response = rejection_test_client.get("/api/telemetry/rejections")
    assert response.status_code == 200
    data = response.json()

    assert "total_denials" in data
    assert data["total_denials"] >= 1
    assert "category_distribution" in data
    assert "subcode_distribution" in data
    assert "carrier_denial_matrix" in data
    assert len(data["carrier_denial_matrix"]) >= 1


def test_get_carrier_profiles_endpoint(rejection_test_client):
    """Verifies GET /api/telemetry/carrier-profiles returns carrier performance scorecards."""
    response = rejection_test_client.get("/api/telemetry/carrier-profiles")
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1
    profile = data[0]
    assert profile["carrier_id"] == "carr-101"
    assert profile["carrier_name"] == "ABC Trucking"
    assert "acceptance_rate_pct" in profile
    assert "denial_rate_pct" in profile
    assert "time_to_initial_response_days" in profile
    assert "denial_tactic_distribution" in profile


def test_get_single_carrier_profile_endpoint(rejection_test_client):
    """Verifies GET /api/telemetry/carrier-profiles/{carrier_id} returns individual carrier profile."""
    response = rejection_test_client.get("/api/telemetry/carrier-profiles/carr-101")
    assert response.status_code == 200
    data = response.json()

    assert data["carrier_id"] == "carr-101"
    assert data["carrier_name"] == "ABC Trucking"


def test_recommend_rebuttal_post_endpoint(rejection_test_client):
    """Verifies POST /api/claims/{claim_id}/rebuttal/recommend creates grounded rebuttal draft."""
    payload = {
        "denial_text": "We decline this claim under Tariff Rule 100 released rate limitations of $0.50/lb."
    }
    response = rejection_test_client.post("/api/claims/clm-847293/rebuttal/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "communication_id" in data
    assert "Hughes v. United Van Lines" in data["governing_citation"]
    assert data["rebuttal_strategy"] == "RELEASED_VALUE_CHALLENGE"
    assert data["draft_status"] == "DRAFT"

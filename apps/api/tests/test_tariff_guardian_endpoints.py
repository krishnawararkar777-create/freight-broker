import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from db.session import get_db, Base
from app.models.domain_models import Organization, Claim, Shipment, Carrier, CarrierContractClause

@pytest.fixture
def tg_test_client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    org = Organization(id="org-tg-api", name="Apex Tariff API Org", contingency_rate=0.20)
    carr = Carrier(id="carr-tg-api", canonical_name="Falcon Freight Express", mc_number="MC-999222")
    now = datetime.now(timezone.utc)
    shp = Shipment(
        id="shp-tg-api",
        organization_id=org.id,
        carrier_id=carr.id,
        external_reference="PRO-999222",
        bol_number="BOL-999222",
        delivery_at=now - timedelta(days=20),
    )
    claim = Claim(
        id="clm-tg-api",
        organization_id=org.id,
        shipment_id=shp.id,
        claimed_amount=14000.0,
        status="UNDER_REVIEW",
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


def test_create_and_list_carrier_contracts_endpoint(tg_test_client):
    """Verify adding custom contract limitation clause and retrieving contract list."""
    resp = tg_test_client.post("/api/carriers/carr-tg-api/contracts", json={
        "organization_id": "org-tg-api",
        "contract_type": "BROKER_CARRIER_MSA",
        "contract_reference": "MSA-2026-FALCON-SEC9",
        "filing_window_days": 90,
        "concealed_notice_days": 10,
        "lawsuit_window_days": 365,
        "released_rate_cap_per_lb": 2.50,
        "supersedes_carrier_tariff": True,
        "clause_text_excerpt": "Claims must be asserted within 90 days of cargo delivery.",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["contract_reference"] == "MSA-2026-FALCON-SEC9"
    assert data["filing_window_days"] == 90
    assert data["released_rate_cap_per_lb"] == 2.50

    # List contracts
    list_resp = tg_test_client.get("/api/carriers/carr-tg-api/contracts")
    assert list_resp.status_code == 200
    clauses = list_resp.json()
    assert len(clauses) >= 1
    assert clauses[0]["contract_reference"] == "MSA-2026-FALCON-SEC9"


def test_get_claim_governing_deadlines_endpoint(tg_test_client):
    """Verify endpoint computes deterministic min() deadline report for claim."""
    # First ingest a 90-day MSA contract
    tg_test_client.post("/api/carriers/carr-tg-api/contracts", json={
        "organization_id": "org-tg-api",
        "contract_type": "BROKER_CARRIER_MSA",
        "contract_reference": "MSA-FALCON-2026",
        "filing_window_days": 90,
        "concealed_notice_days": 10,
        "supersedes_carrier_tariff": True,
    })

    resp = tg_test_client.get("/api/claims/clm-tg-api/governing-deadlines")
    assert resp.status_code == 200
    report = resp.json()
    assert report["claim_id"] == "clm-tg-api"
    assert report["filing_governing_source"] == "BROKER_CARRIER_MSA"
    assert report["filing_window_days"] == 90
    assert report["governing_contract_reference"] == "MSA-FALCON-2026"
    assert report["concealed_notice_days"] == 10
    assert report["urgency_status"] in ["ON_SCHEDULE", "URGENT_DEADLINE_APPROACHING"]
    assert len(report["all_active_clauses"]) >= 1

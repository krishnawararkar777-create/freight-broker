import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db.session import Base
from app.models.domain_models import Organization, Claim, Shipment, SalvageRecord, Document
from app.models.domain_models import Organization, Claim, Shipment, Carrier, SalvageRecord, Document
from app.services.salvage_service import (
    calculate_salvage_valuation,
    save_or_update_salvage_record,
    get_salvage_record,
    generate_mitigation_document,
    COMMODITY_BASE_SALVAGE_RATES,
)

# In-memory test database setup
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

def test_commodity_base_rates():
    """Verify standard commodity baseline recovery rates."""
    assert COMMODITY_BASE_SALVAGE_RATES["METALS_MACHINERY"] == 0.40
    assert COMMODITY_BASE_SALVAGE_RATES["ELECTRONICS"] == 0.25
    assert COMMODITY_BASE_SALVAGE_RATES["DRY_GOODS"] == 0.15
    assert COMMODITY_BASE_SALVAGE_RATES["PERISHABLES_FOOD"] == 0.00
    assert COMMODITY_BASE_SALVAGE_RATES["PHARMACEUTICALS"] == 0.00
    assert COMMODITY_BASE_SALVAGE_RATES["GENERAL_MERCHANDISE"] == 0.10

def test_salvage_calculation_estimated_electronics():
    """
    Test estimation: Gross loss $10,000, Electronics (base 25%), Severity 0.20 (20% damaged / 80% sound).
    Effective rate = 0.25 * (1 - 0.20) = 0.20 (20% salvage value)
    Estimated salvage value = $2,000.00
    Net Claim Demand = $10,000.00 - $2,000.00 = $8,000.00
    """
    res = calculate_salvage_valuation(
        gross_invoice_value=10000.0,
        commodity_category="ELECTRONICS",
        damage_severity_score=0.20,
    )
    assert res.gross_invoice_value == 10000.0
    assert res.commodity_category == "ELECTRONICS"
    assert res.salvage_rate == 0.20
    assert res.estimated_salvage_value == 2000.0
    assert res.realized_salvage_value is None
    assert res.net_claimed_amount == 8000.0

def test_salvage_calculation_perishables_zero_salvage():
    """
    Food / Pharma losses must yield 0% salvage due to mandatory health destruction regulations.
    Gross loss $5,400 -> Salvage $0.00 -> Net Claim $5,400.00
    """
    res = calculate_salvage_valuation(
        gross_invoice_value=5400.0,
        commodity_category="PERISHABLES_FOOD",
        damage_severity_score=0.50,
    )
    assert res.salvage_rate == 0.0
    assert res.estimated_salvage_value == 0.0
    assert res.net_claimed_amount == 5400.0

def test_salvage_calculation_realized_value_override():
    """
    When actual salvage sale proceeds are realized, the realized amount overrides the estimate.
    Gross loss $12,000, Metals (estimate would be $2,400), but consignee sold salvage for $3,150.
    Net Claim Demand = $12,000 - $3,150 = $8,850.00
    """
    res = calculate_salvage_valuation(
        gross_invoice_value=12000.0,
        commodity_category="METALS_MACHINERY",
        damage_severity_score=0.50,
        realized_salvage_value=3150.0,
    )
    assert res.estimated_salvage_value == 2400.0
    assert res.realized_salvage_value == 3150.0
    assert res.net_claimed_amount == 8850.0

def test_salvage_calculation_zero_floor_clamp():
    """Net claimed demand must never be negative even if salvage exceeds gross value."""
    res = calculate_salvage_valuation(
        gross_invoice_value=1000.0,
        commodity_category="METALS_MACHINERY",
        damage_severity_score=0.0,
        realized_salvage_value=1500.0,
    )
    assert res.net_claimed_amount == 0.0

def test_db_salvage_record_save_and_claim_update(db_session):
    """Saving a salvage record must update claim.claimed_amount with net demand."""
    org = Organization(id="org-test", name="Test Org", contingency_rate=0.20)
    carr = Carrier(id="carr-test-1", canonical_name="ABC Trucking", mc_number="MC-111")
    shp = Shipment(id="shp-test-1", organization_id=org.id, carrier_id=carr.id, external_reference="PRO-101", bol_number="BOL-101", shipper_name="Acme", consignee_name="Pacific")
    claim = Claim(id="clm-salvage-1", organization_id=org.id, shipment_id=shp.id, claimed_amount=10000.0, status="DRAFT")
    db_session.add_all([org, carr, shp, claim])
    db_session.commit()

    record = save_or_update_salvage_record(
        db=db_session,
        claim_id="clm-salvage-1",
        organization_id="org-test",
        gross_invoice_value=10000.0,
        commodity_category="ELECTRONICS",
        damage_severity_score=0.20,
        disposition_status="RETAINED_FOR_SALVAGE",
        storage_location="Warehouse Bay 4, Chicago IL",
        notes="Pallet retained in original wrap for carrier inspection.",
    )
    assert record.id is not None
    assert record.net_claimed_amount == 8000.0
    assert record.disposition_status == "RETAINED_FOR_SALVAGE"
    assert record.storage_location == "Warehouse Bay 4, Chicago IL"

    # Verify claim.claimed_amount updated to net demand
    db_session.refresh(claim)
    assert claim.claimed_amount == 8000.0

def test_generate_mitigation_document(db_session):
    """Verify generation of factual mitigation proof document."""
    org = Organization(id="org-test-2", name="Apex Brokers")
    carr = Carrier(id="carr-test-2", canonical_name="ABC Trucking", mc_number="MC-222")
    shp = Shipment(id="shp-test-2", organization_id=org.id, carrier_id=carr.id, external_reference="PRO-102", bol_number="BOL-102", shipper_name="Acme", consignee_name="Pacific")
    claim = Claim(id="clm-mitigation-1", organization_id=org.id, shipment_id=shp.id, claimed_amount=6000.0, status="UNDER_REVIEW")
    db_session.add_all([org, carr, shp, claim])
    db_session.commit()

    save_or_update_salvage_record(
        db=db_session,
        claim_id="clm-mitigation-1",
        organization_id="org-test-2",
        gross_invoice_value=6000.0,
        commodity_category="DRY_GOODS",
        damage_severity_score=0.40,
        disposition_status="RETAINED_FOR_SALVAGE",
        storage_location="Facility D Dock 12",
        notes="Cargo segregated and protected from weather elements.",
    )

    doc = generate_mitigation_document(db=db_session, claim_id="clm-mitigation-1")
    assert doc["claim_id"] == "clm-mitigation-1"
    assert doc["mitigation_status"] == "DUTY_SATISFIED"
    assert doc["commodity_category"] == "DRY_GOODS"
    assert doc["gross_invoice_value"] == 6000.0
    assert doc["salvage_offset"] == 540.0 # 6000 * 0.15 * (1 - 0.4) = 540.0
    assert doc["net_claimed_amount"] == 5460.0 # 6000 - 540 = 5460.0
    assert doc["storage_location"] == "Facility D Dock 12"
    assert "Factual Record of Cargo Loss Mitigation" in doc["document_title"]

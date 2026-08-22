import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db.session import Base
from app.models.domain_models import Organization, Claim, Shipment, Carrier, CarrierRiskFacts
from app.services.carrier_risk_service import (
    normalize_entity_name,
    detect_carrier_anomalies,
    sync_or_get_carrier_risk_facts,
    CarrierAnomalyFlag,
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

def test_normalize_entity_name():
    """Verify corporate suffixes and noise are cleanly stripped for accurate comparison."""
    assert normalize_entity_name("ABC Freight Lines, LLC.") == "ABC FREIGHT LINES"
    assert normalize_entity_name("ABC Freight Lines Inc") == "ABC FREIGHT LINES"
    assert normalize_entity_name("Swift Transportation Co., Inc.") == "SWIFT TRANSPORTATION"
    assert normalize_entity_name("Rapid Logistics Ltd.") == "RAPID LOGISTICS"

def test_clean_carrier_no_anomalies():
    """When Rate Con, BOL, POD, and FMCSA all match and insurance is active, 0 anomalies are flagged."""
    fmcsa = CarrierRiskFacts(
        id="crf-1",
        carrier_id="carr-1",
        dot_number="1234567",
        mc_number="MC-123456",
        legal_name="ABC Freight Lines LLC",
        authority_status="ACTIVE",
        bipd_insurance_on_file=1000000.0,
        cargo_insurance_on_file=100000.0,
        cargo_policy_active=True,
    )
    anomalies = detect_carrier_anomalies(
        rate_con_carrier="ABC Freight Lines LLC",
        bol_carrier="ABC Freight Lines, Inc.",
        pod_carrier="ABC Freight Lines",
        rate_con_mc="MC-123456",
        bol_mc="MC-123456",
        fmcsa_facts=fmcsa,
        pickup_date=datetime(2026, 3, 15, tzinfo=timezone.utc),
    )
    assert len(anomalies) == 0

def test_name_mismatch_double_brokering_anomaly():
    """Flag legal name mismatch between contracted carrier and BOL/POD carrier."""
    fmcsa = CarrierRiskFacts(
        id="crf-2",
        carrier_id="carr-2",
        dot_number="1234567",
        mc_number="MC-123456",
        legal_name="Apex Global Express LLC",
        authority_status="ACTIVE",
        bipd_insurance_on_file=1000000.0,
        cargo_insurance_on_file=100000.0,
        cargo_policy_active=True,
    )
    anomalies = detect_carrier_anomalies(
        rate_con_carrier="Apex Global Express LLC",
        bol_carrier="Shadow Trucking LLC",
        pod_carrier="Shadow Trucking LLC",
        rate_con_mc="MC-123456",
        bol_mc=None,
        fmcsa_facts=fmcsa,
    )
    assert len(anomalies) >= 1
    flag = next((a for a in anomalies if a.anomaly_type == "LEGAL_NAME_MISMATCH"), None)
    assert flag is not None
    assert "Shadow Trucking" in flag.description
    assert "Apex Global Express" in flag.description
    assert flag.severity == "WARNING"

def test_mc_number_mismatch():
    """Flag discrepancy when MC number on document does not match Rate Con / FMCSA record."""
    fmcsa = CarrierRiskFacts(
        id="crf-3",
        carrier_id="carr-3",
        dot_number="1234567",
        mc_number="MC-888999",
        legal_name="Continental Haulers Inc",
        authority_status="ACTIVE",
        bipd_insurance_on_file=1000000.0,
        cargo_insurance_on_file=100000.0,
        cargo_policy_active=True,
    )
    anomalies = detect_carrier_anomalies(
        rate_con_carrier="Continental Haulers Inc",
        bol_carrier="Continental Haulers Inc",
        rate_con_mc="MC-888999",
        bol_mc="MC-111222", # Different MC on BOL
        fmcsa_facts=fmcsa,
    )
    flag = next((a for a in anomalies if a.anomaly_type == "MC_NUMBER_MISMATCH"), None)
    assert flag is not None
    assert "MC-111222" in flag.description
    assert "MC-888999" in flag.description

def test_insurance_lapsed_prior_to_pickup():
    """Pre-submission warning when insurance was cancelled before shipment pickup date."""
    fmcsa = CarrierRiskFacts(
        id="crf-4",
        carrier_id="carr-4",
        dot_number="1234567",
        mc_number="MC-555444",
        legal_name="Fastlane Freight LLC",
        authority_status="ACTIVE",
        cargo_policy_active=False,
        insurance_cancellation_date=datetime(2026, 2, 1, tzinfo=timezone.utc),
    )
    anomalies = detect_carrier_anomalies(
        rate_con_carrier="Fastlane Freight LLC",
        rate_con_mc="MC-555444",
        fmcsa_facts=fmcsa,
        pickup_date=datetime(2026, 2, 15, tzinfo=timezone.utc), # Picked up after cancellation
    )
    flag = next((a for a in anomalies if a.anomaly_type == "INSURANCE_STATUS_WARNING"), None)
    assert flag is not None
    assert "cancelled" in flag.description.lower() or "inactive" in flag.description.lower()

def test_revoked_operating_authority():
    """Flag when carrier operating authority is REVOKED or INACTIVE."""
    fmcsa = CarrierRiskFacts(
        id="crf-5",
        carrier_id="carr-5",
        dot_number="999888",
        mc_number="MC-999888",
        legal_name="Outlaw Transport Inc",
        authority_status="REVOKED",
        cargo_policy_active=True,
    )
    anomalies = detect_carrier_anomalies(
        rate_con_carrier="Outlaw Transport Inc",
        rate_con_mc="MC-999888",
        fmcsa_facts=fmcsa,
    )
    flag = next((a for a in anomalies if a.anomaly_type == "AUTHORITY_INACTIVE_WARNING"), None)
    assert flag is not None
    assert "REVOKED" in flag.description

def test_sync_or_get_carrier_risk_facts(db_session):
    """Verify caching and database query of CarrierRiskFacts."""
    carr = Carrier(id="carr-sync-1", canonical_name="Prime Express Logistics", mc_number="MC-777666")
    db_session.add(carr)
    db_session.commit()

    facts = sync_or_get_carrier_risk_facts(db=db_session, carrier_id=carr.id, force_refresh=True)
    assert facts.carrier_id == carr.id
    assert facts.mc_number == "MC-777666"
    assert facts.authority_status == "ACTIVE"
    assert facts.bipd_insurance_on_file == 1000000.0
    assert facts.cargo_form_type == "BMC-34"

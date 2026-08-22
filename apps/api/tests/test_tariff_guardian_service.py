import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db.session import Base
from app.models.domain_models import Organization, Claim, Shipment, Carrier, CarrierContractClause
from app.services.tariff_guardian_service import (
    compute_governing_deadlines,
    save_carrier_contract_clause,
    get_carrier_contract_clauses,
    GoverningDeadlineReport,
)

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

def test_carmack_statutory_baseline_deadlines(db_session):
    """When no contract clauses exist, system computes standard Carmack statutory deadlines."""
    now = datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc)
    org = Organization(id="org-tg-1", name="Apex Guardian Org", contingency_rate=0.20)
    carr = Carrier(id="carr-tg-1", canonical_name="Standard Carrier LLC", mc_number="MC-111000")
    shp = Shipment(
        id="shp-tg-1",
        organization_id=org.id,
        carrier_id=carr.id,
        external_reference="PRO-111000",
        bol_number="BOL-111000",
        delivery_at=now,
    )
    claim = Claim(
        id="clm-tg-1",
        organization_id=org.id,
        shipment_id=shp.id,
        claimed_amount=5000.0,
        status="UNDER_REVIEW",
    )
    db_session.add_all([org, carr, shp, claim])
    db_session.commit()

    report = compute_governing_deadlines(db_session, claim_id=claim.id, current_time=now)
    assert report.filing_governing_source == "CARMACK_STATUTORY_DEFAULT"
    assert report.filing_window_days == 270
    assert report.governing_filing_deadline == now + timedelta(days=270)
    assert report.concealed_notice_days == 5
    assert report.urgency_status == "ON_SCHEDULE"

def test_msa_shortened_filing_window_override(db_session):
    """Signed Broker-Carrier MSA with 60-day filing window overrides 270-day Carmack baseline."""
    now = datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc)
    org = Organization(id="org-tg-2", name="Apex Guardian Org 2", contingency_rate=0.20)
    carr = Carrier(id="carr-tg-2", canonical_name="Fastlane Freight LLC", mc_number="MC-222000")
    shp = Shipment(
        id="shp-tg-2",
        organization_id=org.id,
        carrier_id=carr.id,
        external_reference="PRO-222000",
        bol_number="BOL-222000",
        delivery_at=now,
    )
    claim = Claim(
        id="clm-tg-2",
        organization_id=org.id,
        shipment_id=shp.id,
        claimed_amount=8000.0,
        status="UNDER_REVIEW",
    )
    clause = CarrierContractClause(
        id="clause-1",
        carrier_id=carr.id,
        organization_id=org.id,
        contract_type="BROKER_CARRIER_MSA",
        contract_reference="MSA-2025-FASTLANE-SEC4",
        filing_window_days=60,
        concealed_notice_days=15,
        lawsuit_window_days=365,
        supersedes_carrier_tariff=True,
        clause_text_excerpt="All cargo claims must be formally submitted in writing within 60 calendar days of delivery.",
    )
    db_session.add_all([org, carr, shp, claim, clause])
    db_session.commit()

    report = compute_governing_deadlines(db_session, claim_id=claim.id, current_time=now)
    assert report.filing_governing_source == "BROKER_CARRIER_MSA"
    assert report.governing_contract_reference == "MSA-2025-FASTLANE-SEC4"
    assert report.filing_window_days == 60
    assert report.governing_filing_deadline == now + timedelta(days=60)
    assert report.lawsuit_window_days == 365
    assert report.concealed_notice_days == 15

def test_hierarchy_contract_supersedes_tariff(db_session):
    """When MSA has supersedes_carrier_tariff=True, it prevails over carrier tariff rules."""
    now = datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc)
    org = Organization(id="org-tg-3", name="Apex Guardian Org 3", contingency_rate=0.20)
    carr = Carrier(id="carr-tg-3", canonical_name="Omni Logistics Inc", mc_number="MC-333000")
    shp = Shipment(
        id="shp-tg-3",
        organization_id=org.id,
        carrier_id=carr.id,
        external_reference="PRO-333000",
        bol_number="BOL-333000",
        delivery_at=now,
    )
    claim = Claim(
        id="clm-tg-3",
        organization_id=org.id,
        shipment_id=shp.id,
        claimed_amount=12000.0,
        status="UNDER_REVIEW",
    )
    # Carrier Tariff says 90 days
    tariff = CarrierContractClause(
        id="clause-tariff-1",
        carrier_id=carr.id,
        organization_id=org.id,
        contract_type="CARRIER_RULES_TARIFF",
        contract_reference="Tariff 100-F",
        filing_window_days=90,
        supersedes_carrier_tariff=False,
    )
    # Broker MSA says 120 days and supersedes tariff
    msa = CarrierContractClause(
        id="clause-msa-1",
        carrier_id=carr.id,
        organization_id=org.id,
        contract_type="BROKER_CARRIER_MSA",
        contract_reference="Broker-Carrier MSA 2026",
        filing_window_days=120,
        supersedes_carrier_tariff=True,
    )
    db_session.add_all([org, carr, shp, claim, tariff, msa])
    db_session.commit()

    report = compute_governing_deadlines(db_session, claim_id=claim.id, current_time=now)
    assert report.filing_governing_source == "BROKER_CARRIER_MSA"
    assert report.filing_window_days == 120
    assert report.governing_contract_reference == "Broker-Carrier MSA 2026"

def test_deadline_urgency_and_time_bar_status(db_session):
    """Verify urgency flags when deadline is approaching (<14 days) or expired."""
    now = datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc)
    org = Organization(id="org-tg-4", name="Apex Guardian Org 4", contingency_rate=0.20)
    carr = Carrier(id="carr-tg-4", canonical_name="Swift Haulers", mc_number="MC-444000")
    
    # Urgent claim: delivered 50 days ago under 60-day window (10 days remaining)
    shp_urgent = Shipment(
        id="shp-tg-urgent",
        organization_id=org.id,
        carrier_id=carr.id,
        external_reference="PRO-URGENT",
        bol_number="BOL-URGENT",
        delivery_at=now - timedelta(days=50),
    )
    claim_urgent = Claim(
        id="clm-tg-urgent",
        organization_id=org.id,
        shipment_id=shp_urgent.id,
        claimed_amount=6000.0,
        status="UNDER_REVIEW",
    )
    clause = CarrierContractClause(
        id="clause-urgent",
        carrier_id=carr.id,
        organization_id=org.id,
        contract_type="BROKER_CARRIER_MSA",
        contract_reference="MSA-60-DAY",
        filing_window_days=60,
    )
    db_session.add_all([org, carr, shp_urgent, claim_urgent, clause])
    db_session.commit()

    report_urgent = compute_governing_deadlines(db_session, claim_id=claim_urgent.id, current_time=now)
    assert report_urgent.urgency_status == "URGENT_DEADLINE_APPROACHING"
    assert report_urgent.days_remaining == 10

    # Barred claim: delivered 65 days ago under 60-day window (-5 days)
    shp_barred = Shipment(
        id="shp-tg-barred",
        organization_id=org.id,
        carrier_id=carr.id,
        external_reference="PRO-BARRED",
        bol_number="BOL-BARRED",
        delivery_at=now - timedelta(days=65),
    )
    claim_barred = Claim(
        id="clm-tg-barred",
        organization_id=org.id,
        shipment_id=shp_barred.id,
        claimed_amount=6000.0,
        status="UNDER_REVIEW",
    )
    db_session.add_all([shp_barred, claim_barred])
    db_session.commit()

    report_barred = compute_governing_deadlines(db_session, claim_id=claim_barred.id, current_time=now)
    assert report_barred.urgency_status == "TIME_BARRED_BY_LIMITATION"
    assert report_barred.days_remaining < 0

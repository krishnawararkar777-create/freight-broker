import os
import sys
import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db.session import Base
from app.models.domain_models import Claim, Shipment, Carrier, CarrierResponse, RecoveryEvent
from app.schemas.rejection_taxonomy import RejectionCategory, RejectionSubCode
from app.services.denial_intelligence_service import DenialIntelligenceService


@pytest.fixture
def denial_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()


def test_classify_procedural_timing_concealed_damage():
    """Verifies classification of 5-day concealed damage notice denial."""
    letter = """
    ABC Trucking Claims Department
    RE: Claim CLM-847293 (PRO# PRO-847293)
    
    We have reviewed your cargo claim. We must decline this claim because notice of concealed 
    loss or damage was reported 12 calendar days following delivery. Under Item 450 of our published 
    freight rules tariff, all concealed damage claims must be filed within 5 business days of delivery.
    Your late notice prevents investigation.
    """
    service = DenialIntelligenceService()
    res = service.classify_denial_letter(letter)

    assert res.primary_category == RejectionCategory.PROCEDURAL_TIMING
    assert res.primary_sub_code == RejectionSubCode.MISSED_CONCEALED_DAMAGE_WINDOW
    assert res.confidence >= 0.85
    assert res.requires_human_adjudication is False
    assert "49 U.S.C. § 14706(e)(1)" in res.governing_citation


def test_classify_documentation_deficiency_clean_pod():
    """Verifies classification of Clean POD denial."""
    letter = """
    Midwest Freight Co. Claims Resolution
    Subject: Cargo Claim Disallowance - PRO 99281
    
    Please be advised that the delivery receipt (POD) was signed clean without any exception notations 
    or damage remarks by the consignee receiving dock. Under standard freight classification rules, 
    a clean delivery receipt establishes good-order delivery. We cannot accept liability.
    """
    service = DenialIntelligenceService()
    res = service.classify_denial_letter(letter)

    assert res.primary_category == RejectionCategory.DOCUMENTATION_DEFICIENCY
    assert res.primary_sub_code == RejectionSubCode.CLEAN_POD_NO_EXCEPTION
    assert res.confidence >= 0.85
    assert res.requires_human_adjudication is False


def test_classify_carmack_statutory_packaging_defense():
    """Verifies classification of improper packaging / act of shipper defense."""
    letter = """
    Swift Line Logistics Claims Dept.
    Re: Claim Ref # CLM-5521
    
    Our investigation and driver report indicate that this cargo suffered from improper packaging, 
    insufficient shrink-wrapping, and inadequate internal cushioning on the pallets. Under the Carmack 
    Amendment statutory exceptions (Act or default of the Shipper), carrier is not liable for damage 
    caused by packaging deficiencies.
    """
    service = DenialIntelligenceService()
    res = service.classify_denial_letter(letter)

    assert res.primary_category == RejectionCategory.CARMACK_STATUTORY_EXCEPTION
    assert res.primary_sub_code == RejectionSubCode.ACT_OF_SHIPPER_PACKAGING
    assert res.confidence >= 0.85
    assert "Elmore & Stahl" in res.governing_citation


def test_classify_salvage_discarded_cargo():
    """Verifies classification of discarded salvage freight defense."""
    letter = """
    ABC Trucking Claims Management
    Claim Decision: DENIED
    
    Upon scheduling an on-site survey, our adjuster was notified that the consignee had discarded and destroyed 
    the damaged goods before carrier inspection could take place. This constitutes a failure to protect salvage 
    and mitigate damages under 49 CFR § 370.9. Carrier liability is fully extinguished.
    """
    service = DenialIntelligenceService()
    res = service.classify_denial_letter(letter)

    assert res.primary_category == RejectionCategory.SALVAGE_MITIGATION
    assert res.primary_sub_code == RejectionSubCode.CARGO_DISCARDED_BEFORE_INSPECTION
    assert res.confidence >= 0.85


def test_classify_coverage_tariff_released_value_limitation():
    """Verifies classification of $0.50/lb released rate limitation."""
    letter = """
    Midwest Freight Co. Settlement Response
    PRO Reference: PRO-77120
    
    We acknowledge damage to 200 lbs of freight. However, pursuant to Tariff Rule 100-A, linehaul 
    rates were tendered under a released valuation rate limiting carrier liability to $0.50 per pound. 
    Our maximum settlement liability is therefore capped at $100.00.
    """
    service = DenialIntelligenceService()
    res = service.classify_denial_letter(letter)

    assert res.primary_category == RejectionCategory.COVERAGE_TARIFF_LIMITATION
    assert res.primary_sub_code == RejectionSubCode.RELEASED_VALUE_RATES_CAP
    assert res.confidence >= 0.85
    assert "Hughes v. United Van Lines" in res.governing_citation


def test_classify_compound_ambiguous_denial_triggers_human_adjudication():
    """Verifies that compound multiple-ground letters trigger requires_human_adjudication."""
    compound_letter = """
    ABC Trucking Final Denial Notice
    Claim # CLM-3391
    
    We are denying this claim on two separate grounds:
    First, the delivery receipt was signed clean with no damage exception noted at time of drop.
    Second, the consignee discarded all damaged freight prior to adjuster arrival, failing to protect salvage.
    """
    service = DenialIntelligenceService()
    res = service.classify_denial_letter(compound_letter)

    # Must detect compound nature
    assert len(res.secondary_categories) >= 1 or res.requires_human_adjudication is True
    assert res.requires_human_adjudication is True


def test_carrier_behavior_profiling(denial_db):
    """Verifies historical carrier performance aggregation (acceptance, denial, TTIR, TTS, tactics)."""
    now = datetime.datetime.now(datetime.timezone.utc)

    # Seed Carrier
    c = Carrier(
        id="carr-101",
        canonical_name="ABC Trucking",
        mc_number="MC-123456",
        active=True
    )
    denial_db.add(c)

    # Seed 4 claims for this carrier
    for idx in range(1, 5):
        s = Shipment(
            id=f"ship-{idx}",
            organization_id="org-apex-001",
            external_reference=f"PRO-{idx}",
            bol_number=f"BOL-{idx}",
            carrier_id="carr-101",
        )
        clm = Claim(
            id=f"claim-{idx}",
            organization_id="org-apex-001",
            shipment_id=s.id,
            claim_type="Cargo Damage",
            status="SUBMITTED",
            claimed_amount=1000.0,
            submitted_at=now - datetime.timedelta(days=20),
        )
        denial_db.add_all([s, clm])

    # Carrier responses: 1 ACCEPTANCE, 1 PARTIAL_SETTLEMENT, 2 DENIALS
    r1 = CarrierResponse(
        id="resp-1",
        claim_id="claim-1",
        document_id="doc-1",
        decision_type="ACCEPTANCE",
        offer_amount=1000.0,
        disputed_amount=0.0,
        created_at=now - datetime.timedelta(days=15),  # TTIR = 5 days
    )
    r2 = CarrierResponse(
        id="resp-2",
        claim_id="claim-2",
        document_id="doc-2",
        decision_type="PARTIAL_SETTLEMENT",
        offer_amount=600.0,
        disputed_amount=400.0,
        created_at=now - datetime.timedelta(days=12),  # TTIR = 8 days
    )
    r3 = CarrierResponse(
        id="resp-3",
        claim_id="claim-3",
        document_id="doc-3",
        decision_type="DENIAL",
        offer_amount=0.0,
        disputed_amount=1000.0,
        denial_reasons_json={"reasons": ["improper_packaging"], "primary_category": "CARMACK_STATUTORY_EXCEPTION"},
        created_at=now - datetime.timedelta(days=10),  # TTIR = 10 days
    )
    r4 = CarrierResponse(
        id="resp-4",
        claim_id="claim-4",
        document_id="doc-4",
        decision_type="DENIAL",
        offer_amount=0.0,
        disputed_amount=1000.0,
        denial_reasons_json={"reasons": ["concealed_damage_late_notice"], "primary_category": "PROCEDURAL_TIMING"},
        created_at=now - datetime.timedelta(days=10),
    )
    denial_db.add_all([r1, r2, r3, r4])
    denial_db.commit()

    service = DenialIntelligenceService()
    profile = service.get_carrier_profile(denial_db, carrier_id="carr-101")

    assert profile.carrier_id == "carr-101"
    assert profile.carrier_name == "ABC Trucking"
    assert profile.total_claims_handled == 4
    assert profile.acceptance_rate_pct == 25.0
    assert profile.partial_settlement_rate_pct == 25.0
    assert profile.denial_rate_pct == 50.0
    assert profile.avg_settlement_ratio == 0.40  # (1000 + 600 + 0 + 0) / 4000
    assert profile.time_to_initial_response_days > 0.0
    assert "CARMACK_STATUTORY_EXCEPTION" in profile.denial_tactic_distribution

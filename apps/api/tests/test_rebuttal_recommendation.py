import os
import sys
import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db.session import Base
from app.models.domain_models import Claim, Shipment, Carrier, Communication, CarrierResponse
from app.schemas.rejection_taxonomy import RejectionCategory, RejectionSubCode
from app.services.rebuttal_service import recommend_and_generate_rebuttal


@pytest.fixture
def rebuttal_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    # Seed carrier, shipment, and claim
    carr = Carrier(id="carr-abc", canonical_name="ABC Trucking", mc_number="MC-123456")
    ship = Shipment(
        id="ship-101",
        organization_id="org-apex-001",
        external_reference="PRO-847293",
        bol_number="BOL-847293",
        carrier_id="carr-abc",
    )
    clm = Claim(
        id="clm-847293",
        organization_id="org-apex-001",
        shipment_id="ship-101",
        claim_type="Cargo Damage",
        status="REJECTED",
        claimed_amount=8000.0,
    )
    session.add_all([carr, ship, clm])
    session.commit()

    yield session
    session.close()


def test_recommend_rebuttal_hughes_released_value_defense(rebuttal_db):
    """Verifies generation of Hughes v. United Van Lines 4-part test rebuttal for released rate caps."""
    carrier_denial_text = """
    We decline full invoice recovery on PRO-847293. Pursuant to Tariff Rule 100, 
    carrier liability is strictly capped at $0.50 per pound ($250.00 total) under released rates.
    """
    res = recommend_and_generate_rebuttal(
        db=rebuttal_db,
        claim_id="clm-847293",
        denial_text=carrier_denial_text,
    )

    assert res["rebuttal_strategy"] == "RELEASED_VALUE_CHALLENGE"
    assert "Hughes v. United Van Lines" in res["governing_citation"]
    assert "829 F.2d 1407" in res["governing_citation"]
    assert "1. Maintain a tariff within STB guidelines" in res["body"]
    assert "2. Obtain shipper's agreement on choice of liability" in res["body"]
    assert "3. Reasonable opportunity to choose between liability tiers" in res["body"]
    assert "4. Pre-transport receipt or Bill of Lading" in res["body"]
    assert res["draft_status"] == "DRAFT"

    # Confirm Communication row created
    comm = rebuttal_db.query(Communication).filter(Communication.id == res["communication_id"]).first()
    assert comm is not None
    assert comm.draft_status == "DRAFT"
    assert "Hughes v. United Van Lines" in comm.body


def test_recommend_rebuttal_elmore_stahl_packaging_defense(rebuttal_db):
    """Verifies generation of Missouri Pacific v. Elmore & Stahl burden-shifting rebuttal for packaging defense."""
    carrier_denial_text = """
    Declined under Carmack Act of Shipper exception. Pallet was improperly shrink-wrapped and lacked packaging integrity.
    """
    res = recommend_and_generate_rebuttal(
        db=rebuttal_db,
        claim_id="clm-847293",
        denial_text=carrier_denial_text,
    )

    assert res["rebuttal_strategy"] == "PACKAGING_PRETEXT_BURDEN_SHIFT"
    assert "Missouri Pacific R. Co. v. Elmore & Stahl" in res["governing_citation"]
    assert "377 U.S. 134" in res["governing_citation"]
    assert "prima facie case" in res["body"].lower()
    assert "clean bill of lading" in res["body"].lower()


def test_recommend_rebuttal_concealed_damage_statutory_window(rebuttal_db):
    """Verifies generation of 49 U.S.C. § 14706(e)(1) statutory 9-month defense for late concealed notice."""
    carrier_denial_text = """
    Claim rejected because concealed damage was reported 10 days after delivery, exceeding our 5-day tariff window.
    """
    res = recommend_and_generate_rebuttal(
        db=rebuttal_db,
        claim_id="clm-847293",
        denial_text=carrier_denial_text,
    )

    assert res["rebuttal_strategy"] == "STATUTORY_FILING_WINDOW_PREEMPTION"
    assert "49 U.S.C. § 14706(e)(1)" in res["governing_citation"]
    assert "9 months" in res["body"] or "nine months" in res["body"].lower()

import pytest
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from app.services.carmack_lawsuit_service import calculate_carmack_lawsuit_deadline
from app.services.rebuttal_service import generate_rebuttal_package
from app.models.domain_models import Claim, Organization, Carrier, Shipment

def test_carmack_2_year_plus_1_day_lawsuit_deadline_standard():
    """
    TDD Test: Verify 2 years + 1 day lawsuit deadline calculation for standard date.
    Jan 15, 2026 -> Jan 16, 2028.
    """
    denial_date = datetime(2026, 1, 15, tzinfo=timezone.utc)
    result = calculate_carmack_lawsuit_deadline(denial_date)
    expected = datetime(2028, 1, 16, tzinfo=timezone.utc)
    assert result["lawsuit_deadline_at"] == expected.isoformat()
    assert result["days_remaining"] > 0

def test_carmack_lawsuit_deadline_leap_year_edge_case():
    """
    TDD Test: Verify 2 years + 1 day deadline calculation across leap year boundary (Feb 29, 2024).
    Feb 29, 2024 + 2 years = Feb 28, 2026 + 1 day = March 1, 2026.
    """
    denial_date = datetime(2024, 2, 29, tzinfo=timezone.utc)
    result = calculate_carmack_lawsuit_deadline(denial_date)
    expected = datetime(2026, 3, 1, tzinfo=timezone.utc)
    assert result["lawsuit_deadline_at"] == expected.isoformat()

def test_carmack_lawsuit_deadline_year_end_boundary():
    """
    TDD Test: Verify year-end boundary (Dec 31, 2025 -> Jan 1, 2028).
    """
    denial_date = datetime(2025, 12, 31, tzinfo=timezone.utc)
    result = calculate_carmack_lawsuit_deadline(denial_date)
    expected = datetime(2028, 1, 1, tzinfo=timezone.utc)
    assert result["lawsuit_deadline_at"] == expected.isoformat()

def test_rebuttal_package_contains_carmack_citations(db_session):
    """
    TDD Test: Verify generated rebuttal package contains Carmack 49 U.S.C. 14706 citations & BOL evidence tags.
    """
    # Clean up test IDs in correct foreign key dependency order
    from app.models.domain_models import Communication
    db_session.query(Communication).filter(Communication.claim_id == "clm-rebut-001").delete()
    db_session.query(Claim).filter(Claim.id == "clm-rebut-001").delete()
    db_session.query(Shipment).filter(Shipment.id == "shp-rebut-001").delete()
    db_session.query(Organization).filter(Organization.id == "org-rebut-001").delete()
    db_session.commit()

    org = Organization(id="org-rebut-001", name="Rebuttal Test Org", type="broker")
    db_session.add(org)
    db_session.commit()

    carrier = db_session.query(Carrier).filter(Carrier.id == "car-001").first()
    if not carrier:
        carrier = Carrier(id="car-001", canonical_name="ABC Trucking", active=True)
        db_session.add(carrier)
        db_session.commit()

    shipment = Shipment(id="shp-rebut-001", organization_id="org-rebut-001", external_reference="PRO-333", bol_number="BOL-333", carrier_id="car-001")
    db_session.add(shipment)
    db_session.commit()

    claim = Claim(id="clm-rebut-001", organization_id="org-rebut-001", shipment_id="shp-rebut-001", claim_type="Cargo Damage", status="REJECTED", claimed_amount=9500.00)
    db_session.add(claim)
    db_session.commit()

    rebuttal = generate_rebuttal_package(db=db_session, claim_id="clm-rebut-001", denial_pretext="improper_packaging")
    assert "49 U.S.C. § 14706" in rebuttal["body"]
    assert "[BOL p.1]" in rebuttal["body"]
    assert rebuttal["draft_status"] == "DRAFT"

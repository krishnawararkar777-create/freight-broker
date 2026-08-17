import pytest
from datetime import datetime, timedelta, timezone
from app.services.sla_service import calculate_sla_deadlines, check_claim_sla_status
from app.services.followup_service import generate_followup_draft, approve_and_dispatch_followup
from app.models.domain_models import Claim, Communication
from fastapi import HTTPException

def test_sla_30_day_acknowledgment_boundaries():
    """
    TDD Test: Verify 30-day acknowledgment SLA boundaries (Day 29 SAFE, Day 31 OVERDUE).
    """
    now = datetime.now(timezone.utc)
    
    # Day 29: Safe
    submitted_29_days_ago = now - timedelta(days=29)
    sla_29 = calculate_sla_deadlines(submitted_29_days_ago)
    assert sla_29["is_acknowledgment_overdue"] is False

    # Day 31: Overdue
    submitted_31_days_ago = now - timedelta(days=31)
    sla_31 = calculate_sla_deadlines(submitted_31_days_ago)
    assert sla_31["is_acknowledgment_overdue"] is True

def test_sla_120_day_resolution_boundaries():
    """
    TDD Test: Verify 120-day resolution SLA boundaries (Day 119 SAFE, Day 121 OVERDUE).
    """
    now = datetime.now(timezone.utc)

    # Day 119: Safe
    submitted_119_days_ago = now - timedelta(days=119)
    sla_119 = calculate_sla_deadlines(submitted_119_days_ago)
    assert sla_119["is_resolution_overdue"] is False

    # Day 121: Overdue
    submitted_121_days_ago = now - timedelta(days=121)
    sla_121 = calculate_sla_deadlines(submitted_121_days_ago)
    assert sla_121["is_resolution_overdue"] is True

def test_followup_draft_server_guard(db_session):
    """
    TDD Test: Attempting to dispatch an unapproved follow-up draft must raise HTTP 403 Forbidden.
    """
    from app.models.domain_models import Organization, Carrier, Shipment

    # Clean up test IDs if existing
    db_session.query(Communication).filter(Communication.id == "comm-test-001").delete()
    db_session.query(Claim).filter(Claim.id == "clm-sla-001").delete()
    db_session.query(Shipment).filter(Shipment.id == "shp-sla-001").delete()
    db_session.query(Organization).filter(Organization.id == "org-sla-001").delete()
    db_session.commit()

    org = Organization(id="org-sla-001", name="SLA Test Org", type="broker")
    db_session.add(org)
    db_session.commit()

    carrier = db_session.query(Carrier).filter(Carrier.id == "car-001").first()
    if not carrier:
        carrier = Carrier(id="car-001", canonical_name="ABC Trucking", active=True)
        db_session.add(carrier)
        db_session.commit()

    shipment = Shipment(id="shp-sla-001", organization_id="org-sla-001", external_reference="PRO-111", bol_number="BOL-111", carrier_id="car-001")
    db_session.add(shipment)
    db_session.commit()

    claim = Claim(id="clm-sla-001", organization_id="org-sla-001", shipment_id="shp-sla-001", claim_type="Cargo Damage", status="SUBMITTED", claimed_amount=5000.0)
    db_session.add(claim)
    db_session.commit()

    comm = Communication(
        id="comm-test-001",
        claim_id="clm-sla-001",
        channel="email",
        direction="outbound",
        sender="sarah@apex.com",
        recipient="claims@abctrucking.com",
        subject="Status Inquiry - 49 CFR 370.9",
        body="Sample follow-up body",
        draft_status="DRAFT"
    )
    db_session.add(comm)
    db_session.commit()

    # Attempt to dispatch without human approval sign-off
    with pytest.raises(HTTPException) as exc_info:
        approve_and_dispatch_followup(db_session, communication_id="comm-test-001", user_id="usr-1", is_approved=False)

    assert exc_info.value.status_code == 403

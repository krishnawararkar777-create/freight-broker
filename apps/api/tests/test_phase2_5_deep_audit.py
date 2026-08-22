import pytest
from app.services.recovery_ledger_service import (
    calculate_contingency_fee,
    record_recovery_event_and_issue_invoice
)
from app.models.domain_models import Claim, Organization, Carrier, Shipment, User, RecoveryEvent, FeeEvent, Invoice, AuditEvent

def setup_test_entities(db):
    """Helper to set up clean test entities for deep audit."""
    db.query(AuditEvent).filter(AuditEvent.organization_id == "org-audit-001").delete()
    db.query(FeeEvent).filter(FeeEvent.claim_id == "clm-audit-001").delete()
    db.query(RecoveryEvent).filter(RecoveryEvent.claim_id == "clm-audit-001").delete()
    db.query(Invoice).filter(Invoice.organization_id == "org-audit-001").delete()
    db.query(Claim).filter(Claim.id == "clm-audit-001").delete()
    db.query(Shipment).filter(Shipment.id == "shp-audit-001").delete()
    db.query(User).filter(User.id == "usr-audit-001").delete()
    db.query(Organization).filter(Organization.id == "org-audit-001").delete()
    db.commit()

    org = Organization(id="org-audit-001", name="Audit Broker", contingency_rate=0.20)
    db.add(org)
    user = User(id="usr-audit-001", organization_id="org-audit-001", name="Audit User", email="audit@test.com")
    db.add(user)
    carrier = db.query(Carrier).filter(Carrier.id == "car-abc").first()
    if not carrier:
        carrier = Carrier(id="car-abc", canonical_name="ABC Trucking")
        db.add(carrier)
    db.commit()

    shipment = Shipment(id="shp-audit-001", organization_id="org-audit-001", external_reference="REF-AUDIT", bol_number="BOL-AUDIT", carrier_id="car-abc")
    db.add(shipment)
    db.commit()

    claim = Claim(id="clm-audit-001", organization_id="org-audit-001", shipment_id="shp-audit-001", claimed_amount=8000.0, status="SUBMITTED")
    db.add(claim)
    db.commit()
    return "clm-audit-001"

def test_phase2_5_step1_and_step2_hand_calculated_20_percent_fee():
    """Verify $6,000 recovery x 20% contingency fee = $1,200 exactly."""
    result = calculate_contingency_fee(6000.00, 0.20)
    assert result["eligible_amount"] == 6000.00
    assert result["contingency_rate"] == 0.20
    assert result["fee_amount"] == 1200.00

def test_phase2_5_step3_fee_events_table_matches_calculation(db_session):
    """Verify record_recovery_event inserts fee_events row matching $1,200 fee."""
    claim_id = setup_test_entities(db_session)
    res = record_recovery_event_and_issue_invoice(
        db_session,
        claim_id=claim_id,
        amount=6000.00,
        user_id="usr-audit-001",
        payment_reference="CHK-99201",
        payer="ABC Trucking"
    )
    fee_event = res["fee_event"]
    assert fee_event.eligible_amount == 6000.00
    assert fee_event.contingency_rate == 0.20
    assert fee_event.fee_amount == 1200.00
    assert fee_event.status == "billed"

def test_phase2_5_step4_zero_dollar_recovery_edge_case(db_session):
    """Verify $0 recovery creates a fee_events row with $0 fee (not skipped, no error)."""
    claim_id = setup_test_entities(db_session)
    res = record_recovery_event_and_issue_invoice(
        db_session,
        claim_id=claim_id,
        amount=0.00,
        user_id="usr-audit-001",
        payment_reference="CHK-ZERO-00",
        payer="ABC Trucking"
    )
    fee_event = res["fee_event"]
    assert fee_event is not None
    assert fee_event.eligible_amount == 0.00
    assert fee_event.fee_amount == 0.00
    assert fee_event.status == "billed"

def test_phase2_5_step6_invoice_generation_math(db_session):
    """Verify auto-generated invoice shows claim fee amount ($1,200) and status issued."""
    claim_id = setup_test_entities(db_session)
    res = record_recovery_event_and_issue_invoice(
        db_session,
        claim_id=claim_id,
        amount=6000.00,
        user_id="usr-audit-001",
        payment_reference="CHK-INV-TEST",
        payer="ABC Trucking"
    )
    invoice = res["invoice"]
    assert invoice is not None
    assert invoice.total == 1200.00
    assert invoice.subtotal == 1200.00
    assert invoice.status == "issued"
    assert invoice.invoice_number.startswith("INV-")

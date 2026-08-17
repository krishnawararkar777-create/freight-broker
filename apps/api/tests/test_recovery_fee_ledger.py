import pytest
from app.services.recovery_ledger_service import calculate_contingency_fee, record_recovery_event_and_issue_invoice
from app.models.domain_models import Claim, Organization, Carrier, Shipment, RecoveryEvent, FeeEvent, Invoice, User

def test_contingency_fee_20_percent_math():
    """
    TDD Test: Verify 20% contingency fee math ($10,000 recovered -> $2,000 fee).
    """
    res = calculate_contingency_fee(eligible_amount=10000.00, rate=0.20)
    assert res["eligible_amount"] == 10000.00
    assert res["contingency_rate"] == 0.20
    assert res["fee_amount"] == 2000.00

def test_contingency_fee_zero_recovery_edge_case():
    """
    TDD Test: Verify $0 recovery results in exactly $0.00 fee invoice ($0 fee on $0 recovered).
    """
    res = calculate_contingency_fee(eligible_amount=0.00, rate=0.20)
    assert res["eligible_amount"] == 0.00
    assert res["fee_amount"] == 0.00

def test_contingency_fee_partial_recovery():
    """
    TDD Test: Verify partial recovery fee ($5,500.50 recovered -> $1,100.10 fee).
    """
    res = calculate_contingency_fee(eligible_amount=5500.50, rate=0.20)
    assert res["eligible_amount"] == 5500.50
    assert res["fee_amount"] == 1100.10

def test_recovery_pipeline_persistence(db_session):
    """
    TDD Test: End-to-end recording of recovery event, fee event creation, and invoice generation.
    """
    # Clean up test IDs in correct foreign key dependency order
    from app.models.domain_models import AuditEvent
    db_session.query(AuditEvent).filter(AuditEvent.organization_id == "org-rec-001").delete()
    db_session.query(FeeEvent).filter(FeeEvent.claim_id == "clm-rec-001").delete()
    db_session.query(RecoveryEvent).filter(RecoveryEvent.claim_id == "clm-rec-001").delete()
    db_session.query(Invoice).filter(Invoice.organization_id == "org-rec-001").delete()
    db_session.query(Claim).filter(Claim.id == "clm-rec-001").delete()
    db_session.query(Shipment).filter(Shipment.id == "shp-rec-001").delete()
    db_session.query(User).filter(User.id == "usr-rec-001").delete()
    db_session.query(Organization).filter(Organization.id == "org-rec-001").delete()
    db_session.commit()

    org = Organization(id="org-rec-001", name="Ledger Test Org", type="broker", contingency_rate=0.20)
    db_session.add(org)
    db_session.commit()

    user = User(id="usr-rec-001", organization_id="org-rec-001", name="Sarah Jenkins", email="sarah@apex.com", role="Claims Manager")
    db_session.add(user)
    db_session.commit()

    carrier = db_session.query(Carrier).filter(Carrier.id == "car-001").first()
    if not carrier:
        carrier = Carrier(id="car-001", canonical_name="ABC Trucking", active=True)
        db_session.add(carrier)
        db_session.commit()

    shipment = Shipment(id="shp-rec-001", organization_id="org-rec-001", external_reference="PRO-444", bol_number="BOL-444", carrier_id="car-001")
    db_session.add(shipment)
    db_session.commit()

    claim = Claim(id="clm-rec-001", organization_id="org-rec-001", shipment_id="shp-rec-001", claim_type="Cargo Damage", status="APPROVED", claimed_amount=10000.00)
    db_session.add(claim)
    db_session.commit()

    rec_result = record_recovery_event_and_issue_invoice(
        db=db_session,
        claim_id="clm-rec-001",
        amount=8000.00,
        payment_reference="CHK-998877",
        payer="ABC Trucking",
        user_id="usr-rec-001"
    )

    assert rec_result["recovery_event"].amount == 8000.00
    assert rec_result["fee_event"].fee_amount == 1600.00  # 20% of $8,000
    assert rec_result["invoice"].total == 1600.00
    assert claim.status == "RECOVERED"

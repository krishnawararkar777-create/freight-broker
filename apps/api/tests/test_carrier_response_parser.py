import pytest
from app.services.carrier_response_service import calculate_settlement_discrepancy, process_carrier_response
from schemas.carrier_response_schema import CarrierResponseExtraction
from app.models.domain_models import Claim, Organization, Carrier, Shipment, Document

def test_settlement_discrepancy_ratio_math():
    """
    TDD Test: Verify settlement offer delta calculation ($8,000 claimed - $5,000 offer = $3,000 disputed).
    """
    res = calculate_settlement_discrepancy(claimed_amount=8000.00, offer_amount=5000.00)
    assert res["offer_amount"] == 5000.00
    assert res["disputed_amount"] == 3000.00
    assert res["recovery_ratio"] == 0.625  # 62.5% recovery offer

def test_settlement_full_denial_delta():
    """
    TDD Test: Verify $0 offer results in 100% disputed amount.
    """
    res = calculate_settlement_discrepancy(claimed_amount=10000.00, offer_amount=0.00)
    assert res["offer_amount"] == 0.00
    assert res["disputed_amount"] == 10000.00
    assert res["recovery_ratio"] == 0.0

def test_process_carrier_response_persistence(db_session):
    """
    TDD Test: End-to-end processing of carrier response letter into CarrierResponse model.
    """
    # Clean up test IDs in correct foreign key dependency order
    from app.models.domain_models import CarrierResponse, AuditEvent
    db_session.query(AuditEvent).filter(AuditEvent.organization_id == "org-resp-001").delete()
    db_session.query(CarrierResponse).filter(CarrierResponse.claim_id == "clm-resp-001").delete()
    db_session.query(Document).filter(Document.id == "doc-resp-001").delete()
    db_session.query(Claim).filter(Claim.id == "clm-resp-001").delete()
    db_session.query(Shipment).filter(Shipment.id == "shp-resp-001").delete()
    db_session.query(Organization).filter(Organization.id == "org-resp-001").delete()
    db_session.commit()

    org = Organization(id="org-resp-001", name="Resp Test Org", type="broker")
    db_session.add(org)
    db_session.commit()

    carrier = db_session.query(Carrier).filter(Carrier.id == "car-001").first()
    if not carrier:
        carrier = Carrier(id="car-001", canonical_name="ABC Trucking", active=True)
        db_session.add(carrier)
        db_session.commit()

    shipment = Shipment(id="shp-resp-001", organization_id="org-resp-001", external_reference="PRO-222", bol_number="BOL-222", carrier_id="car-001")
    db_session.add(shipment)
    db_session.commit()

    claim = Claim(id="clm-resp-001", organization_id="org-resp-001", shipment_id="shp-resp-001", claim_type="Cargo Damage", status="SUBMITTED", claimed_amount=8000.00)
    db_session.add(claim)
    db_session.commit()

    doc = Document(
        id="doc-resp-001",
        organization_id="org-resp-001",
        claim_id="clm-resp-001",
        shipment_id="shp-resp-001",
        document_type="CARRIER_RESPONSE",
        filename="ABC_Settlement_Letter.pdf",
        mime_type="application/pdf",
        object_key="org-resp-001/clm-resp-001/doc-resp-001/ABC_Settlement_Letter.pdf",
        sha256="abc123hash"
    )
    db_session.add(doc)
    db_session.commit()

    resp = process_carrier_response(
        db=db_session,
        claim_id="clm-resp-001",
        document_id="doc-resp-001",
        carrier_claim_reference="ABC-CLAIM-987",
        decision_type="PARTIAL_SETTLEMENT",
        offer_amount=5000.00,
        denial_reasons=["packaging_defect_partial"]
    )

    assert resp.claim_id == "clm-resp-001"
    assert resp.offer_amount == 5000.00
    assert resp.disputed_amount == 3000.00
    assert resp.decision_type == "PARTIAL_SETTLEMENT"

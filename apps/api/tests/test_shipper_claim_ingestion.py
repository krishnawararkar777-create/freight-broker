import pytest
from app.models.domain_models import Organization, Facility, Carrier, Claim, Shipment, CustomerPolicy
from app.schemas.shipper_schemas import ShipperClaimCreate, SkuItemDetail
from services.shipper_ingestion_service import shipper_ingestion_service

def test_manual_shipper_claim_ingestion_deterministic_math(db_session):
    # Setup test org and facility
    db_session.query(Claim).filter(Claim.id == 'clm-shipper-manual-01').delete()
    db_session.query(Shipment).filter(Shipment.organization_id == 'org-shipper-ingest-01').delete()
    db_session.query(Facility).filter(Facility.id == 'fac-test-ingest-01').delete()
    db_session.query(CustomerPolicy).filter(CustomerPolicy.organization_id == 'org-shipper-ingest-01').delete()
    from app.models.domain_models import AuditEvent
    db_session.query(AuditEvent).filter(AuditEvent.organization_id == 'org-shipper-ingest-01').delete()
    db_session.query(Organization).filter(Organization.id == 'org-shipper-ingest-01').delete()
    db_session.commit()

    org = Organization(id='org-shipper-ingest-01', name='Apex Industrial Shippers', type='shipper')
    db_session.add(org)
    db_session.commit()

    policy = CustomerPolicy(id='pol-ingest-01', organization_id='org-shipper-ingest-01', valuation_basis='STANDARD_COST')
    facility = Facility(id='fac-test-ingest-01', organization_id='org-shipper-ingest-01', facility_code='PLANT-IN-01', name='Indianapolis Distribution Center')
    carrier = db_session.query(Carrier).filter(Carrier.id == 'car-001').first()
    if not carrier:
        carrier = Carrier(id='car-001', canonical_name='ABC Trucking', active=True)
        db_session.add(carrier)
    db_session.add_all([policy, facility])
    db_session.commit()

    # Define SKU items with deterministic math:
    # Item 1: 5 units @ .00 = ,000.00
    # Item 2: 2 units @ ,250.00 = ,500.00
    # Total Claim Amount = ,500.00
    sku_items = [
        SkuItemDetail(sku='SKU-VALVE-01', description='Industrial Hydraulic Valve', damaged_qty=5, unit_cost=800.00),
        SkuItemDetail(sku='SKU-PUMP-02', description='High Pressure Fuel Pump', damaged_qty=2, unit_cost=1250.00)
    ]

    claim_req = ShipperClaimCreate(
        organization_id='org-shipper-ingest-01',
        facility_id='fac-test-ingest-01',
        po_number='PO-984729',
        carrier_id='car-001',
        external_reference='PRO-SHP-8819',
        bol_number='BOL-SHP-8819',
        claim_type='Cargo Damage',
        sku_details=sku_items,
        notes='Crushed during pallet unloading at dock 4'
    )

    # Ingest Claim
    claim = shipper_ingestion_service.create_manual_shipper_claim(
        db=db_session,
        req=claim_req,
        claim_id='clm-shipper-manual-01'
    )

    assert claim.id == 'clm-shipper-manual-01'
    assert claim.organization_id == 'org-shipper-ingest-01'
    assert claim.facility_id == 'fac-test-ingest-01'
    assert claim.po_number == 'PO-984729'
    assert claim.claimed_amount == 6500.00
    assert claim.status == 'DRAFT'
    assert claim.is_approved_by_human is False
    assert claim.internal_approval_stage == 'WAREHOUSE_INSPECTION'
    assert len(claim.sku_details) == 2
    assert claim.sku_details[0]['total_loss'] == 4000.00
    assert claim.sku_details[1]['total_loss'] == 2500.00

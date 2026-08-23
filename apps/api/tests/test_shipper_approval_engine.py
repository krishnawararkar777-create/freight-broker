import pytest
from app.models.domain_models import Organization, Facility, Carrier, Claim, Shipment, User, AuditEvent
from app.schemas.shipper_schemas import ShipperClaimCreate, SkuItemDetail
from services.shipper_ingestion_service import shipper_ingestion_service
from services.shipper_approval_service import shipper_approval_service
from services.submission_service import submission_service, SubmissionBlockedException

@pytest.fixture
def setup_shipper_claim(db_session):
    # Cleanup in correct FK order
    db_session.query(Claim).filter(Claim.id == 'clm-test-approval-01').delete()
    db_session.query(Shipment).filter(Shipment.organization_id == 'org-shipper-appr-01').delete()
    db_session.query(AuditEvent).filter(AuditEvent.organization_id == 'org-shipper-appr-01').delete()
    db_session.query(User).filter(User.organization_id == 'org-shipper-appr-01').delete()
    db_session.query(Facility).filter(Facility.id == 'fac-appr-01').delete()
    db_session.query(Organization).filter(Organization.id == 'org-shipper-appr-01').delete()
    db_session.commit()

    org = Organization(id='org-shipper-appr-01', name='Apex Industrial Corp', type='shipper')
    db_session.add(org)
    db_session.commit()

    fac = Facility(id='fac-appr-01', organization_id='org-shipper-appr-01', facility_code='PLANT-01', name='Columbus Plant')
    carrier = db_session.query(Carrier).filter(Carrier.id == 'car-001').first()
    if not carrier:
        carrier = Carrier(id='car-001', canonical_name='ABC Trucking', active=True)
        db_session.add(carrier)

    inspector = User(id='usr-insp-10', organization_id='org-shipper-appr-01', name='Inspector Bob', email='bob@shipper.com', role='Plant Manager / Inspector')
    coordinator = User(id='usr-coord-20', organization_id='org-shipper-appr-01', name='Coordinator Carol', email='carol@shipper.com', role='Logistics Coordinator')
    director = User(id='usr-dir-30', organization_id='org-shipper-appr-01', name='Director Dave', email='dave@shipper.com', role='Logistics Director')

    db_session.add_all([fac, inspector, coordinator, director])
    db_session.commit()

    # Create ,500 claim (elevated threshold)
    sku_items = [
        SkuItemDetail(sku='SKU-A', description='Engine Component', damaged_qty=10, unit_cost=650.00)
    ]
    claim_req = ShipperClaimCreate(
        organization_id='org-shipper-appr-01',
        facility_id='fac-appr-01',
        po_number='PO-7788',
        carrier_id='car-001',
        external_reference='PRO-7788',
        bol_number='BOL-7788',
        sku_details=sku_items
    )
    claim = shipper_ingestion_service.create_manual_shipper_claim(
        db=db_session,
        req=claim_req,
        claim_id='clm-test-approval-01'
    )
    return claim

def test_full_sequential_approval_workflow_and_submission(db_session, setup_shipper_claim):
    claim_id = 'clm-test-approval-01'

    # Stage 1: Sign Warehouse Inspection
    claim = shipper_approval_service.sign_warehouse_inspection(
        db=db_session,
        claim_id=claim_id,
        user_id='usr-insp-10',
        user_role='Plant Manager / Inspector',
        notes='Inspected damaged pallets at dock 2. Bins crushed.'
    )
    assert claim.internal_approval_stage == 'LOGISTICS_VERIFICATION'
    assert claim.inspection_signed_by == 'usr-insp-10'
    assert claim.inspection_signed_at is not None

    # Verify premature submission is blocked
    with pytest.raises(SubmissionBlockedException):
        submission_service.submit_claim(db=db_session, claim_id=claim_id)

    # Stage 2: Sign Logistics Verification
    claim = shipper_approval_service.sign_logistics_verification(
        db=db_session,
        claim_id=claim_id,
        user_id='usr-coord-20',
        user_role='Logistics Coordinator',
        notes='BOL and POD matched. Freight charges verified.'
    )
    assert claim.internal_approval_stage == 'DIRECTOR_APPROVAL'
    assert claim.logistics_signed_by == 'usr-coord-20'

    # Stage 3: Sign Director Approval (,500 >= ,000 requires Director)
    claim = shipper_approval_service.sign_director_approval(
        db=db_session,
        claim_id=claim_id,
        user_id='usr-dir-30',
        user_role='Logistics Director',
        notes='Authorized for carrier formal claim filing.'
    )
    assert claim.internal_approval_stage == 'READY_FOR_SUBMISSION'
    assert claim.director_signed_by == 'usr-dir-30'
    assert claim.is_approved_by_human is True
    assert claim.status == 'APPROVED'

    # Stage 4: External Carrier Submission
    submitted_claim = submission_service.submit_claim(db=db_session, claim_id=claim_id)
    assert submitted_claim.status == 'SUBMITTED'
    assert submitted_claim.submitted_at is not None

def test_out_of_order_approval_rejected(db_session, setup_shipper_claim):
    claim_id = 'clm-test-approval-01'

    # Cannot jump directly to Logistics Verification while in WAREHOUSE_INSPECTION
    with pytest.raises(ValueError) as exc:
        shipper_approval_service.sign_logistics_verification(
            db=db_session,
            claim_id=claim_id,
            user_id='usr-coord-20',
            user_role='Logistics Coordinator'
        )
    assert 'Warehouse Inspection must be completed' in str(exc.value)

def test_unauthorized_role_rejected(db_session, setup_shipper_claim):
    claim_id = 'clm-test-approval-01'

    # Advance to Logistics Verification stage
    shipper_approval_service.sign_warehouse_inspection(
        db=db_session,
        claim_id=claim_id,
        user_id='usr-insp-10',
        user_role='Plant Manager / Inspector'
    )

    # Inspector cannot sign Logistics Verification
    with pytest.raises(PermissionError):
        shipper_approval_service.sign_logistics_verification(
            db=db_session,
            claim_id=claim_id,
            user_id='usr-insp-10',
            user_role='Plant Manager / Inspector'
        )
